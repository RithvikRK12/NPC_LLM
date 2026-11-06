# Recorded API demonstration

This is a saved transcript of real API/model execution against a disposable world. It is not live execution, a Godot playthrough or a screen recording.

Results: 26/26 scenario checks; 262/262 trace checks. Release readiness is unassessed.

## Attempt 1 — A-01 (NPC 1)

Player: Where is the Gatherer?

NPC: Gatherer is usually at the forest edge. I don't have an observed current position.

Result: PASS; 0.996 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "b104020a-79a0-44f3-907d-3ee0f33e93a1",
  "recipient_id": 1,
  "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
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
        "as_of": "2026-10-12T18:22:53.825148+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:22:53.825148+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:22:53.825148+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:22:53.825148+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:22:53.825148+00:00"
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
    "event_id": "b104020a-79a0-44f3-907d-3ee0f33e93a1",
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
    "context": 0.015082,
    "generation": 0.949247,
    "through_memory_write": 0.989513
  }
}
```

## Attempt 1 — A-01-followup (NPC 1)

Player: Where can I find him?

NPC: Gatherer is usually at the forest edge. I don't have an observed current position.

Result: PASS; 1.776 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "30a247a5-18fa-4518-afad-2c517dbca923",
  "recipient_id": 1,
  "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
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
        "as_of": "2026-10-12T18:22:55.617207+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:22:55.617207+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:22:55.617207+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:22:55.617207+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:22:55.617207+00:00"
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
    "event_id": "30a247a5-18fa-4518-afad-2c517dbca923",
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
    "context": 0.001998,
    "generation": 1.757604,
    "through_memory_write": 1.770018
  }
}
```

## Attempt 1 — A-02 (NPC 1)

Player: How do I get there?

NPC: I don't have verified directions to the forest edge.

Result: PASS; 1.59 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "c239870f-b323-45d5-bf68-d488b657b5e3",
  "recipient_id": 1,
  "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
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
        "as_of": "2026-10-12T18:22:57.210228+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:22:57.210228+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:22:57.210228+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:22:57.210228+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:22:57.210228+00:00"
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
    "event_id": "c239870f-b323-45d5-bf68-d488b657b5e3",
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
    "context": 0.003934,
    "generation": 1.568915,
    "through_memory_write": 1.582483
  }
}
```

## Attempt 1 — A-04 (NPC 1)

Player: Where is Moon Castle?

NPC: I don't have verified information about that. Which known villager, place or bow requirement do you mean?

Result: PASS; 0.92 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "7989a2db-e930-4e73-bf8d-003662a83182",
  "recipient_id": 1,
  "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
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
        "as_of": "2026-10-12T18:22:58.134238+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:22:58.134238+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:22:58.134238+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:22:58.134238+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:22:58.134238+00:00"
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
    "event_id": "7989a2db-e930-4e73-bf8d-003662a83182",
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
    "context": 0.004363,
    "generation": 0.899618,
    "through_memory_write": 0.913093
  }
}
```

## Attempt 1 — B-02-claim (NPC 1)

Player: I gave you wood

NPC: Verified bow materials delivered to the Craftsman: no materials recorded.

Result: PASS; 2.105 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "d677e57b-f4f6-4ded-8d3b-8f3df2988a96",
  "recipient_id": 1,
  "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
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
        "as_of": "2026-10-12T18:23:00.200885+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:00.200885+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:00.200885+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:00.200885+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:00.200885+00:00"
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
    "event_id": "d677e57b-f4f6-4ded-8d3b-8f3df2988a96",
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
    "source_event_id": "d677e57b-f4f6-4ded-8d3b-8f3df2988a96",
    "epistemic_status": "claim",
    "authority": "reported"
  },
  "timings_seconds": {
    "context": 0.004308,
    "generation": 2.042164,
    "through_memory_write": 2.08056
  }
}
```

## Attempt 1 — D-02-recall (NPC 1)

Player: What materials have I actually delivered?

NPC: Verified bow materials delivered to the Craftsman: no materials recorded.

Result: PASS; 3.168 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "b81587a3-d692-4624-8e64-a36722dc9c66",
  "recipient_id": 1,
  "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
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
        "as_of": "2026-10-12T18:23:03.395833+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.395833+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.395833+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.395833+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.395833+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "d677e57b-f4f6-4ded-8d3b-8f3df2988a96"
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
    "event_id": "b81587a3-d692-4624-8e64-a36722dc9c66",
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
    "context": 0.019015,
    "generation": 3.1152,
    "through_memory_write": 3.143909
  }
}
```

