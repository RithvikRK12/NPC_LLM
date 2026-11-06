# Recorded API demonstration

This is a saved transcript of real API/model execution against a disposable world. It is not live execution, a Godot playthrough or a screen recording.

Results: 26/26 scenario checks; 262/262 trace checks. Release readiness is unassessed.

## Attempt 1 — A-01 (NPC 1)

Player: Where is the Gatherer?

NPC: Gatherer is usually at the forest edge. I don't have an observed current position.

Result: PASS; 5.079 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "76f2e435-decd-4e9a-89b4-83b674773458",
  "recipient_id": 1,
  "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "succeeded",
    "authoritative_override": false
  },
  "proposal": {
    "answer_kind": "answer",
    "fact_ids": [
      "person.gatherer.location"
    ],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:06.555576+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:06.555576+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:06.555576+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:06.555576+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:06.555576+00:00"
      }
    ],
    "retrieved_memory_provenance": [],
    "memory_retrieval": {
      "mode": "empty",
      "reason": "no_eligible_indexed_vectors",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 0,
      "lexical_candidates": 0,
      "selected_ids": []
    },
    "recent_dialogue_messages": 0
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": [
      "person.gatherer.location"
    ]
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "76f2e435-decd-4e9a-89b4-83b674773458",
    "conversation_id": 1,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.014331,
    "generation": 4.997666,
    "through_memory_write": 5.067724
  }
}
```

## Attempt 1 — A-01-followup (NPC 1)

Player: Where can I find him?

NPC: Gatherer is usually at the forest edge. I don't have an observed current position.

Result: PASS; 3.607 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "b70d6b27-8eaf-4830-a789-90e3840ccfe7",
  "recipient_id": 1,
  "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "succeeded",
    "authoritative_override": false
  },
  "proposal": {
    "answer_kind": "answer",
    "fact_ids": [
      "person.gatherer.location"
    ],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:10.185311+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:10.185311+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:10.185311+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:10.185311+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:10.185311+00:00"
      }
    ],
    "retrieved_memory_provenance": [],
    "memory_retrieval": {
      "mode": "empty",
      "reason": "no_eligible_indexed_vectors",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 0,
      "lexical_candidates": 0,
      "selected_ids": []
    },
    "recent_dialogue_messages": 2
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": [
      "person.gatherer.location"
    ]
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "b70d6b27-8eaf-4830-a789-90e3840ccfe7",
    "conversation_id": 2,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.00161,
    "generation": 3.586568,
    "through_memory_write": 3.600292
  }
}
```

## Attempt 1 — A-02 (NPC 1)

Player: How do I get there?

NPC: I don't have verified directions to the forest edge.

Result: PASS; 1.58 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "23967db2-5a84-4462-96cd-14d6026c1545",
  "recipient_id": 1,
  "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "succeeded",
    "authoritative_override": false
  },
  "proposal": {
    "answer_kind": "answer",
    "fact_ids": [
      "person.gatherer.route"
    ],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:11.770255+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:11.770255+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:11.770255+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:11.770255+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:11.770255+00:00"
      }
    ],
    "retrieved_memory_provenance": [],
    "memory_retrieval": {
      "mode": "empty",
      "reason": "no_eligible_indexed_vectors",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 0,
      "lexical_candidates": 0,
      "selected_ids": []
    },
    "recent_dialogue_messages": 4
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": [
      "person.gatherer.route"
    ]
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "23967db2-5a84-4462-96cd-14d6026c1545",
    "conversation_id": 3,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.003199,
    "generation": 1.560372,
    "through_memory_write": 1.573394
  }
}
```

## Attempt 1 — A-04 (NPC 1)

Player: Where is Moon Castle?

NPC: I don't have verified information about that. Which known villager, place or bow requirement do you mean?

Result: PASS; 2.802 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "5f46a00d-be4e-4786-a72e-f9595f16ab9a",
  "recipient_id": 1,
  "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "succeeded",
    "authoritative_override": false
  },
  "proposal": {
    "answer_kind": "clarify",
    "fact_ids": [],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:14.576030+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:14.576030+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:14.576030+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:14.576030+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:14.576030+00:00"
      }
    ],
    "retrieved_memory_provenance": [],
    "memory_retrieval": {
      "mode": "empty",
      "reason": "no_eligible_indexed_vectors",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 0,
      "lexical_candidates": 0,
      "selected_ids": []
    },
    "recent_dialogue_messages": 6
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": []
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": false,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": true,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "clarify": 0.21000000000000002
    },
    "selection": "clarify",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "5f46a00d-be4e-4786-a72e-f9595f16ab9a",
    "conversation_id": 4,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.003623,
    "generation": 2.782242,
    "through_memory_write": 2.795122
  }
}
```

## Attempt 1 — B-02-claim (NPC 1)

Player: I gave you wood

NPC: Verified bow materials delivered to the Craftsman: no materials recorded.

