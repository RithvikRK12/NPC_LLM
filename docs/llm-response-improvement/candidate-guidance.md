# Candidate response guidance under test

Status: evaluated as the existing `improved_guidance` dialogue-shadow variant; not adopted in the configured application.

## Candidate direction

Answer the latest message first, including its distinct practical and emotional concerns. Use prior dialogue only to resolve references or answer an explicit recall request; treat prior NPC speech as attributed history, not proof of current world facts. Use current supplied facts and capabilities for claims or offers. When evidence is missing, say you do not know or ask one concise question. Do not invent current conditions, events, mechanics, promises, or biography. Preserve authored voice and identity; keep uncertainty attributed. Finish the main answer in a complete, concise sentence within the existing dialogue limit, removing optional anecdotes and recaps before the answer.

## Evidence and limits

The run snapshots for `improved_guidance` contain the more detailed form of this direction. Two matched full Llama runs completed 176/176 with no missing outputs. In non-scored spot checks, the Gatherer correctly recalled “quiet attentive company” for `gatherer-04:t2` in both runs, while baseline t04 repeated the fruit-stash answer. The successful later fruit recall control `gatherer-04:t3` also remained correct in both runs. Craftsman's unknown rope advice at `craftsman-02:t3` explicitly recommended waiting, though both outputs were cutoff-suspected. Unsupported present-world assertions still occurred: repeat 2 invented a rain forecast at `craftsman-01:t3` and a recent wild-animal incident at `gatherer-01:t3`. Cutoff suspicion was 82/176 and 83/176; request p50/p95 was 3.807/5.043s and 4.484/6.565s.

The user waived human review. These examples are direct artifact inspection by the implementation agent, not reviewer scores, independent semantic review, or a pass rate. They show one concrete recall improvement alongside unresolved grounding/cutoff problems. Keep the candidate unadopted and retain the current deployed prompt.