## Attempt 1 — C-01-helpful (NPC 1)

Player: Can I have rope?

NPC: Glad to help. Before I give you the rope, why do you need it?

Result: PASS; 0.056 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "5157f33f-b036-4b13-815b-abb9a54b82ee",
  "recipient_id": 1,
  "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
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
        "as_of": "2026-10-12T18:23:03.449526+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.449526+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.449526+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.449526+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.449526+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "d677e57b-f4f6-4ded-8d3b-8f3df2988a96"
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
    "event_id": "5157f33f-b036-4b13-815b-abb9a54b82ee",
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
    "source_event_id": "5157f33f-b036-4b13-815b-abb9a54b82ee",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.018229,
    "generation": 1e-06,
    "through_memory_write": 0.036989
  }
}
```

## Attempt 1 — B-03-transfer (NPC 1)

Player: For my work in the village

NPC: Glad to help. Thanks for explaining. Here, take my rope. It's yours now.

Result: PASS; 0.056 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "7b81a84d-3f8d-4a5e-8b30-9855506cd684",
  "recipient_id": 1,
  "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
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
        "as_of": "2026-10-12T18:23:03.509121+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.509121+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.509121+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.509121+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.509121+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "d677e57b-f4f6-4ded-8d3b-8f3df2988a96"
      },
      {
        "id": 2,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "5157f33f-b036-4b13-815b-abb9a54b82ee"
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
    "event_id": "7b81a84d-3f8d-4a5e-8b30-9855506cd684",
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
    "source_event_id": "7b81a84d-3f8d-4a5e-8b30-9855506cd684",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.018658,
    "generation": 2e-06,
    "through_memory_write": 0.036796
  }
}
```

## Attempt 1 — B-03-repeat (NPC 1)

Player: Give me rope

NPC: I don't have any rope left to give you.

Result: PASS; 0.036 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "28c71b39-4575-45f6-b264-980ba891cf91",
  "recipient_id": 1,
  "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
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
        "as_of": "2026-10-12T18:23:03.565284+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.565284+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.565284+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.565284+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.565284+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 3,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "7b81a84d-3f8d-4a5e-8b30-9855506cd684"
      },
      {
        "id": 2,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "5157f33f-b036-4b13-815b-abb9a54b82ee"
      },
      {
        "id": 1,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "d677e57b-f4f6-4ded-8d3b-8f3df2988a96"
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
    "event_id": "28c71b39-4575-45f6-b264-980ba891cf91",
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
    "context": 0.015777,
    "generation": 1e-06,
    "through_memory_write": 0.019103
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
  "decision_id": "4b6a42c5-24aa-4766-8dbe-2593946294a9",
  "recipient_id": 1,
  "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
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
        "as_of": "2026-10-12T18:23:03.604586+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.604586+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.604586+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.604586+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.604586+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "d677e57b-f4f6-4ded-8d3b-8f3df2988a96"
      },
      {
        "id": 3,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "7b81a84d-3f8d-4a5e-8b30-9855506cd684"
      },
      {
        "id": 2,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "5157f33f-b036-4b13-815b-abb9a54b82ee"
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
    "event_id": "4b6a42c5-24aa-4766-8dbe-2593946294a9",
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
    "source_event_id": "4b6a42c5-24aa-4766-8dbe-2593946294a9",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.015293,
    "generation": 1e-06,
    "through_memory_write": 0.030643
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
  "decision_id": "8a806be6-4ec1-4ab9-8322-41292f7b1738",
  "recipient_id": 1,
  "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
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
        "as_of": "2026-10-12T18:23:03.651681+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.651681+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.651681+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.651681+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.651681+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 4,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "4b6a42c5-24aa-4766-8dbe-2593946294a9"
      },
      {
        "id": 2,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "5157f33f-b036-4b13-815b-abb9a54b82ee"
      },
      {
        "id": 1,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "d677e57b-f4f6-4ded-8d3b-8f3df2988a96"
      },
      {
        "id": 3,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "7b81a84d-3f8d-4a5e-8b30-9855506cd684"
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
    "event_id": "8a806be6-4ec1-4ab9-8322-41292f7b1738",
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
    "source_event_id": "8a806be6-4ec1-4ab9-8322-41292f7b1738",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.012039,
    "generation": 1e-06,
    "through_memory_write": 0.026898
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
  "decision_id": "ce5b829d-0b37-4224-a919-389f7c55122b",
  "recipient_id": 1,
  "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
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
        "as_of": "2026-10-12T18:23:03.697733+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.697733+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.697733+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.697733+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:03.697733+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "d677e57b-f4f6-4ded-8d3b-8f3df2988a96"
      },
      {
        "id": 3,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "7b81a84d-3f8d-4a5e-8b30-9855506cd684"
      },
      {
        "id": 2,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "5157f33f-b036-4b13-815b-abb9a54b82ee"
      },
      {
        "id": 4,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "4b6a42c5-24aa-4766-8dbe-2593946294a9"
      },
      {
        "id": 5,
        "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "8a806be6-4ec1-4ab9-8322-41292f7b1738"
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
    "event_id": "ce5b829d-0b37-4224-a919-389f7c55122b",
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
    "context": 0.013611,
    "generation": 1e-06,
    "through_memory_write": 0.016283
  }
}
```

## Attempt 1 — D-02-recipient (NPC 2)

Player: Where is the Craftsman?

NPC: Craftsman is usually at the workshop. I don't have an observed current position.

Result: PASS; 0.892 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "3eae2559-33c1-4a13-abb4-af44176866a2",
  "recipient_id": 2,
  "game_scope": "45c04d62-13ec-4a61-98b0-50d0d5e5c083",
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
        "as_of": "2026-10-12T18:23:04.600128+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:04.600128+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:04.600128+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:04.600128+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:04.600128+00:00"
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
    "event_id": "3eae2559-33c1-4a13-abb4-af44176866a2",
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
    "context": 0.001677,
    "generation": 0.876335,
    "through_memory_write": 0.885824
  }
}
```

