# Recorded API demonstration

This is a saved transcript of real API/model execution against a disposable world. It is not live execution, a Godot playthrough or a screen recording.

Results: 26/26 scenario checks; 262/262 trace checks. Release readiness is unassessed.

## Attempt 1 — A-01 (NPC 1)

Player: Where is the Gatherer?

NPC: Gatherer is usually at the forest edge. I don't have an observed current position.

Result: PASS; 1.017 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "b85ccdd5-5436-4f25-9c99-aad13c070434",
  "recipient_id": 1,
  "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
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
        "as_of": "2026-10-12T18:25:02.155846+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:02.155846+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:02.155846+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:02.155846+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:02.155846+00:00"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "b85ccdd5-5436-4f25-9c99-aad13c070434",
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
    "context": 0.016247,
    "generation": 0.974973,
    "through_memory_write": 1.01014
  }
}
```

## Attempt 1 — A-01-followup (NPC 1)

Player: Where can I find him?

NPC: Gatherer is usually at the forest edge. I don't have an observed current position.

Result: PASS; 1.842 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "33863929-4b71-44a1-b3ad-d2ec64b76db1",
  "recipient_id": 1,
  "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
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
        "as_of": "2026-10-12T18:25:04.005826+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:04.005826+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:04.005826+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:04.005826+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:04.005826+00:00"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "33863929-4b71-44a1-b3ad-d2ec64b76db1",
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
    "context": 0.002121,
    "generation": 1.823952,
    "through_memory_write": 1.835276
  }
}
```

## Attempt 1 — A-02 (NPC 1)

Player: How do I get there?

NPC: I don't have verified directions to the forest edge.

Result: PASS; 1.605 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "f939da39-caf6-4dae-beb6-4127a704e6be",
  "recipient_id": 1,
  "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
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
        "as_of": "2026-10-12T18:25:05.613514+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:05.613514+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:05.613514+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:05.613514+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:05.613514+00:00"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "f939da39-caf6-4dae-beb6-4127a704e6be",
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
    "context": 0.003784,
    "generation": 1.583861,
    "through_memory_write": 1.598105
  }
}
```

## Attempt 1 — A-04 (NPC 1)

Player: Where is Moon Castle?

NPC: I don't have verified information about that. Which known villager, place or bow requirement do you mean?

Result: PASS; 0.868 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "56757411-f319-446b-965e-fd9d0fd5ff44",
  "recipient_id": 1,
  "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
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
        "as_of": "2026-10-12T18:25:06.484876+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:06.484876+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:06.484876+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:06.484876+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:06.484876+00:00"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "56757411-f319-446b-965e-fd9d0fd5ff44",
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
    "context": 0.002512,
    "generation": 0.847529,
    "through_memory_write": 0.860984
  }
}
```

## Attempt 1 — B-02-claim (NPC 1)

Player: I gave you wood

NPC: Verified bow materials delivered to the Craftsman: no materials recorded.

Result: PASS; 2.275 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "de5b56a3-51bc-4b3b-a91f-4d95960fdaed",
  "recipient_id": 1,
  "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
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
        "as_of": "2026-10-12T18:25:08.707837+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:08.707837+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:08.707837+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:08.707837+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:08.707837+00:00"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "de5b56a3-51bc-4b3b-a91f-4d95960fdaed",
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
    "source_event_id": "de5b56a3-51bc-4b3b-a91f-4d95960fdaed",
    "epistemic_status": "claim",
    "authority": "reported"
  },
  "timings_seconds": {
    "context": 0.005061,
    "generation": 2.19704,
    "through_memory_write": 2.243691
  }
}
```

## Attempt 1 — D-02-recall (NPC 1)

Player: What materials have I actually delivered?

NPC: Verified bow materials delivered to the Craftsman: no materials recorded.

Result: PASS; 3.352 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "607ad93e-c9bd-48da-9589-a0afcedf3769",
  "recipient_id": 1,
  "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
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
        "as_of": "2026-10-12T18:25:12.098020+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.098020+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.098020+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.098020+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.098020+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "de5b56a3-51bc-4b3b-a91f-4d95960fdaed"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "607ad93e-c9bd-48da-9589-a0afcedf3769",
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
    "context": 0.018242,
    "generation": 3.295496,
    "through_memory_write": 3.324694
  }
}
```

