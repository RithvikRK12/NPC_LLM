"""Pure, bounded admission of generated narrative canon from final speech.

Semantic support and affordance classification are injected decisions. This
module checks their inputs and applies authored/head precedence; it does not
pretend that string rules establish truth or authorize game entities.
"""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol

from .contracts import (
    AddCanonChange,
    AssembledReply,
    CanonCandidate,
    CanonChange,
    CanonRecord,
    CandidateReply,
    CorrectionCandidate,
    ExpressiveSegment,
    ReviseCanonChange,
    SourceRef,
    TextSpan,
)


class CanonRules(Protocol):
    """Trusted validators supplied by the owning validation boundary.

    `validated_claim` must be based on the exact accepted final reply and
    validated candidate evidence. It is a semantic policy hook, not a
    mechanical authority check.
    """

    def validated_claim(
        self, candidate: CanonCandidate, final_text: str, span_text: str,
        evidence: tuple[SourceRef, ...],
    ) -> bool: ...

    def needs_affordance_grounding(self, candidate: CanonCandidate, span_text: str) -> bool: ...

    def affordance_is_grounded(
        self, candidate: CanonCandidate, span_text: str, evidence: tuple[SourceRef, ...],
    ) -> bool: ...

    def category_for(self, candidate: CanonCandidate) -> str: ...

    def validated_correction(
        self, candidate: CanonCandidate, correction: CorrectionCandidate,
        head: CanonRecord, final_text: str, span_text: str,
        correction_texts: tuple[str, ...], evidence: tuple[SourceRef, ...],
    ) -> bool:
        """Confirm explicit NPC acceptance in this exact final support span.

        The attributed challenge alone is insufficient. The owning validator
        checks semantic linkage to the head and replacement, using the exact
        accepted message slices and final speech. Missing/failing checkers
        reject revisions, including for legacy T01 rules implementations.
        """
        ...


@dataclass(frozen=True, slots=True)
class CanonReply:
    """Final reply plus detached correction evidence from the accepted input.

    Correction targets are resolved canon IDs; correction_texts is keyed by
    the exact player-message source IDs carried in evidence_dependencies.
    Callers supply scoped accepted texts, never provider-rewritten messages.
    Defaults keep addition-only callers compatible and revisions closed.
    """

    candidate_reply: CandidateReply
    assembled: AssembledReply
    corrections: tuple[CorrectionCandidate, ...] = ()
    correction_texts: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'corrections', tuple(self.corrections))
        object.__setattr__(self, 'correction_texts', MappingProxyType(dict(self.correction_texts)))