Result: PASS; 2.751 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "ddd68385-914d-4c51-a48c-28aa8542578c",
  "recipient_id": 1,
  "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "succeeded",
    "authoritative_override": false
  },
  "proposal": {
    "answer_kind": "answer",
    "fact_ids": [
      "quest.bow.delivered"
    ],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:16.704840+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:16.704840+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:16.704840+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:16.704840+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:16.704840+00:00"
      }
    ],
    "retrieved_memory_provenance": [],
    "memory_retrieval": {
      "mode": "empty",
      "reason": "no_eligible_indexed_vectors",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 0,
      "lexical_candidates": 0,
      "selected_ids": []
    },
    "recent_dialogue_messages": 8
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": [
      "quest.bow.delivered"
    ]
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "ddd68385-914d-4c51-a48c-28aa8542578c",
    "conversation_id": 5,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": true,
    "stored": true,
    "memory_id": 1,
    "source_event_id": "ddd68385-914d-4c51-a48c-28aa8542578c",
    "epistemic_status": "claim",
    "authority": "reported"
  },
  "timings_seconds": {
    "context": 0.005046,
    "generation": 2.104433,
    "through_memory_write": 2.682913
  }
}
```

## Attempt 1 — D-02-recall (NPC 1)

Player: What materials have I actually delivered?

NPC: Verified bow materials delivered to the Craftsman: no materials recorded.

Result: PASS; 4.021 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "fbf94aa8-1e9f-4abb-8f2a-eff8a546f3a0",
  "recipient_id": 1,
  "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "succeeded",
    "authoritative_override": false
  },
  "proposal": {
    "answer_kind": "answer",
    "fact_ids": [
      "quest.bow.delivered"
    ],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.320096+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.320096+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.320096+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.320096+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.320096+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "ddd68385-914d-4c51-a48c-28aa8542578c"
      }
    ],
    "memory_retrieval": {
      "mode": "semantic",
      "reason": "query_embedding_available",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 1,
      "lexical_candidates": 0,
      "selected_ids": [
        1
      ]
    },
    "recent_dialogue_messages": 10
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": [
      "quest.bow.delivered"
    ]
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "fbf94aa8-1e9f-4abb-8f2a-eff8a546f3a0",
    "conversation_id": 6,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.019793,
    "generation": 3.934906,
    "through_memory_write": 3.983665
  }
}
```

## Attempt 1 — C-01-helpful (NPC 1)

Player: Can I have rope?

NPC: Glad to help. Before I give you the rope, why do you need it?

Result: PASS; 0.045 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "0c8087ef-0a39-402b-9cc7-769ea30666cd",
  "recipient_id": 1,
  "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "bypassed",
    "authoritative_override": true
  },
  "proposal": {
    "answer_kind": null,
    "fact_ids": [],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.385116+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.385116+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.385116+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.385116+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.385116+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "ddd68385-914d-4c51-a48c-28aa8542578c"
      }
    ],
    "memory_retrieval": {
      "mode": "semantic",
      "reason": "query_embedding_available",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 1,
      "lexical_candidates": 0,
      "selected_ids": [
        1
      ]
    },
    "recent_dialogue_messages": 12
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": []
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": false,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": true,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": true,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "clarify": 0.21000000000000002,
      "cooperate": 0.75
    },
    "selection": "cooperate",
    "mapping": {
      "action": "ask_question",
      "item": "rope",
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "0c8087ef-0a39-402b-9cc7-769ea30666cd",
    "conversation_id": 7,
    "action": "ask_question",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": true,
    "stored": true,
    "memory_id": 2,
    "source_event_id": "0c8087ef-0a39-402b-9cc7-769ea30666cd",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.013376,
    "generation": 1e-06,
    "through_memory_write": 0.028013
  }
}
```

## Attempt 1 — B-03-transfer (NPC 1)

Player: For my work in the village

NPC: Glad to help. Thanks for explaining. Here, take my rope. It's yours now.

Result: PASS; 0.051 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "820abcb9-ae45-4034-b064-d0f1df1552f6",
  "recipient_id": 1,
  "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "bypassed",
    "authoritative_override": true
  },
  "proposal": {
    "answer_kind": null,
    "fact_ids": [],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.434057+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.434057+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.434057+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.434057+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.434057+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "ddd68385-914d-4c51-a48c-28aa8542578c"
      },
      {
        "id": 2,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "0c8087ef-0a39-402b-9cc7-769ea30666cd"
      }
    ],
    "memory_retrieval": {
      "mode": "semantic",
      "reason": "query_embedding_available",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 2,
      "lexical_candidates": 0,
      "selected_ids": [
        1,
        2
      ]
    },
    "recent_dialogue_messages": 12
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": []
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": false,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": true,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "cooperate": 0.75
    },
    "selection": "cooperate",
    "mapping": {
      "action": "give_item",
      "item": "rope",
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "820abcb9-ae45-4034-b064-d0f1df1552f6",
    "conversation_id": 8,
    "action": "give_item",
    "transfer": {
      "action": "give_item",
      "item": "rope",
      "source_before": 1,
      "source_after": 0,
      "destination_before": 0,
      "destination_after": 1
    },
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": true,
    "stored": true,
    "memory_id": 3,
    "source_event_id": "820abcb9-ae45-4034-b064-d0f1df1552f6",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.015989,
    "generation": 1e-06,
    "through_memory_write": 0.032381
  }
}
```

## Attempt 1 — B-03-repeat (NPC 1)

Player: Give me rope

NPC: I don't have any rope left to give you.