## Attempt 1 — C-01-helpful (NPC 1)

Player: Can I have rope?

NPC: Glad to help. Before I give you the rope, why do you need it?

Result: PASS; 0.055 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "6ba878b9-df8a-4a0e-a1a4-b0832d39f7cc",
  "recipient_id": 1,
  "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
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
        "as_of": "2026-10-12T18:25:12.154392+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.154392+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.154392+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.154392+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.154392+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "de5b56a3-51bc-4b3b-a91f-4d95960fdaed"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "6ba878b9-df8a-4a0e-a1a4-b0832d39f7cc",
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
    "source_event_id": "6ba878b9-df8a-4a0e-a1a4-b0832d39f7cc",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.017891,
    "generation": 2e-06,
    "through_memory_write": 0.036631
  }
}
```

## Attempt 1 — B-03-transfer (NPC 1)

Player: For my work in the village

NPC: Glad to help. Thanks for explaining. Here, take my rope. It's yours now.

Result: PASS; 0.055 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "1e46756a-8bac-4f0d-bfed-436c65539d99",
  "recipient_id": 1,
  "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
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
        "as_of": "2026-10-12T18:25:12.213076+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.213076+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.213076+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.213076+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.213076+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "de5b56a3-51bc-4b3b-a91f-4d95960fdaed"
      },
      {
        "id": 2,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "6ba878b9-df8a-4a0e-a1a4-b0832d39f7cc"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "1e46756a-8bac-4f0d-bfed-436c65539d99",
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
    "source_event_id": "1e46756a-8bac-4f0d-bfed-436c65539d99",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.01792,
    "generation": 1e-06,
    "through_memory_write": 0.03635
  }
}
```

## Attempt 1 — B-03-repeat (NPC 1)

Player: Give me rope

NPC: I don't have any rope left to give you.

Result: PASS; 0.035 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "56095e96-049b-427b-97a3-0a7e1151df9d",
  "recipient_id": 1,
  "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
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
        "as_of": "2026-10-12T18:25:12.269746+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.269746+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.269746+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.269746+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.269746+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 3,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "1e46756a-8bac-4f0d-bfed-436c65539d99"
      },
      {
        "id": 2,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "6ba878b9-df8a-4a0e-a1a4-b0832d39f7cc"
      },
      {
        "id": 1,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "de5b56a3-51bc-4b3b-a91f-4d95960fdaed"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "56095e96-049b-427b-97a3-0a7e1151df9d",
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
    "context": 0.015929,
    "generation": 1e-06,
    "through_memory_write": 0.019183
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
  "decision_id": "e45ee7f0-2877-4044-85ec-3a76431250d7",
  "recipient_id": 1,
  "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
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
        "as_of": "2026-10-12T18:25:12.308667+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.308667+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.308667+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.308667+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.308667+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "de5b56a3-51bc-4b3b-a91f-4d95960fdaed"
      },
      {
        "id": 3,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "1e46756a-8bac-4f0d-bfed-436c65539d99"
      },
      {
        "id": 2,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "6ba878b9-df8a-4a0e-a1a4-b0832d39f7cc"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "e45ee7f0-2877-4044-85ec-3a76431250d7",
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
    "source_event_id": "e45ee7f0-2877-4044-85ec-3a76431250d7",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.015306,
    "generation": 1e-06,
    "through_memory_write": 0.030968
  }
}
```

## Attempt 1 — C-01-cancel (NPC 1)

Player: cancel

NPC: All right, I'll keep it for now.

Result: PASS; 0.04 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "ee84f2f9-063a-4958-803d-39be4ce206f7",
  "recipient_id": 1,
  "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
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
        "as_of": "2026-10-12T18:25:12.356915+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.356915+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.356915+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.356915+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.356915+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 4,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "e45ee7f0-2877-4044-85ec-3a76431250d7"
      },
      {
        "id": 2,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "6ba878b9-df8a-4a0e-a1a4-b0832d39f7cc"
      },
      {
        "id": 1,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "de5b56a3-51bc-4b3b-a91f-4d95960fdaed"
      },
      {
        "id": 3,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "1e46756a-8bac-4f0d-bfed-436c65539d99"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "ee84f2f9-063a-4958-803d-39be4ce206f7",
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
    "source_event_id": "ee84f2f9-063a-4958-803d-39be4ce206f7",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.012367,
    "generation": 1e-06,
    "through_memory_write": 0.027143
  }
}
```

