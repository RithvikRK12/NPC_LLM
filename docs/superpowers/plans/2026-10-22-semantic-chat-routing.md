# Context-aware Local LLM Chat Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route every player chat turn from one strict, versioned interpretation produced by the configured local model while preserving authoritative server validation and output grounding.

**Architecture:** Add a semantic contract and interpreter call that receives the current player message plus bounded chronological context, current state, facts and capabilities. Attach the accepted result to the turn context; route supported concerns from it, render facts and operations on the server, and pass the same result to speech generation, validation and one bounded repair. Provider/schema failure degrades explicitly and never invokes phrase routing.

**Tech Stack:** Python 3.12, Pydantic, FastAPI, SQLAlchemy, OpenAI-compatible local Ollama endpoint, unittest.

**Spec:** `docs/superpowers/specs/2026-10-22-semantic-chat-routing-design.md`

## Global Constraints

- Keep the selected local Llama model and local inference; no hosted inference or replacement model.
- Never use either personal `mvp.db` for tests; use disposable databases.
- Keep deterministic ownership, role, consent, current-state, supported-operation, CAS and transaction checks.
- Permit at most one mutation per message and never repeat a committed action during repair.
- Preserve unrelated uncommitted `Play.command` and `README.md` edits.
- No database migration or frontend wire change absent demonstrated need.
- Keep provider failures explicit without keyword-router fallback.

## Review Focus

- Pending purpose plus interruption: verify the unrelated concern leaves the pending request untouched and a later purpose answer binds to it.
- Bare assent: verify it binds only to the compatible current question and never supplies missing item purpose.
- Quoted, hypothetical and negated operation wording: verify no operation is proposed or executed.
- Mixed social/factual/operation messages: verify all supported concerns survive and final facts/outcomes remain authoritative.
- Model/schema outage: verify explicit degradation, zero mutations, and no phrase router fallback.

---

### Task 1: Versioned Interpretation Contract and Provider Interface

**Files:**
- Create: `backend/app/services/semantic_routing.py`
- Modify: `backend/app/services/llm/service.py`
- Modify: `backend/app/services/llm/openai_compatible.py`
- Test: `backend/tests/test_semantic_routing.py`

**Interfaces:** `InterpretationContext` carries message, ordered history, pending question/item, focus, encounter, facts and capabilities. `AcceptedInterpretation` contains strict version `1`, ordered concerns, clarification and validation. `LLMService.interpret(...)` performs one timed provider call and parses the strict contract.

- [x] Test accepted strict schema, span/reference/capability validation, modality and malformed/provider failure.
- [x] Run the focused unittest module and confirm expected failures.
- [x] Implement contract, bounded interpretation prompt, and schema-constrained local provider call.
- [x] Verify focused contract tests pass.

### Task 2: Pipeline Context Propagation and Semantic Routing

**Files:**
- Modify: `backend/app/services/context/models.py`
- Modify: `backend/app/services/context/builder.py`
- Modify: `backend/app/services/pipeline.py`
- Modify: `backend/app/services/prompts/builder.py`
- Modify: `backend/app/services/validation/service.py`
- Test: `backend/tests/test_semantic_routing.py`
- Test: `backend/tests/test_grounded_chat.py`

**Interfaces:** Pipeline interprets every accepted turn outside write locks, stores the validated result on `ConversationContext`, and uses it for route selection, prompt and validation. Chronological recent accepted turns remain available without social phrase filtering.

- [x] Add mocked integration tests for social continuation, factual answer, mixed concern, and explicit provider failure.
- [x] Replace phrase decisions in active prompt, decode, history, validation, and fallback paths with accepted concerns.
- [x] Verify focused integration tests pass and no mocked interpretation can authorize state changes by itself.

### Task 3: Operation and Encounter Adapters

**Files:**
- Modify: `backend/app/services/pipeline.py`
- Modify: `backend/app/services/validation/items.py`
- Modify: `backend/app/services/craftsman_intent.py`
- Modify: `backend/app/services/craftsman.py`
- Test: `backend/tests/test_semantic_routing.py`
- Test: `backend/tests/test_grounded_chat.py`

**Interfaces:** Item and Craftsman adapters consume typed concerns and exact targets directly; they do not synthesize sentences for legacy regex parsing. Existing deterministic state, ownership, role, consent and encounter guards remain authoritative.

- [x] Test direct purpose transfer, cancellation, pending-purpose handling, interruption/resumption and non-direct quoted operations.
- [x] Route only supported direct requests and compatible pending answers through the existing guarded execution paths.
- [x] Verify focused tests for cancellation/interruption and that the adapter performs at most one item operation.

### Task 4: Grounded Mixed Replies, Repair, and Failure Behavior

**Files:**
- Modify: `backend/app/services/pipeline.py`
- Modify: `backend/app/services/validation/service.py`
- Modify: `backend/app/services/decision_trace.py`
- Test: `backend/tests/test_semantic_routing.py`
- Test: `backend/tests/test_grounded_chat.py`

- [x] Test mixed social/factual concern retention, grounding rejection, bounded interpretation correction, and quoted-operation nonexecution.
- [x] Preserve server-rendered factual/outcome segments and validate the complete published response.
- [x] Record routing version, accepted interpretation, failure reason, call counts, interpretation and end-to-end latency without chain-of-thought.

### Task 5: Held-out Local Model Evaluation and Documentation

**Files:**
- Create: `backend/tests/fixtures/semantic-routing-heldout-v1.json`
- Create: `backend/tests/run_semantic_routing_live.py`
- Create: `docs/evidence/semantic-chat-routing/README.md`
- Modify: `backend/tests/test_semantic_routing.py`

- [x] Freeze held-out expected decisions for both NPCs, multi-turn context, indirect requests, yes/no, interruptions, mixed concerns, negation, quotation, hypothetical and unsupported requests.
- [x] Add disposable-DB HTTP evaluation with before/after mutation audit and latency/call metrics.
- [x] Run focused tests and the live local-model evaluation.
- [x] Report denominators, baseline distinctions, limitations and exact restart/run commands; state that the model quality gates were missed.
- [ ] Complete the full repository suite with the new interpreter stubbed in legacy tests; current offline run is confounded by localhost model access attempts, while the escalated run was interrupted because of slow real-model calls.

