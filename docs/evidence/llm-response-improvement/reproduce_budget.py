"""Reproduce D02's structured JSON versus dialogue output-budget ambiguity."""
import json
from pathlib import Path

from app.services.conversation import contracts as c
from app.services.llm.structured import GenerationMalformed, StructuredGenerationAdapter

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / 'backend/tests/fixtures/conversation/t05-valid.json'


class Response:
    status_code = 200

    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass

    def json(self):
        return {'choices': [{'message': {'content': self.content}}]}


class FakeTransport:
    def __init__(self, response):
        self.response = response
        self.payload = None

    def post(self, url, *, json, headers, timeout):
        self.payload = json
        return self.response


def main():
    fixture = json.loads(FIXTURE.read_text())
    content = json.dumps(fixture['proposal'], ensure_ascii=False, separators=(',', ':'))
    settings = type('Settings', (), {
        'llm_base_url': 'http://127.0.0.1:11434/v1', 'llm_api_key': '',
        'llm_model': 'local-fake', 'llm_timeout_seconds': 3,
        'llm_structured_output': True,
    })()
    context = c.ContextPacket.model_validate(fixture['context'])
    transport = FakeTransport(Response(content))
    adapter = StructuredGenerationAdapter(settings, transport=transport)
    try:
        adapter.generate('proposal', context,
            c.Deadline.after(3, clock=lambda: 100.0), 600)
        result = 'accepted'
    except GenerationMalformed:
        result = 'GenerationMalformed'
    print(json.dumps({
        'reply_characters': sum(len(segment.get('text', '')) for segment in fixture['proposal']['reply']),
        'serialized_json_characters': len(content),
        'provider_max_tokens': transport.payload['max_tokens'],
        'adapter_result': result,
        'fake_transport_calls': 1,
    }, sort_keys=True))


if __name__ == '__main__':
    main()