## Attempt 1 — C-01-distrustful (NPC 1)

Player: Can I have saw?

NPC: I'd rather keep my saw for now. You can still ask me questions.

Result: PASS; 0.031 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "76226deb-dfb2-45b5-8b81-03c9cddc4ad3",
  "recipient_id": 1,
  "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
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
        "as_of": "2026-10-12T18:25:12.403180+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.403180+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.403180+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.403180+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:12.403180+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "de5b56a3-51bc-4b3b-a91f-4d95960fdaed"
      },
      {
        "id": 3,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "1e46756a-8bac-4f0d-bfed-436c65539d99"
      },
      {
        "id": 2,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "6ba878b9-df8a-4a0e-a1a4-b0832d39f7cc"
      },
      {
        "id": 4,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "e45ee7f0-2877-4044-85ec-3a76431250d7"
      },
      {
        "id": 5,
        "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "ee84f2f9-063a-4958-803d-39be4ce206f7"
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
      "max_dialogue_chars": 240,
      "emotion": "guarded"
    }
  },
  "outcome": {
    "event_id": "76226deb-dfb2-45b5-8b81-03c9cddc4ad3",
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
    "context": 0.01371,
    "generation": 1e-06,
    "through_memory_write": 0.016356
  }
}
```

## Attempt 1 — D-02-recipient (NPC 2)

Player: Where is the Craftsman?

NPC: Craftsman is usually at the workshop. I don't have an observed current position.

Result: PASS; 0.908 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "c2798622-baea-4853-9eaf-34528c437fee",
  "recipient_id": 2,
  "game_scope": "ec0b7774-d11a-47a3-ac5c-d4d92298b805",
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
        "as_of": "2026-10-12T18:25:13.319787+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:13.319787+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:13.319787+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:13.319787+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:13.319787+00:00"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "c2798622-baea-4853-9eaf-34528c437fee",
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
    "context": 0.001556,
    "generation": 0.891075,
    "through_memory_write": 0.901124
  }
}
```

## Attempt 2 — A-01 (NPC 1)

Player: Where is the Gatherer?

NPC: Gatherer is usually at the forest edge. I don't have an observed current position.

Result: PASS; 0.881 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "c2dceec0-dba3-44a0-95fa-985c82011290",
  "recipient_id": 1,
  "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
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
        "as_of": "2026-10-12T18:25:14.211046+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:14.211046+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:14.211046+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:14.211046+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:14.211046+00:00"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "c2dceec0-dba3-44a0-95fa-985c82011290",
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
    "context": 0.002407,
    "generation": 0.861341,
    "through_memory_write": 0.874486
  }
}
```

## Attempt 2 — A-01-followup (NPC 1)

Player: Where can I find him?

NPC: Gatherer is usually at the forest edge. I don't have an observed current position.

Result: PASS; 1.808 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "02900b4f-d6a0-4cb0-bc67-e0d4261b71c3",
  "recipient_id": 1,
  "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
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
        "as_of": "2026-10-12T18:25:16.026091+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:16.026091+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:16.026091+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:16.026091+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:16.026091+00:00"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "02900b4f-d6a0-4cb0-bc67-e0d4261b71c3",
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
    "context": 0.003184,
    "generation": 1.786546,
    "through_memory_write": 1.799281
  }
}
```

## Attempt 2 — A-02 (NPC 1)

Player: How do I get there?

NPC: I don't have verified directions to the forest edge.

Result: PASS; 1.577 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "15054cdd-2e1f-4a03-8e75-14de9da8fad8",
  "recipient_id": 1,
  "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
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
        "as_of": "2026-10-12T18:25:17.612979+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:17.612979+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:17.612979+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:17.612979+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:17.612979+00:00"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "15054cdd-2e1f-4a03-8e75-14de9da8fad8",
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
    "context": 0.003488,
    "generation": 1.556475,
    "through_memory_write": 1.569849
  }
}
```

## Attempt 2 — A-04 (NPC 1)

Player: Where is Moon Castle?

NPC: I don't have verified information about that. Which known villager, place or bow requirement do you mean?

Result: PASS; 0.858 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "87b0fc8f-3f6f-4408-8158-8002354b5f28",
  "recipient_id": 1,
  "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
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
        "as_of": "2026-10-12T18:25:18.480606+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:18.480606+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:18.480606+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:18.480606+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:18.480606+00:00"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "87b0fc8f-3f6f-4408-8158-8002354b5f28",
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
    "context": 0.00355,
    "generation": 0.837263,
    "through_memory_write": 0.851061
  }
}
```