Result: PASS; 0.033 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "2024c58e-14ae-4270-af08-9a793202f8d9",
  "recipient_id": 1,
  "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "bypassed",
    "authoritative_override": true
  },
  "proposal": {
    "answer_kind": null,
    "fact_ids": [],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.487656+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.487656+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.487656+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.487656+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.487656+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 3,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "820abcb9-ae45-4034-b064-d0f1df1552f6"
      },
      {
        "id": 2,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "0c8087ef-0a39-402b-9cc7-769ea30666cd"
      },
      {
        "id": 1,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "ddd68385-914d-4c51-a48c-28aa8542578c"
      }
    ],
    "memory_retrieval": {
      "mode": "semantic",
      "reason": "query_embedding_available",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 3,
      "lexical_candidates": 0,
      "selected_ids": [
        3,
        2,
        1
      ]
    },
    "recent_dialogue_messages": 12
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": []
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "2024c58e-14ae-4270-af08-9a793202f8d9",
    "conversation_id": 9,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.0152,
    "generation": 1e-06,
    "through_memory_write": 0.018142
  }
}
```

## Attempt 1 — C-01-cautious (NPC 1)

Player: Can I have hammer?

NPC: Let's be careful. Before I give you the hammer, why do you need it?

Result: PASS; 0.047 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "ef727fb6-f6f3-457b-aca7-b6fa7567ff1e",
  "recipient_id": 1,
  "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "bypassed",
    "authoritative_override": true
  },
  "proposal": {
    "answer_kind": null,
    "fact_ids": [],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.523330+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.523330+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.523330+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.523330+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.523330+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "ddd68385-914d-4c51-a48c-28aa8542578c"
      },
      {
        "id": 3,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "820abcb9-ae45-4034-b064-d0f1df1552f6"
      },
      {
        "id": 2,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "0c8087ef-0a39-402b-9cc7-769ea30666cd"
      }
    ],
    "memory_retrieval": {
      "mode": "semantic",
      "reason": "query_embedding_available",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 3,
      "lexical_candidates": 0,
      "selected_ids": [
        1,
        3,
        2
      ]
    },
    "recent_dialogue_messages": 12
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": []
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.65,
      "fear": 0.6,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.1,
        "high": 0.7
      },
      "fear": {
        "low": 0.2,
        "high": 0.6
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 0.2,
      "distrust": 0.1,
      "afraid": 0.6,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.4,
      "caution": 0.5789473684210527,
      "expression": 0.4
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": false,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": true,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": true,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "clarify": 0.5131578947368421,
      "cooperate": 0.4
    },
    "selection": "clarify",
    "mapping": {
      "action": "ask_question",
      "item": "hammer",
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "ef727fb6-f6f3-457b-aca7-b6fa7567ff1e",
    "conversation_id": 10,
    "action": "ask_question",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": true,
    "stored": true,
    "memory_id": 4,
    "source_event_id": "ef727fb6-f6f3-457b-aca7-b6fa7567ff1e",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.013789,
    "generation": 1e-06,
    "through_memory_write": 0.029172
  }
}
```

## Attempt 1 — C-01-cancel (NPC 1)

Player: cancel

NPC: All right, I'll keep it for now.

Result: PASS; 0.043 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "bb3553fd-c8f6-4a19-b631-af0403ea90fe",
  "recipient_id": 1,
  "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "bypassed",
    "authoritative_override": true
  },
  "proposal": {
    "answer_kind": null,
    "fact_ids": [],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.573356+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.573356+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.573356+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.573356+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.573356+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 4,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "ef727fb6-f6f3-457b-aca7-b6fa7567ff1e"
      },
      {
        "id": 2,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "0c8087ef-0a39-402b-9cc7-769ea30666cd"
      },
      {
        "id": 1,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "ddd68385-914d-4c51-a48c-28aa8542578c"
      },
      {
        "id": 3,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "820abcb9-ae45-4034-b064-d0f1df1552f6"
      }
    ],
    "memory_retrieval": {
      "mode": "semantic",
      "reason": "query_embedding_available",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 4,
      "lexical_candidates": 0,
      "selected_ids": [
        4,
        2,
        1,
        3
      ]
    },
    "recent_dialogue_messages": 12
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": []
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.65,
      "fear": 0.6,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.1,
        "high": 0.7
      },
      "fear": {
        "low": 0.2,
        "high": 0.6
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 0.2,
      "distrust": 0.1,
      "afraid": 0.6,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.4,
      "caution": 0.5789473684210527,
      "expression": 0.4
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "bb3553fd-c8f6-4a19-b631-af0403ea90fe",
    "conversation_id": 11,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": true,
    "stored": true,
    "memory_id": 5,
    "source_event_id": "bb3553fd-c8f6-4a19-b631-af0403ea90fe",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.013433,
    "generation": 1e-06,
    "through_memory_write": 0.028954
  }
}
```

## Attempt 1 — C-01-distrustful (NPC 1)

Player: Can I have saw?

NPC: I'd rather keep my saw for now. You can still ask me questions.

Result: PASS; 0.033 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "4fefcf44-6f9f-47b1-a7a4-b1dc58388a85",
  "recipient_id": 1,
  "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "bypassed",
    "authoritative_override": true
  },
  "proposal": {
    "answer_kind": null,
    "fact_ids": [],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.623019+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.623019+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.623019+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.623019+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:21.623019+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "ddd68385-914d-4c51-a48c-28aa8542578c"
      },
      {
        "id": 3,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "820abcb9-ae45-4034-b064-d0f1df1552f6"
      },
      {
        "id": 2,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "0c8087ef-0a39-402b-9cc7-769ea30666cd"
      },
      {
        "id": 4,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "ef727fb6-f6f3-457b-aca7-b6fa7567ff1e"
      },
      {
        "id": 5,
        "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "bb3553fd-c8f6-4a19-b631-af0403ea90fe"
      }
    ],
    "memory_retrieval": {
      "mode": "semantic",
      "reason": "query_embedding_available",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 5,
      "lexical_candidates": 0,
      "selected_ids": [
        1,
        3,
        2,
        4,
        5
      ]
    },
    "recent_dialogue_messages": 12
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": []
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.05,
      "fear": 0.8,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 1.0,
        "high": 0.0
      },
      "fear": {
        "low": 0.0,
        "high": 1.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 0.0,
      "distrust": 1.0,
      "afraid": 1.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.19999999999999998,
      "caution": 0.7999999999999999,
      "expression": 0.19999999999999998
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": false,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": true,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": true,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": true,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "clarify": 0.6900000000000001,
      "cooperate": 0.19999999999999998,
      "refuse": 0.74
    },
    "selection": "refuse",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "guarded",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "4fefcf44-6f9f-47b1-a7a4-b1dc58388a85",
    "conversation_id": 12,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.01486,
    "generation": 1e-06,
    "through_memory_write": 0.017725
  }
}
```

