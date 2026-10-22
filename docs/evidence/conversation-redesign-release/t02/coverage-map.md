# Adoption coverage map

The full backend discovery command runs these tests; PostgreSQL adapter runners repeat the SQL invariants in newly created `npc_test_*` databases. Fault injection and concurrent writers simulate the named crash/race boundaries; these are not claims that a production process was killed at every instruction.

## Detailed design §5.4

| Failure point | Behavioral test IDs |
| --- | --- |
| Before admission commits | `test_failed_admission_rolls_back_sequence_allocation`; `test_lost_admission_commit_ack_recovers_same_identity` (`test_conversation_persistence.py`) |
| After admission, before generation | `test_restart_scan_claims_durable_oldest_turn` (`test_conversation_worker.py`); `test_restart_scan_lists_only_active_streams_with_pending_turns` (`test_conversation_persistence.py`) |
| Provider dispatched, no saved output | `test_uncertain_dispatched_proposal_falls_back_without_redispatch`; `test_lost_action_composition_output_uses_receipt_grounded_fallback` (`test_conversation_coordinator.py`) |
| Operation transaction uncertainty | `test_receipt_insert_failure_rolls_back_inventory_quest_and_phase`; `test_lost_commit_ack_recovers_receipt_before_any_new_execution` (`test_conversation_persistence.py`) |
| Action committed, no speech | `test_recovered_receipt_is_composed_without_operation_dispatch` (`test_conversation_coordinator.py`); `test_startup_recovery_finalizes_a_committed_receipt_without_reexecuting_it` (`test_conversation_application.py`) |
| Finalized before HTTP delivery | `test_durable_final_submit_and_lookup_preserve_legacy_and_revisions` (`test_conversation_api.py`); `test_recovered_final_result_is_returned_without_reprocessing` (`test_conversation_coordinator.py`) |
| Clear during generation | `test_clear_racing_finalization_leaves_no_old_epoch_payload` (`test_conversation_persistence_lifecycle.py`); `test_scope_epoch_and_npc_are_checked_without_allocating` (`test_conversation_persistence.py`) |
| Clear after action commit | `test_clear_erases_old_payload_but_preserves_receipt_and_canon_origin` (`test_conversation_persistence_lifecycle.py`); `test_receipt_recovery_survives_clear_but_never_crosses_new_game_scope` (`test_conversation_persistence.py`) |
| Reset races an action | `test_new_game_rotates_scope_and_rejects_late_old_scope_writes` (`test_conversation_persistence_lifecycle.py`); `test_receipt_recovery_survives_clear_but_never_crosses_new_game_scope` |
| Lease replaced, old worker returns | `test_expired_claim_retains_oldest_phase_and_rejects_old_worker`; `test_replaced_and_expired_fences_cannot_execute` (`test_conversation_persistence.py`) |
| Shared item consumed by another NPC | `test_cross_npc_shared_item_race_rejects_loser_without_substitution`; `test_changed_ownership_records_rejection_and_never_substitutes` (`test_conversation_persistence.py`) |

## Detailed design §8

| Condition | Behavioral test IDs |
| --- | --- |
| Invalid input/schema/bounds | `test_invalid_versioned_input_rejected_before_admission` (`test_conversation_api.py`); generation adapter bound/Unicode tests |
| Missing NPC/save, stale key, payload conflict | `test_unknown_npc_save_stale_key_and_payload_conflict` (`test_conversation_api.py`) |
| Already pending | `test_pending_identity_replays_without_draft_and_status_only_reads` (`test_conversation_api.py`) |
| Provider timeout/unavailable/malformed | `test_provider_timeout_maps_to_distinct_timeout`; `test_provider_outage_never_substitutes_mock`; `test_malformed_json_maps_to_distinct_malformed_output` (`test_conversation_generation_adapter.py`); coordinator fallback tests |
| Unsupported/ambiguous actions | OperationPolicy/InteractionPolicy suites; `test_invented_model_action_for_personal_question_cannot_move_stock`; `test_quoted_and_hypothetical_requests_never_move_stock` (`test_conversation_playtest.py`) |
| Changed action resource | `test_changed_ownership_records_rejection_and_never_substitutes` (`test_conversation_persistence.py`) |
| Changed evidence/canon before publication | `test_publication_rechecks_exact_resource_evidence_even_without_plan_revision`; `test_publication_rejects_stale_narrative_canon_revision` (`test_conversation_persistence_lifecycle.py`) |
| DB failure/commit uncertain | Lost-ack/rollback tests in `test_conversation_persistence.py`; `test_typed_errors_keep_stable_recovery_status_and_safe_fields` (`test_conversation_api.py`) |
| Embedding/index failure | Semantic-memory retrieval suite; `test_failed_index_is_disposable_after_summary_commit` (`test_conversation_memory.py`) |
| Summary failure | `test_provider_failure_retains_only_valid_prior_and_leaves_work_dirty` (`test_conversation_memory.py`) |
| Trace failure | `test_sink_outage_cannot_change_committed_operation_or_finalization_results` (`test_conversation_diagnostics.py`) |
| Internal exception | `test_typed_errors_keep_stable_recovery_status_and_safe_fields` (`test_conversation_api.py`); coordinator malformed-boundary cases |
| Context cannot fit | `test_context_overflow_finishes_without_generation_or_actions` (`test_conversation_playtest.py`) |
| Recovery without another POST | `test_recovery_loop_wakes_a_late_pending_stream_without_another_post` (`test_conversation_worker.py`) |

## Integration defects closed in this handoff

- `test_conversation_playtest.py`: real production graph for purpose-before-stock transfer, receipt fulfillment/publication, idempotent retry, deterministic bow meeting, contextual wreck help, cancellation, non-action questions, quoted requests and context overflow.
- `conversation_signal_smoke.gd`: actual ChatWindow signal binding, continued sequence after clear, gift-to-durable-transport wiring, preservation of an unsent composer.
- `revisioned_state_smoke.gd`: typed `RevisionSet.resources` from the real versioned API, plus existing stale/cross-NPC snapshot and activity ordering checks.
- `ui_rework_smoke.gd`: whole client layout/input flow, durable clear followed by a gift, independent NPC draft preservation. Global rectangles are checked against physical viewport dimensions, matching the current UI scale.
- `bow_quest_smoke.gd`: current moving NPC position, explicit purpose, real inventory, pickup, materials, elapsed crafting delay and exactly one bow.

## Limits

Mechanical assertions and local pilot readiness are separate from semantic language-quality percentages. The human review waiver does not provide calibrated judge agreement or evidence of the release thresholds. The production semantic canon extractor remains fail-closed. Latency/readability and broad release remain provisional under evaluation-release/T03.
