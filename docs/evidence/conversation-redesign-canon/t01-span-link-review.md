# T01 span provenance review

The first T01 implementation compared the proposal content with the text at `candidate_continuity_changes[*].supporting_span`, but did not prove that the final span came from the candidate's own expressive source segment. A final reply that repeated the same sentence could therefore point the canon reference at the second occurrence while the fresh segment map identified the first.

The regression test `test_rejects_final_ref_not_linked_to_fresh_source_segment_mapping` uses exactly that shape. It passes only when the policy resolves the source candidate span in `CandidateReply`, resolves the complete source segment through `AssembledReply.segment_spans`, translates the candidate offsets through that mapping, and requires equality with the final candidate span. The claim text's second occurrence is rejected.

The frozen contracts are unchanged. `CandidateReply` already checks that candidate spans resolve against expressive segment text; the policy now independently links those spans through the fresh assembled mapping before admitting canon.