## Attempt 1 — D-02-recipient (NPC 2)

Player: Where is the Craftsman?

NPC: Craftsman is usually at the workshop. I don't have an observed current position.

Result: PASS; 2.601 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "1d2bd54d-f7a1-48d7-baa3-3861eb402a16",
  "recipient_id": 2,
  "game_scope": "b308179b-c023-45f8-b6ca-2d58b4698d6f",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "succeeded",
    "authoritative_override": false
  },
  "proposal": {
    "answer_kind": "answer",
    "fact_ids": [
      "person.craftsman.location"
    ],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:24.231792+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:24.231792+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:24.231792+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:24.231792+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:24.231792+00:00"
      }
    ],
    "retrieved_memory_provenance": [],
    "memory_retrieval": {
      "mode": "empty",
      "reason": "no_eligible_indexed_vectors",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 0,
      "lexical_candidates": 0,
      "selected_ids": []
    },
    "recent_dialogue_messages": 0
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": [
      "person.craftsman.location"
    ]
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.5,
      "fear": 0.25,
      "aggression": 0.05,
      "curiosity": 0.7
    },
    "memberships": {
      "trust": {
        "low": 0.4,
        "high": 0.4
      },
      "fear": {
        "low": 0.9,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.0,
        "high": 0.8
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 0.4,
      "distrust": 0.4,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.8
    },
    "outputs": {
      "cooperation": 0.5307692307692307,
      "caution": 0.4307692307692308,
      "expression": 0.5615384615384615
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "1d2bd54d-f7a1-48d7-baa3-3861eb402a16",
    "conversation_id": 13,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.001687,
    "generation": 2.581046,
    "through_memory_write": 2.593748
  }
}
```

## Attempt 2 — A-01 (NPC 1)

Player: Where is the Gatherer?

NPC: Gatherer is usually at the forest edge. I don't have an observed current position.

Result: PASS; 0.903 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "e58fac56-3da4-4ce7-bab2-d50d09589f38",
  "recipient_id": 1,
  "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "succeeded",
    "authoritative_override": false
  },
  "proposal": {
    "answer_kind": "answer",
    "fact_ids": [
      "person.gatherer.location"
    ],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:25.142702+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:25.142702+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:25.142702+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:25.142702+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:25.142702+00:00"
      }
    ],
    "retrieved_memory_provenance": [],
    "memory_retrieval": {
      "mode": "empty",
      "reason": "no_eligible_indexed_vectors",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 0,
      "lexical_candidates": 0,
      "selected_ids": []
    },
    "recent_dialogue_messages": 0
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": [
      "person.gatherer.location"
    ]
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "e58fac56-3da4-4ce7-bab2-d50d09589f38",
    "conversation_id": 1,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.001541,
    "generation": 0.885371,
    "through_memory_write": 0.895747
  }
}
```

## Attempt 2 — A-01-followup (NPC 1)

Player: Where can I find him?

NPC: Gatherer is usually at the forest edge. I don't have an observed current position.