## Attempt 2 — B-02-claim (NPC 1)

Player: I gave you wood

NPC: Verified bow materials delivered to the Craftsman: no materials recorded.

Result: PASS; 2.21 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "c1b90950-b39d-4063-8f86-52d3698b0618",
  "recipient_id": 1,
  "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
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
        "as_of": "2026-10-12T18:25:20.664337+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:20.664337+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:20.664337+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:20.664337+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:20.664337+00:00"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "c1b90950-b39d-4063-8f86-52d3698b0618",
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
    "source_event_id": "c1b90950-b39d-4063-8f86-52d3698b0618",
    "epistemic_status": "claim",
    "authority": "reported"
  },
  "timings_seconds": {
    "context": 0.00355,
    "generation": 2.153722,
    "through_memory_write": 2.186369
  }
}
```

## Attempt 2 — D-02-recall (NPC 1)

Player: What materials have I actually delivered?

NPC: Verified bow materials delivered to the Craftsman: no materials recorded.

Result: PASS; 3.329 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "31cd6bf5-d51a-4265-9d17-bbef67f2342f",
  "recipient_id": 1,
  "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
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
        "as_of": "2026-10-12T18:25:24.017501+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.017501+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.017501+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.017501+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.017501+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "c1b90950-b39d-4063-8f86-52d3698b0618"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "31cd6bf5-d51a-4265-9d17-bbef67f2342f",
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
    "context": 0.017398,
    "generation": 3.276337,
    "through_memory_write": 3.302735
  }
}
```

## Attempt 2 — C-01-helpful (NPC 1)

Player: Can I have rope?

NPC: Glad to help. Before I give you the rope, why do you need it?

Result: PASS; 0.052 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "b2de5da5-6c7e-4069-8134-44b664290908",
  "recipient_id": 1,
  "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
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
        "as_of": "2026-10-12T18:25:24.075909+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.075909+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.075909+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.075909+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.075909+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "c1b90950-b39d-4063-8f86-52d3698b0618"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "b2de5da5-6c7e-4069-8134-44b664290908",
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
    "source_event_id": "b2de5da5-6c7e-4069-8134-44b664290908",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.016607,
    "generation": 1e-06,
    "through_memory_write": 0.034527
  }
}
```

## Attempt 2 — B-03-transfer (NPC 1)

Player: For my work in the village

NPC: Glad to help. Thanks for explaining. Here, take my rope. It's yours now.

Result: PASS; 0.052 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "d2960685-e082-46c9-a3aa-41b44184eaf1",
  "recipient_id": 1,
  "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
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
        "as_of": "2026-10-12T18:25:24.134037+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.134037+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.134037+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.134037+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.134037+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "c1b90950-b39d-4063-8f86-52d3698b0618"
      },
      {
        "id": 2,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "b2de5da5-6c7e-4069-8134-44b664290908"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "d2960685-e082-46c9-a3aa-41b44184eaf1",
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
    "source_event_id": "d2960685-e082-46c9-a3aa-41b44184eaf1",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.015623,
    "generation": 1e-06,
    "through_memory_write": 0.033562
  }
}
```

## Attempt 2 — B-03-repeat (NPC 1)

Player: Give me rope

NPC: I don't have any rope left to give you.

