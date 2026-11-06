"""Run real Godot UI/HTTP against a runner-owned SQLite world; no model mocks.

Requires a Godot 4 executable. Evidence targets must not already exist.
The production .env is read for provider settings; DATABASE_URL is overridden
before backend import/startup. Neither the normal database nor port 8000 is used.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]


def stop(process):
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def wait_ready(process, port):
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError('Backend exited; inspect backend.log')
        try:
            with urlopen(f'http://127.0.0.1:{port}/health', timeout=.5) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(.1)
    raise RuntimeError('Disposable backend startup timed out')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--behavior-fixtures', action='store_true', help='Controlled distrustful Craftsman/helpful Gatherer states in disposable DB')
    parser.add_argument('--rendered', action='store_true')
    parser.add_argument('--provider-failure', action='store_true')
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output.exists():
        parser.error('Evidence already exists; choose a new output directory.')
    output.mkdir(parents=True)
    godot = str(Path(args.godot).resolve())
    summary = {'started_at': datetime.now(timezone.utc).isoformat(),
               'mode': 'provider_connection_failure' if args.provider_failure else 'configured_live_provider',
               'rendered': args.rendered, 'passed': False}
    paths = [*ROOT.glob('frontend/godot/scripts/*.gd'),
             ROOT / 'frontend/godot/tests/grounded_chat_smoke.gd',
             Path(__file__), *ROOT.glob('backend/app/**/*.py'),
             ROOT / 'backend/app/services/context/village.json',
             ROOT / 'backend/app/services/rule_engine/behavior_policy.json']
    summary['implementation_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    backend = None
    try:
        with tempfile.TemporaryDirectory(prefix='npc-godot-verification-') as temp:
            work = Path(temp)
            project = work / 'godot'
            shutil.copytree(ROOT / 'frontend/godot', project,
                            ignore=shutil.ignore_patterns('.godot', '*.import'))
            shutil.copy(ROOT / 'backend/tests/grounding_scenarios.json', project / 'tests')
            env = os.environ.copy()
            env['PYTHONPATH'] = str(ROOT / 'backend')
            env['DATABASE_URL'] = f'sqlite:///{work / "world.db"}'
            if args.provider_failure:
                env['LLM_BASE_URL'] = 'http://127.0.0.1:1/v1'
                env['LLM_TIMEOUT_SECONDS'] = '1'
            config_code = ('import json; from app.config.settings import get_settings; s=get_settings(); '
                           'print(json.dumps(dict(model=s.llm_model, temperature=.2, '
                           'structured_output=s.llm_structured_output, embedding_model=s.embedding_model)))')
            summary['provider_configuration'] = json.loads(subprocess.check_output(
                [sys.executable, '-c', config_code], cwd=ROOT, env=env, text=True))
            # Reserve the listening socket ourselves: cannot accidentally use an
            # unrelated backend, even if another verification runs concurrently.
            with socket.socket() as listener, (output / 'backend.log').open('w') as log:
                listener.bind(('127.0.0.1', 0))
                listener.listen(128)
                port = listener.getsockname()[1]
                summary['isolation'] = {'database': env['DATABASE_URL'], 'endpoint': f'http://127.0.0.1:{port}', 'temporary_project': str(project)}
                backend = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--fd', str(listener.fileno())],
                                           cwd=ROOT, env=env, pass_fds=(listener.fileno(),), stdout=log, stderr=subprocess.STDOUT)
                wait_ready(backend, port)
                if args.behavior_fixtures:
                    import sqlite3
                    with sqlite3.connect(work / 'world.db') as fixture_db:
                        fixture_db.execute('UPDATE npcs SET trust=.05, fear=.8, aggression=.05, curiosity=.3 WHERE id=1')
                        fixture_db.execute('UPDATE npcs SET trust=.95, fear=.05, aggression=.05, curiosity=.3 WHERE id=2')
                    summary['behavior_fixtures'] = {'1': 'distrustful', '2': 'helpful', 'authored_recovery': False}
                # Import assets in the temporary project, keeping the checkout clean.
                with (output / 'import.log').open('w') as import_log:
                    subprocess.run([godot, '--headless', '--path', str(project), '--editor', '--import'],
                                   stdout=import_log, stderr=subprocess.STDOUT, timeout=90, check=True)
                command = [godot, '--path', str(project)]
                if not args.rendered:
                    command.append('--headless')
                command += ['--script', 'res://tests/grounded_chat_smoke.gd', '--',
                            f'--verification-url=http://127.0.0.1:{port}', f'--evidence-dir={output}',
                            '--failure-mode' if args.provider_failure else '--live-mode']
                if args.behavior_fixtures:
                    command.append('--behavior-mode')
                with (output / 'godot.log').open('w') as godot_log:
                    result = subprocess.run(command, stdout=godot_log, stderr=subprocess.STDOUT, timeout=600)
                summary['godot_exit_code'] = result.returncode
                report = json.loads((output / 'godot.json').read_text())
                summary['checks_passed'] = sum(c['passed'] for c in report['checks'])
                summary['checks_total'] = len(report['checks'])
                summary['passed'] = result.returncode == 0 and summary['checks_passed'] == summary['checks_total']
                # Capture actual raw proposals from this isolated DB after Godot
                # exits, without importing production session globals here.
                import sqlite3
                with sqlite3.connect(work / 'world.db') as db:
                    rows = db.execute('SELECT npc_id, player_input, llm_output, validated_output, final_dialogue FROM conversations ORDER BY id').fetchall()
                    cursor = db.execute('SELECT id, npc_id, event, event_type, game_scope, source_event_id, source_conversation_id, epistemic_status, authority, lifecycle, correction_of_id, superseded_by_id FROM memories ORDER BY id')
                    columns = [column[0] for column in cursor.description]
                    memory_rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    current_scope = db.execute('SELECT game_scope FROM players WHERE id=1').fetchone()[0]
                    sources = {row[0]: row[1:] for row in db.execute('SELECT id, npc_id, game_scope, source_event_id FROM conversations')}
                    valid_sources = all(m['game_scope'] == current_scope and
                                        sources.get(m['source_conversation_id']) == (m['npc_id'], m['game_scope'], m['source_event_id']) for m in memory_rows)
                    summary['memory_provenance'] = {'records': len(memory_rows), 'all_sources_valid': valid_sources}
                    summary['passed'] = summary['passed'] and valid_sources
                # Shareable decision evidence is separate from the original raw audit.
                traces = [json.loads(row[3]).get('decision_trace') for row in rows
                          if json.loads(row[3]).get('decision_trace')]
                trace_sources = {value[2]: (identity, value[0], value[1]) for identity, value in sources.items()}
                traces_valid = bool(traces) and all(
                    trace_sources.get(trace['decision_id']) == (
                        trace['outcome']['conversation_id'], trace['recipient_id'], trace['game_scope'])
                    and trace['outcome']['event_id'] == trace['decision_id'] for trace in traces)
                summary['decision_traces'] = {'records': len(traces), 'all_source_links_valid': traces_valid}
                summary['passed'] = summary['passed'] and traces_valid
                (output / 'decision-traces.json').write_text(json.dumps(traces, indent=2) + '\n')
                (output / 'memories.json').write_text(json.dumps(memory_rows, indent=2) + '\n')
                (output / 'conversations.json').write_text(json.dumps([
                    dict(npc_id=r[0], player_input=r[1], proposal=json.loads(r[2]), validated=json.loads(r[3]), answer=r[4]) for r in rows], indent=2) + '\n')
                if not args.provider_failure:
                    # Genuine backend + Godot process restart against the same
                    # disposable DB, followed by an explicit disposable reset.
                    stop(backend)
                    backend = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--fd', str(listener.fileno())],
                                               cwd=ROOT, env=env, pass_fds=(listener.fileno(),), stdout=log, stderr=subprocess.STDOUT)
                    wait_ready(backend, port)
                    resume_command = [('--resume-mode' if arg == '--live-mode' else arg) for arg in command]
                    with (output / 'resume.log').open('w') as resume_log:
                        resume = subprocess.run(resume_command, stdout=resume_log, stderr=subprocess.STDOUT, timeout=120)
                    resume_report = json.loads((output / 'resume.json').read_text())
                    summary['checks_passed'] += sum(c['passed'] for c in resume_report['checks'])
                    summary['checks_total'] += len(resume_report['checks'])
                    summary['passed'] = summary['passed'] and resume.returncode == 0 and all(c['passed'] for c in resume_report['checks'])
                stop(backend)
                backend = None
    except Exception as exc:
        summary['error'] = str(exc)
    finally:
        if backend is not None:
            stop(backend)
        summary['finished_at'] = datetime.now(timezone.utc).isoformat()
        summary['snapshots'] = [path.name for path in sorted(output.glob('*.png'))]
        if args.rendered and not summary['snapshots']:
            summary['passed'] = False
            summary['rendering_error'] = 'Rendered run produced no screenshots'
        (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'implementation_sha256'}, indent=2))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