Result: PASS; 1.737 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "e3f6bf9b-1ed4-4991-980f-60ab33a74857",
  "recipient_id": 1,
  "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "succeeded",
    "authoritative_override": false
  },
  "proposal": {
    "answer_kind": "answer",
    "fact_ids": [
      "person.gatherer.location"
    ],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:26.892214+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:26.892214+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:26.892214+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:26.892214+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:26.892214+00:00"
      }
    ],
    "retrieved_memory_provenance": [],
    "memory_retrieval": {
      "mode": "empty",
      "reason": "no_eligible_indexed_vectors",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 0,
      "lexical_candidates": 0,
      "selected_ids": []
    },
    "recent_dialogue_messages": 2
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": [
      "person.gatherer.location"
    ]
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "e3f6bf9b-1ed4-4991-980f-60ab33a74857",
    "conversation_id": 2,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.002529,
    "generation": 1.724676,
    "through_memory_write": 1.732196
  }
}
```

## Attempt 2 — A-02 (NPC 1)

Player: How do I get there?

NPC: I don't have verified directions to the forest edge.

Result: PASS; 1.552 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "b1e1ff27-d717-4165-9e08-f825fc3d410c",
  "recipient_id": 1,
  "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "succeeded",
    "authoritative_override": false
  },
  "proposal": {
    "answer_kind": "answer",
    "fact_ids": [
      "person.gatherer.route"
    ],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:28.439854+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:28.439854+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:28.439854+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:28.439854+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:28.439854+00:00"
      }
    ],
    "retrieved_memory_provenance": [],
    "memory_retrieval": {
      "mode": "empty",
      "reason": "no_eligible_indexed_vectors",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 0,
      "lexical_candidates": 0,
      "selected_ids": []
    },
    "recent_dialogue_messages": 4
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": [
      "person.gatherer.route"
    ]
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "b1e1ff27-d717-4165-9e08-f825fc3d410c",
    "conversation_id": 3,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.001852,
    "generation": 1.528443,
    "through_memory_write": 1.541409
  }
}
```

## Attempt 2 — A-04 (NPC 1)

Player: Where is Moon Castle?

NPC: I don't have verified information about that. Which known villager, place or bow requirement do you mean?

Result: PASS; 0.984 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "462ce77e-c9cc-4a07-834b-b5a8f08d7193",
  "recipient_id": 1,
  "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "succeeded",
    "authoritative_override": false
  },
  "proposal": {
    "answer_kind": "clarify",
    "fact_ids": [],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:29.438116+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:29.438116+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:29.438116+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:29.438116+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:29.438116+00:00"
      }
    ],
    "retrieved_memory_provenance": [],
    "memory_retrieval": {
      "mode": "empty",
      "reason": "no_eligible_indexed_vectors",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 0,
      "lexical_candidates": 0,
      "selected_ids": []
    },
    "recent_dialogue_messages": 6
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": []
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": false,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": true,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "clarify": 0.21000000000000002
    },
    "selection": "clarify",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "462ce77e-c9cc-4a07-834b-b5a8f08d7193",
    "conversation_id": 4,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.004088,
    "generation": 0.95946,
    "through_memory_write": 0.974611
  }
}
```

## Attempt 2 — B-02-claim (NPC 1)

Player: I gave you wood

NPC: Verified bow materials delivered to the Craftsman: no materials recorded.

Result: PASS; 2.309 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "cebba93a-c1d8-4d29-a648-3b6166105867",
  "recipient_id": 1,
  "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "succeeded",
    "authoritative_override": false
  },
  "proposal": {
    "answer_kind": "answer",
    "fact_ids": [
      "quest.bow.delivered"
    ],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:31.713878+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:31.713878+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:31.713878+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:31.713878+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:31.713878+00:00"
      }
    ],
    "retrieved_memory_provenance": [],
    "memory_retrieval": {
      "mode": "empty",
      "reason": "no_eligible_indexed_vectors",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 0,
      "lexical_candidates": 0,
      "selected_ids": []
    },
    "recent_dialogue_messages": 8
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": [
      "quest.bow.delivered"
    ]
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "cebba93a-c1d8-4d29-a648-3b6166105867",
    "conversation_id": 5,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": true,
    "stored": true,
    "memory_id": 1,
    "source_event_id": "cebba93a-c1d8-4d29-a648-3b6166105867",
    "epistemic_status": "claim",
    "authority": "reported"
  },
  "timings_seconds": {
    "context": 0.003122,
    "generation": 2.243313,
    "through_memory_write": 2.280675
  }
}
```

## Attempt 2 — D-02-recall (NPC 1)

Player: What materials have I actually delivered?

NPC: Verified bow materials delivered to the Craftsman: no materials recorded.

