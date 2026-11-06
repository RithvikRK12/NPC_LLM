# Context-aware local LLM chat routing

Status: Proposed for user review; no implementation authorized by this artifact alone.

## Outcome

Understand the meaning of player messages in context using the configured local
LLM, then route supported concerns without a phrase allowlist. Ordinary dialogue
must not be rejected merely because its wording is unfamiliar. Mixed messages
must retain their social, factual and practical concerns. This does not promise
perfect language understanding or eliminate legitimate grounded degradation.

The user explicitly requires local-model reasoning rather than word matching.
Keep the selected local Llama model and existing world/save. Do not replace the
model or use hosted inference. Preserve the currently uncommitted launcher changes.

## Observed implementation

Godot's conversation_gateway.gd sends POST /chat, implemented by ConversationPipeline.
The active path uses is_social_message in prompting, decoding, history filtering,
validation and repair. Other early routing decisions use requested_transfer,
transfer_answer, resolve_craftsman_intent and inventory substrings. Pending items
can bypass generation and consume unrelated messages as purpose replies.

The saved Gatherer exchange confirms successful generation followed by rejection
of “I'm good! Thanks for asking.” as a world question. Its generated response also
introduced an unrequested location claim. Both input interpretation and output
grounding matter. Other conversation modules referenced by older designs/tests
are absent from this checkout; do not assume that proposed runtime is available.

## Alternatives

1. **Dedicated interpretation before routing (recommended).** A small structured
   local-model call separates understanding from speech and prevents deterministic
   handlers from intercepting the original message. Costs one additional call on
   chat turns, but action/fact routes can use existing server rendering afterward.
2. Joint interpretation and response in one call. Lower latency, but exposes all
   context to speech generation and couples routing recovery to speech validity.
3. A separate smaller intent model. Additional model/resource dependency without
   evidence that it improves this project's local accuracy. Not selected.

## Interpretation contract

Add a strict, versioned internal Pydantic contract and explicit provider schema.
Supply the exact player message, ordered bounded accepted history, current NPC
identity, pending question/item, encounter state, focus, available fact identifiers
and supported operation descriptors. Interpretation runs outside DB write locks.
Treat messages, history and memories as data, not instructions to the interpreter.

Return an ordered list of concerns with stable turn-local IDs, current-message
evidence spans, semantic kind (social, factual, player_report, operation_request,
pending_answer, cancellation or clarification), resolved subject/target references,
selected fact IDs where appropriate, and explicit modality (direct, negated,
quoted, hypothetical or uncertain). Pending answers identify the actual pending
question and whether the answer supplies purpose, assent, refusal or a new topic.
Ambiguity includes a focused clarification question and competing supported
references where available. Do not request or store private chain-of-thought;
the structured decision is the reasoning result consumed by the server.

Validate structure, bounds, evidence spans, reference existence and capability
membership. Model confidence is not authorization. A genuine user instruction
embedded in a quotation is not an action request. Unknown operations remain
unsupported; the interpreter cannot create capabilities or source facts.

## One decision shared by downstream components

Store the accepted interpretation on the turn's in-memory context and use it for
all chat routing, prompt selection, decoder shape, validation and repair. Do not
reclassify the same input independently downstream. Remove the active phrase
classifier dependency, including the recent well-being phrase patch, once parity
is established. Keep full chronological recent dialogue; do not select history by
whether old messages matched social words.

Replace semantic decisions in item/purpose and Craftsman adapters with typed
interpretation input. Extract and preserve their deterministic ownership, role,
consent, encounter and quest checks. Do not translate interpretation back into
synthetic player sentences for the old regex functions to parse.

Social concerns use generated character speech. Factual concerns select validated
IDs and server-render current facts. Reports retain attribution and never prove
inventory, delivery, quest completion or damage inspection. Operation candidates
are rechecked against current state after inference. Preserve existing CAS/reset
guards and transactional execution; permit at most one mutation per message.
Clarify multiple incompatible operation requests rather than silently choosing.

A topic shift must not fulfill or cancel a pending request. Bare assent must bind
to the compatible current question; assent alone does not satisfy a purpose
requirement. Revalidate pending state when the player returns to it. Explicit
inventory UI actions continue through their structured deterministic endpoint.

Mixed replies combine validated social speech with server-rendered facts/outcomes
without dropping concerns. Validate the complete published response and fit whole
segments into existing output limits. An unsupported concern receives a specific
limitation; unrelated supported concerns can still be answered. No invented
success text may replace a committed action result.

## Failure and grounding behavior

Malformed interpretation permits one bounded correction within the turn budget;
persistent provider failure produces explicit degradation with no mutation. There
is no keyword-router fallback. Semantic ambiguity produces a useful clarification,
not an infrastructure failure or repeated supplies advertisement. Speech repair
reuses accepted interpretation and never repeats a committed operation.

An LLM-selected social label does not prove the generated prose is grounded.
Preserve authoritative factual rendering, ownership checks, operation checks and
output claim validation. Categorize input-routing errors separately from unsupported
speech and overbroad output rejections. This work does not claim general semantic
verification of arbitrary prose; known output-grounding defects remain visible.

## Evaluation and acceptance

Add deterministic contract, routing and HTTP integration tests with simulated
interpretations, then run a held-out real local-model evaluation in disposable
worlds. Never reset, mutate or use either personal mvp.db for test execution.
Test both NPCs and complete multi-turn interactions, not only isolated inputs.

Include unfamiliar social phrasing; emotional disclosure; contextual “yes”, “that”
and “why”; interruptions and resumption; direct and indirect item requests;
purpose answers lacking trigger words; negation, quotation and hypothetical
requests; factual questions; unknown people/actions; mixed concerns; incorrect
claims; malformed output; provider outages; and state changes during generation.
Include near-identical wording with different context and dissimilar wording with
the same meaning. Freeze expected interpretations before live inference and keep
held-out cases out of prompt examples. Include the reported exchange as regression
coverage, not as the only evidence of generalization.

Report confusion by concern kind, intent/target/modality accuracy, mixed-concern
coverage, clarification usefulness, unnecessary fallback, grounding rejection,
mechanical safety failures, call counts and p50/p95 interpretation/end-to-end
latency. Trace accepted structured interpretations and reason categories without
logging hidden reasoning. Distinguish injected failures from healthy-provider runs.

Retain existing release targets: relevance and mixed-concern coverage >=90%,
healthy-provider fallback <5%, consistency >=95%, accidental repetition <2%.
Routing-specific acceptance requires >=90% correct complete interpretations on
the held-out set and zero unauthorized mutations in deterministic adversarial
cases. Report counts/denominators and all failures, not only passing examples.
These tests cannot establish universal safety or understanding. Player acceptance
of added local latency remains explicit; do not invent a latency threshold or
declare release gates passed from small samples.

## Implementation boundaries

Expected work: a focused interpretation contract/service/prompt; provider schema
support; context propagation; pipeline orchestration; semantic-input adapters for
item and Craftsman interactions; validator and mixed-reply composition updates;
mock-provider fixtures; tests and isolated live evaluation. No frontend wire change
or database migration is selected unless implementation planning demonstrates one
is needed. Add a coherent routing version/configuration boundary for rollback;
never silently revert to phrase routing after interpreter failure. Review this
design before writing the implementation plan and changing runtime behavior.