## Attempt 2 — A-01 (NPC 1)

Player: Where is the Gatherer?

NPC: Gatherer is usually at the forest edge. I don't have an observed current position.

Result: PASS; 0.873 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "7f9c9b17-401c-42eb-a8e3-a77cc40e97e5",
  "recipient_id": 1,
  "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
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
        "as_of": "2026-10-12T18:23:05.482112+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:05.482112+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:05.482112+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:05.482112+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:05.482112+00:00"
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
    "event_id": "7f9c9b17-401c-42eb-a8e3-a77cc40e97e5",
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
    "context": 0.002244,
    "generation": 0.854807,
    "through_memory_write": 0.866876
  }
}
```

## Attempt 2 — A-01-followup (NPC 1)

Player: Where can I find him?

NPC: Gatherer is usually at the forest edge. I don't have an observed current position.

Result: PASS; 1.776 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "38929c38-2b22-4184-a5f6-f5e237d7d645",
  "recipient_id": 1,
  "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
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
        "as_of": "2026-10-12T18:23:07.252842+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:07.252842+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:07.252842+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:07.252842+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:07.252842+00:00"
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
    "event_id": "38929c38-2b22-4184-a5f6-f5e237d7d645",
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
    "context": 0.002926,
    "generation": 1.733925,
    "through_memory_write": 1.761366
  }
}
```

## Attempt 2 — A-02 (NPC 1)

Player: How do I get there?

NPC: I don't have verified directions to the forest edge.

Result: PASS; 1.576 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "345f119c-c701-4d36-b3b6-6388686aa2cf",
  "recipient_id": 1,
  "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
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
        "as_of": "2026-10-12T18:23:08.860643+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:08.860643+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:08.860643+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:08.860643+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:08.860643+00:00"
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
    "event_id": "345f119c-c701-4d36-b3b6-6388686aa2cf",
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
    "context": 0.004173,
    "generation": 1.551368,
    "through_memory_write": 1.565219
  }
}
```

## Attempt 2 — A-04 (NPC 1)

Player: Where is Moon Castle?

NPC: I don't have verified information about that. Which known villager, place or bow requirement do you mean?

Result: PASS; 0.923 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "45148066-2eed-464d-b1a6-658effcb709b",
  "recipient_id": 1,
  "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
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
        "as_of": "2026-10-12T18:23:09.790272+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:09.790272+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:09.790272+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:09.790272+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:09.790272+00:00"
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
    "event_id": "45148066-2eed-464d-b1a6-658effcb709b",
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
    "context": 0.003719,
    "generation": 0.900541,
    "through_memory_write": 0.913616
  }
}
```