Result: PASS; 3.415 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "d4a771bb-dd5b-4d1b-8c0b-995f1c393e6f",
  "recipient_id": 1,
  "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "succeeded",
    "authoritative_override": false
  },
  "proposal": {
    "answer_kind": "answer",
    "fact_ids": [
      "quest.bow.delivered"
    ],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.159070+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.159070+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.159070+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.159070+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.159070+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "cebba93a-c1d8-4d29-a648-3b6166105867"
      }
    ],
    "memory_retrieval": {
      "mode": "semantic",
      "reason": "query_embedding_available",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 1,
      "lexical_candidates": 0,
      "selected_ids": [
        1
      ]
    },
    "recent_dialogue_messages": 10
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": [
      "quest.bow.delivered"
    ]
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "d4a771bb-dd5b-4d1b-8c0b-995f1c393e6f",
    "conversation_id": 6,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.020742,
    "generation": 3.354524,
    "through_memory_write": 3.386547
  }
}
```

## Attempt 2 — C-01-helpful (NPC 1)

Player: Can I have rope?

NPC: Glad to help. Before I give you the rope, why do you need it?

Result: PASS; 0.055 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "1b7850f5-d25f-4371-9dbc-ddad6a42c502",
  "recipient_id": 1,
  "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "bypassed",
    "authoritative_override": true
  },
  "proposal": {
    "answer_kind": null,
    "fact_ids": [],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.223677+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.223677+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.223677+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.223677+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.223677+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "cebba93a-c1d8-4d29-a648-3b6166105867"
      }
    ],
    "memory_retrieval": {
      "mode": "semantic",
      "reason": "query_embedding_available",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 1,
      "lexical_candidates": 0,
      "selected_ids": [
        1
      ]
    },
    "recent_dialogue_messages": 12
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": []
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": false,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": true,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": true,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "clarify": 0.21000000000000002,
      "cooperate": 0.75
    },
    "selection": "cooperate",
    "mapping": {
      "action": "ask_question",
      "item": "rope",
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "1b7850f5-d25f-4371-9dbc-ddad6a42c502",
    "conversation_id": 7,
    "action": "ask_question",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": true,
    "stored": true,
    "memory_id": 2,
    "source_event_id": "1b7850f5-d25f-4371-9dbc-ddad6a42c502",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.017902,
    "generation": 2e-06,
    "through_memory_write": 0.036626
  }
}
```

## Attempt 2 — B-03-transfer (NPC 1)

Player: For my work in the village

NPC: Glad to help. Thanks for explaining. Here, take my rope. It's yours now.

Result: PASS; 0.053 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "93b61e83-7fa6-46c0-9774-24b41258bcb8",
  "recipient_id": 1,
  "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "bypassed",
    "authoritative_override": true
  },
  "proposal": {
    "answer_kind": null,
    "fact_ids": [],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.283418+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.283418+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.283418+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.283418+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.283418+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "cebba93a-c1d8-4d29-a648-3b6166105867"
      },
      {
        "id": 2,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "1b7850f5-d25f-4371-9dbc-ddad6a42c502"
      }
    ],
    "memory_retrieval": {
      "mode": "semantic",
      "reason": "query_embedding_available",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 2,
      "lexical_candidates": 0,
      "selected_ids": [
        1,
        2
      ]
    },
    "recent_dialogue_messages": 12
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": []
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": false,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": true,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "cooperate": 0.75
    },
    "selection": "cooperate",
    "mapping": {
      "action": "give_item",
      "item": "rope",
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "93b61e83-7fa6-46c0-9774-24b41258bcb8",
    "conversation_id": 8,
    "action": "give_item",
    "transfer": {
      "action": "give_item",
      "item": "rope",
      "source_before": 1,
      "source_after": 0,
      "destination_before": 0,
      "destination_after": 1
    },
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": true,
    "stored": true,
    "memory_id": 3,
    "source_event_id": "93b61e83-7fa6-46c0-9774-24b41258bcb8",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.016206,
    "generation": 1e-06,
    "through_memory_write": 0.034135
  }
}
```

## Attempt 2 — B-03-repeat (NPC 1)

Player: Give me rope

NPC: I don't have any rope left to give you.

Result: PASS; 0.036 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "d0c78f9f-07fd-4d53-9bc5-5fa89ef0da4e",
  "recipient_id": 1,
  "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "bypassed",
    "authoritative_override": true
  },
  "proposal": {
    "answer_kind": null,
    "fact_ids": [],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.343289+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.343289+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.343289+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.343289+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.343289+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 3,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "93b61e83-7fa6-46c0-9774-24b41258bcb8"
      },
      {
        "id": 2,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "1b7850f5-d25f-4371-9dbc-ddad6a42c502"
      },
      {
        "id": 1,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "cebba93a-c1d8-4d29-a648-3b6166105867"
      }
    ],
    "memory_retrieval": {
      "mode": "semantic",
      "reason": "query_embedding_available",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 3,
      "lexical_candidates": 0,
      "selected_ids": [
        3,
        2,
        1
      ]
    },
    "recent_dialogue_messages": 12
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": []
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.95,
      "fear": 0.05,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.0,
        "high": 1.0
      },
      "fear": {
        "low": 1.0,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 1.0,
      "distrust": 0.0,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.75,
      "caution": 0.2,
      "expression": 0.75
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "d0c78f9f-07fd-4d53-9bc5-5fa89ef0da4e",
    "conversation_id": 9,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.016491,
    "generation": 2e-06,
    "through_memory_write": 0.019689
  }
}
```

## Attempt 2 — C-01-cautious (NPC 1)

Player: Can I have hammer?

NPC: Let's be careful. Before I give you the hammer, why do you need it?