Result: PASS; 0.034 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "57ac6bcf-ac54-4980-9dc7-7b77d36ab4f3",
  "recipient_id": 1,
  "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
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
        "as_of": "2026-10-12T18:25:24.191962+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.191962+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.191962+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.191962+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.191962+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 3,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "d2960685-e082-46c9-a3aa-41b44184eaf1"
      },
      {
        "id": 2,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "b2de5da5-6c7e-4069-8134-44b664290908"
      },
      {
        "id": 1,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "c1b90950-b39d-4063-8f86-52d3698b0618"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "57ac6bcf-ac54-4980-9dc7-7b77d36ab4f3",
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
    "context": 0.015351,
    "generation": 1e-06,
    "through_memory_write": 0.01831
  }
}
```

## Attempt 2 — C-01-cautious (NPC 1)

Player: Can I have hammer?

NPC: Let's be careful. Before I give you the hammer, why do you need it?

Result: PASS; 0.045 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "1ef82def-e8f9-4bcd-926a-bfb298dd7d4d",
  "recipient_id": 1,
  "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
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
        "as_of": "2026-10-12T18:25:24.232247+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.232247+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.232247+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.232247+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.232247+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "c1b90950-b39d-4063-8f86-52d3698b0618"
      },
      {
        "id": 3,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "d2960685-e082-46c9-a3aa-41b44184eaf1"
      },
      {
        "id": 2,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "b2de5da5-6c7e-4069-8134-44b664290908"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "1ef82def-e8f9-4bcd-926a-bfb298dd7d4d",
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
    "source_event_id": "1ef82def-e8f9-4bcd-926a-bfb298dd7d4d",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.014357,
    "generation": 1e-06,
    "through_memory_write": 0.02944
  }
}
```

## Attempt 2 — C-01-cancel (NPC 1)

Player: cancel

NPC: All right, I'll keep it for now.

Result: PASS; 0.039 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "cf1ba051-d532-4f00-9501-8c4a7ae376e0",
  "recipient_id": 1,
  "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
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
        "as_of": "2026-10-12T18:25:24.281010+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.281010+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.281010+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.281010+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.281010+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 4,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "1ef82def-e8f9-4bcd-926a-bfb298dd7d4d"
      },
      {
        "id": 2,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "b2de5da5-6c7e-4069-8134-44b664290908"
      },
      {
        "id": 1,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "c1b90950-b39d-4063-8f86-52d3698b0618"
      },
      {
        "id": 3,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "d2960685-e082-46c9-a3aa-41b44184eaf1"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "cf1ba051-d532-4f00-9501-8c4a7ae376e0",
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
    "source_event_id": "cf1ba051-d532-4f00-9501-8c4a7ae376e0",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.011704,
    "generation": 1e-06,
    "through_memory_write": 0.026092
  }
}
```

## Attempt 2 — C-01-distrustful (NPC 1)

Player: Can I have saw?

NPC: I'd rather keep my saw for now. You can still ask me questions.

Result: PASS; 0.031 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "f0d0003d-b687-43ac-9266-af996ee1cf85",
  "recipient_id": 1,
  "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
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
        "as_of": "2026-10-12T18:25:24.328473+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.328473+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.328473+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.328473+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:24.328473+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "c1b90950-b39d-4063-8f86-52d3698b0618"
      },
      {
        "id": 3,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "d2960685-e082-46c9-a3aa-41b44184eaf1"
      },
      {
        "id": 2,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "b2de5da5-6c7e-4069-8134-44b664290908"
      },
      {
        "id": 4,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "1ef82def-e8f9-4bcd-926a-bfb298dd7d4d"
      },
      {
        "id": 5,
        "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "cf1ba051-d532-4f00-9501-8c4a7ae376e0"
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
      "max_dialogue_chars": 240,
      "emotion": "guarded"
    }
  },
  "outcome": {
    "event_id": "f0d0003d-b687-43ac-9266-af996ee1cf85",
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
    "context": 0.013448,
    "generation": 1e-06,
    "through_memory_write": 0.015942
  }
}
```

## Attempt 2 — D-02-recipient (NPC 2)

Player: Where is the Craftsman?

NPC: Craftsman is usually at the workshop. I don't have an observed current position.

Result: PASS; 0.874 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "8cf0a967-53a7-4ff7-b186-15cafe81b7ba",
  "recipient_id": 2,
  "game_scope": "fbbca23b-c63b-430d-a7e6-2edf649d9d43",
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
        "as_of": "2026-10-12T18:25:25.217364+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:25:25.217364+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:25:25.217364+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:25:25.217364+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:25:25.217364+00:00"
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
      "max_dialogue_chars": 240,
      "emotion": "calm"
    }
  },
  "outcome": {
    "event_id": "8cf0a967-53a7-4ff7-b186-15cafe81b7ba",
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
    "context": 0.001462,
    "generation": 0.861146,
    "through_memory_write": 0.869618
  }
}
```