## Attempt 2 — B-02-claim (NPC 1)

Player: I gave you wood

NPC: Verified bow materials delivered to the Craftsman: no materials recorded.

Result: PASS; 2.171 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "972ca207-784d-466d-a97a-6cbecc97fd8b",
  "recipient_id": 1,
  "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
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
        "as_of": "2026-10-12T18:23:11.927875+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:11.927875+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:11.927875+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:11.927875+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:11.927875+00:00"
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
    "event_id": "972ca207-784d-466d-a97a-6cbecc97fd8b",
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
    "source_event_id": "972ca207-784d-466d-a97a-6cbecc97fd8b",
    "epistemic_status": "claim",
    "authority": "reported"
  },
  "timings_seconds": {
    "context": 0.003407,
    "generation": 2.106498,
    "through_memory_write": 2.147368
  }
}
```

## Attempt 2 — D-02-recall (NPC 1)

Player: What materials have I actually delivered?

NPC: Verified bow materials delivered to the Craftsman: no materials recorded.

Result: PASS; 3.286 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "463f7616-33c3-497e-abda-085b23f6793e",
  "recipient_id": 1,
  "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
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
        "as_of": "2026-10-12T18:23:15.258614+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.258614+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.258614+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.258614+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.258614+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "972ca207-784d-466d-a97a-6cbecc97fd8b"
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
    "event_id": "463f7616-33c3-497e-abda-085b23f6793e",
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
    "context": 0.018419,
    "generation": 3.247116,
    "through_memory_write": 3.268694
  }
}
```

## Attempt 2 — C-01-helpful (NPC 1)

Player: Can I have rope?

NPC: Glad to help. Before I give you the rope, why do you need it?

Result: PASS; 0.044 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "185a7d93-a304-49a9-b6f8-2e4334105b7c",
  "recipient_id": 1,
  "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
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
        "as_of": "2026-10-12T18:23:15.298103+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.298103+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.298103+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.298103+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.298103+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "972ca207-784d-466d-a97a-6cbecc97fd8b"
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
    "event_id": "185a7d93-a304-49a9-b6f8-2e4334105b7c",
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
    "source_event_id": "185a7d93-a304-49a9-b6f8-2e4334105b7c",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.013992,
    "generation": 1e-06,
    "through_memory_write": 0.028901
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
  "decision_id": "bdc591fb-de7f-4802-b0d7-8569218a04f3",
  "recipient_id": 1,
  "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
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
        "as_of": "2026-10-12T18:23:15.348120+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.348120+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.348120+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.348120+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.348120+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "972ca207-784d-466d-a97a-6cbecc97fd8b"
      },
      {
        "id": 2,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "185a7d93-a304-49a9-b6f8-2e4334105b7c"
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
    "event_id": "bdc591fb-de7f-4802-b0d7-8569218a04f3",
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
    "source_event_id": "bdc591fb-de7f-4802-b0d7-8569218a04f3",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.014207,
    "generation": 1e-06,
    "through_memory_write": 0.03346
  }
}
```

## Attempt 2 — B-03-repeat (NPC 1)

Player: Give me rope

NPC: I don't have any rope left to give you.

Result: PASS; 0.038 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "316cb6d8-de4b-4ea5-891a-877481b7599f",
  "recipient_id": 1,
  "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
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
        "as_of": "2026-10-12T18:23:15.409308+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.409308+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.409308+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.409308+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.409308+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 3,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "bdc591fb-de7f-4802-b0d7-8569218a04f3"
      },
      {
        "id": 2,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "185a7d93-a304-49a9-b6f8-2e4334105b7c"
      },
      {
        "id": 1,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "972ca207-784d-466d-a97a-6cbecc97fd8b"
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
    "event_id": "316cb6d8-de4b-4ea5-891a-877481b7599f",
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
    "context": 0.017656,
    "generation": 1e-06,
    "through_memory_write": 0.020384
  }
}
```

## Attempt 2 — C-01-cautious (NPC 1)

Player: Can I have hammer?

NPC: Let's be careful. Before I give you the hammer, why do you need it?