class CanonPolicy:
    """Plan supported additions and explicitly accepted narrative corrections.

    `active_canon` and `authored_constraints` are scoped detached current
    heads supplied by the caller. Revision plans retain the canon ID and
    expected head revision; persistence must CAS it and preserve old records.
    """

    def __init__(self, rules: CanonRules):
        self._rules = rules

    def plan(
        self,
        reply: CanonReply,
        active_canon: Sequence[CanonRecord],
        authored_constraints: Sequence[CanonRecord],
    ) -> tuple[CanonChange, ...]:
        if (not isinstance(reply, CanonReply) or
                not isinstance(reply.candidate_reply, CandidateReply) or
                not isinstance(reply.assembled, AssembledReply)):
            return ()
        assembled = reply.assembled
        candidates = reply.candidate_reply.canon_candidates

        # The accepted assembly carries a fresh candidate-to-final-speech map.
        # Candidate segment offsets alone are never publication authority.
        final_by_candidate = {ref.candidate_id: ref.supporting_span for ref in assembled.candidate_continuity_changes}
        candidates_by_id = {candidate.candidate_id: candidate for candidate in candidates}
        if len(candidates_by_id) != len(candidates):
            return ()
        segments_by_id = {segment.segment_id: segment for segment in reply.candidate_reply.segments
                          if isinstance(segment, ExpressiveSegment)}

        output: list[CanonChange] = []
        emitted_keys: set[tuple[str, str]] = set()
        for candidate_id, final_span in final_by_candidate.items():
            candidate = candidates_by_id.get(candidate_id)
            if candidate is None or candidate.kind not in {'add', 'revise'}:
                continue
            try:
                source_segment = segments_by_id.get(candidate.supporting_span.text_id)
                if source_segment is None:
                    continue
                exact_source_text = candidate.supporting_span.resolve(
                    {source_segment.segment_id: source_segment.text},
                )
                mapped_segment_span = assembled.segment_spans.get(source_segment.segment_id)
                if mapped_segment_span is None or mapped_segment_span.text_id != assembled.text_id:
                    continue
                # The fresh assembly map must reproduce the whole source
                # segment, then the candidate's source offsets are translated
                # through that map to the only final span allowed to support it.
                mapped_segment_span.resolve(
                    {assembled.text_id: assembled.final_text}, expected_text=source_segment.text,
                )
                expected_final_span = TextSpan(
                    text_id=assembled.text_id,
                    start=mapped_segment_span.start + candidate.supporting_span.start,
                    end=mapped_segment_span.start + candidate.supporting_span.end,
                )
                if final_span != expected_final_span:
                    continue
                exact_final_text = final_span.resolve(
                    {assembled.text_id: assembled.final_text}, expected_text=exact_source_text,
                )
            except (KeyError, ValueError, TypeError):
                continue

            # Ensure the proposed content itself is actually represented by
            # its claimed final span. Semantic paraphrase decisions belong to
            # the injected validator; this exact form is the safe default.
            if candidate.content not in exact_source_text:
                continue
            try:
                supported = self._rules.validated_claim(
                    candidate, assembled.final_text, exact_final_text, assembled.evidence_dependencies,
                )
                requires_grounding = self._rules.needs_affordance_grounding(candidate, exact_final_text)
                grounded = (not requires_grounding or self._rules.affordance_is_grounded(
                    candidate, exact_final_text, assembled.evidence_dependencies,
                ))
                category = self._rules.category_for(candidate)
            except Exception:
                # A checker failure cannot turn a proposal into durable canon.
                continue
            if not supported or not grounded:
                continue

            key = (candidate.subject, candidate.predicate)
            if key in emitted_keys:
                continue
            # Any authored value for this identity slot wins, including an
            # identical one. Authored content changes use content/game APIs.
            if any(record.origin == 'authored' and record.status == 'active' and
                   (record.subject, record.predicate) == key
                   for record in (*active_canon, *authored_constraints)):
                continue
            if candidate.kind == 'revise':
                if supported is not True or grounded is not True:
                    continue
                revision = self._revision(
                    candidate, reply, active_canon, final_span, exact_final_text,
                )
                if revision is not None:
                    output.append(revision)
                    emitted_keys.add(key)
                continue
            # Ordinary generation never overwrites an existing generated head.
            if any(record.status == 'active' and
                   (record.subject, record.predicate) == key
                   for record in active_canon):
                continue

            output.append(AddCanonChange(
                kind='add', canon_id=candidate.candidate_id, expected_revision=0,
                subject=candidate.subject, predicate=candidate.predicate,
                content=candidate.content, category=category, origin='generated',
                authority='narrative_only', supporting_span=final_span,
            ))
            emitted_keys.add(key)
        return tuple(output)

    def _revision(
        self, candidate: CanonCandidate, reply: CanonReply,
        active_canon: Sequence[CanonRecord], final_span: TextSpan,
        exact_final_text: str,
    ) -> ReviseCanonChange | None:
        heads = tuple(record for record in active_canon if record.status == 'active' and
                      (record.subject, record.predicate) == (candidate.subject, candidate.predicate))
        if len(heads) != 1:
            return None
        head, = heads
        if (head.origin != 'generated' or head.authority != 'narrative_only' or
                candidate.expected_revision != head.revision):
            return None
        corrections = tuple(correction for correction in reply.corrections
                            if correction.correction_id == candidate.correction_candidate_id)
        if len(corrections) != 1:
            return None
        correction, = corrections
        if correction.target_reference_id != head.canon_id:
            return None

        evidence = reply.assembled.evidence_dependencies
        # Message slices are checked structurally here; acceptance and
        # correction meaning remain the injected validator's responsibility.
        for span in correction.source_spans:
            if not any(source.kind == 'player_message' and source.source_id == span.text_id and
                       source.attribution == correction.attribution and
                       source.game_scope == head.game_scope and source.npc_id in (None, head.npc_id)
                       for source in evidence):
                return None
        try:
            correction_texts = tuple(span.resolve(reply.correction_texts)
                                     for span in correction.source_spans)
            accepted = self._rules.validated_correction(
                candidate, correction, head, reply.assembled.final_text,
                exact_final_text, correction_texts, evidence,
            )
        except Exception:
            return None
        if accepted is not True:
            return None
        return ReviseCanonChange(
            kind='revise', canon_id=head.canon_id, expected_revision=head.revision,
            subject=head.subject, predicate=head.predicate, content=candidate.content,
            category=head.category, origin='generated', authority='narrative_only',
            supporting_span=final_span, correction_link=correction.correction_id,
        )