Result: PASS; 0.048 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "927ab103-9d40-4adc-93e7-a550969c69b6",
  "recipient_id": 1,
  "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "bypassed",
    "authoritative_override": true
  },
  "proposal": {
    "answer_kind": null,
    "fact_ids": [],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.385666+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.385666+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.385666+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.385666+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.385666+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "cebba93a-c1d8-4d29-a648-3b6166105867"
      },
      {
        "id": 3,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "93b61e83-7fa6-46c0-9774-24b41258bcb8"
      },
      {
        "id": 2,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "1b7850f5-d25f-4371-9dbc-ddad6a42c502"
      }
    ],
    "memory_retrieval": {
      "mode": "semantic",
      "reason": "query_embedding_available",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 3,
      "lexical_candidates": 0,
      "selected_ids": [
        1,
        3,
        2
      ]
    },
    "recent_dialogue_messages": 12
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": []
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.65,
      "fear": 0.6,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.1,
        "high": 0.7
      },
      "fear": {
        "low": 0.2,
        "high": 0.6
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 0.2,
      "distrust": 0.1,
      "afraid": 0.6,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.4,
      "caution": 0.5789473684210527,
      "expression": 0.4
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": false,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": true,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": true,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "clarify": 0.5131578947368421,
      "cooperate": 0.4
    },
    "selection": "clarify",
    "mapping": {
      "action": "ask_question",
      "item": "hammer",
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "927ab103-9d40-4adc-93e7-a550969c69b6",
    "conversation_id": 10,
    "action": "ask_question",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": true,
    "stored": true,
    "memory_id": 4,
    "source_event_id": "927ab103-9d40-4adc-93e7-a550969c69b6",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.015328,
    "generation": 1e-06,
    "through_memory_write": 0.031524
  }
}
```

## Attempt 2 — C-01-cancel (NPC 1)

Player: cancel

NPC: All right, I'll keep it for now.

Result: PASS; 0.04 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "51a5a578-9206-4c9f-a190-9558d371b687",
  "recipient_id": 1,
  "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "bypassed",
    "authoritative_override": true
  },
  "proposal": {
    "answer_kind": null,
    "fact_ids": [],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.437708+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.437708+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.437708+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.437708+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.437708+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 4,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "927ab103-9d40-4adc-93e7-a550969c69b6"
      },
      {
        "id": 2,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "1b7850f5-d25f-4371-9dbc-ddad6a42c502"
      },
      {
        "id": 1,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "cebba93a-c1d8-4d29-a648-3b6166105867"
      },
      {
        "id": 3,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "93b61e83-7fa6-46c0-9774-24b41258bcb8"
      }
    ],
    "memory_retrieval": {
      "mode": "semantic",
      "reason": "query_embedding_available",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 4,
      "lexical_candidates": 0,
      "selected_ids": [
        4,
        2,
        1,
        3
      ]
    },
    "recent_dialogue_messages": 12
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": []
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.65,
      "fear": 0.6,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 0.1,
        "high": 0.7
      },
      "fear": {
        "low": 0.2,
        "high": 0.6
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 0.2,
      "distrust": 0.1,
      "afraid": 0.6,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.4,
      "caution": 0.5789473684210527,
      "expression": 0.4
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "51a5a578-9206-4c9f-a190-9558d371b687",
    "conversation_id": 11,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": true,
    "stored": true,
    "memory_id": 5,
    "source_event_id": "51a5a578-9206-4c9f-a190-9558d371b687",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.012128,
    "generation": 1e-06,
    "through_memory_write": 0.026666
  }
}
```

## Attempt 2 — C-01-distrustful (NPC 1)

Player: Can I have saw?

NPC: I'd rather keep my saw for now. You can still ask me questions.