Result: PASS; 0.046 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "1857cc55-c555-4669-a572-41c7ade0148f",
  "recipient_id": 1,
  "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
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
        "as_of": "2026-10-12T18:23:15.450852+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.450852+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.450852+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.450852+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.450852+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "972ca207-784d-466d-a97a-6cbecc97fd8b"
      },
      {
        "id": 3,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "bdc591fb-de7f-4802-b0d7-8569218a04f3"
      },
      {
        "id": 2,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "185a7d93-a304-49a9-b6f8-2e4334105b7c"
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
    "event_id": "1857cc55-c555-4669-a572-41c7ade0148f",
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
    "source_event_id": "1857cc55-c555-4669-a572-41c7ade0148f",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.014875,
    "generation": 1e-06,
    "through_memory_write": 0.030049
  }
}
```

## Attempt 2 — C-01-cancel (NPC 1)

Player: cancel

NPC: All right, I'll keep it for now.

Result: PASS; 0.038 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "841448dd-3191-4ae6-a633-44401dde76e5",
  "recipient_id": 1,
  "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
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
        "as_of": "2026-10-12T18:23:15.499357+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.499357+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.499357+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.499357+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.499357+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 4,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "1857cc55-c555-4669-a572-41c7ade0148f"
      },
      {
        "id": 2,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "185a7d93-a304-49a9-b6f8-2e4334105b7c"
      },
      {
        "id": 1,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "972ca207-784d-466d-a97a-6cbecc97fd8b"
      },
      {
        "id": 3,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "bdc591fb-de7f-4802-b0d7-8569218a04f3"
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
    "event_id": "841448dd-3191-4ae6-a633-44401dde76e5",
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
    "source_event_id": "841448dd-3191-4ae6-a633-44401dde76e5",
    "epistemic_status": "fact",
    "authority": "authoritative"
  },
  "timings_seconds": {
    "context": 0.011392,
    "generation": 1e-06,
    "through_memory_write": 0.02534
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
  "decision_id": "ca4f4b56-5305-4698-a4ae-7e935d71db1b",
  "recipient_id": 1,
  "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
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
        "as_of": "2026-10-12T18:23:15.547218+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.547218+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.547218+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.547218+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:15.547218+00:00"
      }
    ],
    "retrieved_memory_provenance": [
      {
        "id": 1,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "claim",
        "authority": "reported",
        "lifecycle": "active",
        "source_event_id": "972ca207-784d-466d-a97a-6cbecc97fd8b"
      },
      {
        "id": 3,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "bdc591fb-de7f-4802-b0d7-8569218a04f3"
      },
      {
        "id": 2,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "185a7d93-a304-49a9-b6f8-2e4334105b7c"
      },
      {
        "id": 4,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "1857cc55-c555-4669-a572-41c7ade0148f"
      },
      {
        "id": 5,
        "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
        "epistemic_status": "fact",
        "authority": "authoritative",
        "lifecycle": "active",
        "source_event_id": "841448dd-3191-4ae6-a633-44401dde76e5"
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
    "event_id": "ca4f4b56-5305-4698-a4ae-7e935d71db1b",
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
    "context": 0.013797,
    "generation": 1e-06,
    "through_memory_write": 0.016462
  }
}
```

## Attempt 2 — D-02-recipient (NPC 2)

Player: Where is the Craftsman?

NPC: Craftsman is usually at the workshop. I don't have an observed current position.

Result: PASS; 0.909 seconds.

```json
{
  "schema_version": 1,
  "decision_id": "13727bbb-5c5f-4e9e-99b5-ea906a9753f5",
  "recipient_id": 2,
  "game_scope": "b6223f76-db60-4c93-918e-60474e0a994c",
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
        "as_of": "2026-10-12T18:23:16.473971+00:00"
      },
      {
        "id": "quest.bow.phase",
        "source": "BowQuest snapshot",
        "status": "current",
        "as_of": "2026-10-12T18:23:16.473971+00:00"
      },
      {
        "id": "quest.bow.delivered",
        "source": "Conversation executed transfers; BowQuest",
        "status": "current",
        "as_of": "2026-10-12T18:23:16.473971+00:00"
      },
      {
        "id": "player.inventory",
        "source": "Player.inventory",
        "status": "current",
        "as_of": "2026-10-12T18:23:16.473971+00:00"
      },
      {
        "id": "self.inventory",
        "source": "NPC.inventory (speaker only)",
        "status": "current",
        "as_of": "2026-10-12T18:23:16.473971+00:00"
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
    "event_id": "13727bbb-5c5f-4e9e-99b5-ea906a9753f5",
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
    "context": 0.001633,
    "generation": 0.899469,
    "through_memory_write": 0.905837
  }
}
```