Result: PASS; 0.033 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "1327ebca-2cf6-4bc9-87c3-d8eaf595dba7",
  "recipient_id": 1,
  "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "bypassed",
    "authoritative_override": true
  },
  "proposal": {
    "answer_kind": null,
    "fact_ids": [],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.488033+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.488033+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.488033+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.488033+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:35.488033+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "cebba93a-c1d8-4d29-a648-3b6166105867"
      },
      {
        "id": 3,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "93b61e83-7fa6-46c0-9774-24b41258bcb8"
      },
      {
        "id": 2,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "1b7850f5-d25f-4371-9dbc-ddad6a42c502"
      },
      {
        "id": 4,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "927ab103-9d40-4adc-93e7-a550969c69b6"
      },
      {
        "id": 5,
        "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "51a5a578-9206-4c9f-a190-9558d371b687"
      }
    ],
    "memory_retrieval": {
      "mode": "semantic",
      "reason": "query_embedding_available",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 5,
      "lexical_candidates": 0,
      "selected_ids": [
        1,
        3,
        2,
        4,
        5
      ]
    },
    "recent_dialogue_messages": 12
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": []
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.05,
      "fear": 0.8,
      "aggression": 0.05,
      "curiosity": 0.3
    },
    "memberships": {
      "trust": {
        "low": 1.0,
        "high": 0.0
      },
      "fear": {
        "low": 0.0,
        "high": 1.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.8,
        "high": 0.0
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 0.0,
      "distrust": 1.0,
      "afraid": 1.0,
      "aggressive": 0.0,
      "curious": 0.0
    },
    "outputs": {
      "cooperation": 0.19999999999999998,
      "caution": 0.7999999999999999,
      "expression": 0.19999999999999998
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": false,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": true,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": true,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": true,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "clarify": 0.6900000000000001,
      "cooperate": 0.19999999999999998,
      "refuse": 0.74
    },
    "selection": "refuse",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "guarded",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "1327ebca-2cf6-4bc9-87c3-d8eaf595dba7",
    "conversation_id": 12,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.014555,
    "generation": 2e-06,
    "through_memory_write": 0.01727
  }
}
```

## Attempt 2 — D-02-recipient (NPC 2)

Player: Where is the Craftsman?

NPC: Craftsman is usually at the workshop. I don't have an observed current position.

Result: PASS; 0.982 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "2e760bed-c748-4bdd-aa2b-d2bcf3de64ab",
  "recipient_id": 2,
  "game_scope": "b3af74bf-67d1-43b7-a452-28ecbd528b8d",
  "configuration": {
    "provider": "OpenAICompatibleProvider",
    "model": "llama3:latest",
    "structured_output": true,
    "temperature": 0.2,
    "embedding_model": "nomic-embed-text",
    "embedding_revision": "v1",
    "embedding_dimensions": 768,
    "behavior_policy": {
      "id": "village-response",
      "version": "1"
    }
  },
  "generation": {
    "status": "succeeded",
    "authoritative_override": false
  },
  "proposal": {
    "answer_kind": "answer",
    "fact_ids": [
      "person.craftsman.location"
    ],
    "unrecognized_fact_count": 0,
    "action": null,
    "item": null,
    "state_update": {},
    "state_update_invalid": false,
    "unrecognized_field_count": 0
  },
  "context": {
    "fact_sources": [
      {
        "id": "person.craftsman.location",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.craftsman.work",
        "source": "database/seed.py; services/quests/bow.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.craftsman.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "person.gatherer.location",
        "source": "database/seed.py; services/validation/items.py",
        "status": "usual",
        "as_of": null
      },
      {
        "id": "person.gatherer.work",
        "source": "database/seed.py; services/validation/items.py",
        "status": "public",
        "as_of": null
      },
      {
        "id": "person.gatherer.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.workshop.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.forest_edge.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.village_square.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "place.well.route",
        "source": "database/seed.py; services/quests/bow.py; frontend/godot/scripts/main.gd",
        "status": "unknown",
        "as_of": null
      },
      {
        "id": "quest.bow.requirements",
        "source": "services/quests/bow.py; Craftsman quest material stock",
        "status": "current",
        "as_of": "2026-10-12T18:21:36.482077+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:21:36.482077+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:21:36.482077+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:21:36.482077+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:21:36.482077+00:00"
      }
    ],
    "retrieved_memory_provenance": [],
    "memory_retrieval": {
      "mode": "empty",
      "reason": "no_eligible_indexed_vectors",
      "candidate_limit_per_path": 40,
      "materialization_limit": 80,
      "result_limit": 5,
      "vector_index_build": "all_eligible_vector_pairs_on_cache_miss",
      "malformed_vector_id_limit": 50,
      "semantic_candidates": 0,
      "lexical_candidates": 0,
      "selected_ids": []
    },
    "recent_dialogue_messages": 0
  },
  "validation": {
    "rejected": false,
    "reason": null,
    "selected_fact_ids": [
      "person.craftsman.location"
    ]
  },
  "behavior": {
    "candidate_state": {
      "trust": 0.5,
      "fear": 0.25,
      "aggression": 0.05,
      "curiosity": 0.7
    },
    "memberships": {
      "trust": {
        "low": 0.4,
        "high": 0.4
      },
      "fear": {
        "low": 0.9,
        "high": 0.0
      },
      "aggression": {
        "low": 1.0,
        "high": 0.0
      },
      "curiosity": {
        "low": 0.0,
        "high": 0.8
      }
    },
    "rule_strengths": {
      "baseline": 1.0,
      "trusted": 0.4,
      "distrust": 0.4,
      "afraid": 0.0,
      "aggressive": 0.0,
      "curious": 0.8
    },
    "outputs": {
      "cooperation": 0.5307692307692307,
      "caution": 0.4307692307692308,
      "expression": 0.5615384615384615
    },
    "ordering": [
      "role_conditioning",
      "final_control_validation",
      "fsec"
    ],
    "eligibility": {
      "answer": {
        "eligible": true,
        "reason": "validated non-request response"
      },
      "clarify": {
        "eligible": false,
        "reason": "clarification already permitted"
      },
      "cooperate": {
        "eligible": false,
        "reason": "authorized request with owned item and supported role"
      },
      "refuse": {
        "eligible": false,
        "reason": "optional owned outgoing item; low cooperation only"
      },
      "offer_recovery": {
        "eligible": false,
        "reason": "no authored recovery route"
      }
    },
    "scores": {
      "answer": 1.0
    },
    "selection": "answer",
    "mapping": {
      "action": "speak",
      "item": null,
      "emotion": "calm",
      "max_dialogue_chars": 240
    }
  },
  "outcome": {
    "event_id": "2e760bed-c748-4bdd-aa2b-d2bcf3de64ab",
    "conversation_id": 13,
    "action": "speak",
    "transfer": null,
    "quest_before": "available",
    "quest_after": "available"
  },
  "memory_write": {
    "important": false,
    "stored": false,
    "memory_id": null,
    "source_event_id": null,
    "epistemic_status": "interpretation",
    "authority": "inferred"
  },
  "timings_seconds": {
    "context": 0.00161,
    "generation": 0.963376,
    "through_memory_write": 0.975006
  }
}
```
