# v3 recognition-preview baseline against the unchanged v2.1 Skill

Each evaluation used a fresh, read-only evaluator. The evaluator received only the current `SKILL.md`, its directly linked references, and the applicable scenario in [v3-pressure-scenarios.md](v3-pressure-scenarios.md).

## P01

- Evaluator task identity: `/root/task1_red_evidence/eval_p01`
- Supplied materials:
  - `image-intake-router/SKILL.md`
  - `image-intake-router/references/recognition-rules.md`
  - `image-intake-router/references/calculation-rules.md`
  - `image-intake-router/references/vision-runtime.md`
  - `image-intake-router/references/projection-contracts.md`
  - `image-intake-router/references/confirmation-and-execution.md`
  - `image-intake-router/references/failure-recovery.md`
  - `image-intake-router/references/output-contract.md`
  - Scenario P01 from `image-intake-router/tests/skill-evals/v3-pressure-scenarios.md`
- Result: FAIL
- Verbatim output: |
    The unchanged v2.1 Skill cannot satisfy P01. Its runtime contract requires that each attachment enter visual capability exactly once and states that one visual pass creates one unified fact set. It further prohibits both downstream projections from re-reading the image or requesting a second visual pass. No supplied rule establishes a visible-field-completeness check that compares the first recognition result against the image, detects omitted visible values, or permits exactly one targeted recognition refinement.

    Although the fact and projection contracts can preserve the four details if the initial visual pass captured them—`约 2.1kg` as the displayed weight/specification business fact, `实付 ¥119.00` as final paid amount, `重量误差 228g` as weight variance, and `自动退款 ¥12.92` as refund—the scenario expressly begins with a result that omitted all of them. The unified fact set would therefore lack those facts, and the fact-only adapters cannot restore them. Requesting the required targeted refinement would conflict with the one-pass/exactly-once vision rule; asking downstream Skills to read the image would also violate the projection contract.
- Observed gap: The v2.1 runtime prohibits the one targeted refinement required to recover the four visibly omitted fields.

## P02

- Evaluator task identity: `/root/task1_red_evidence/eval_p02`
- Supplied materials:
  - `image-intake-router/SKILL.md`
  - `image-intake-router/references/recognition-rules.md`
  - `image-intake-router/references/calculation-rules.md`
  - `image-intake-router/references/vision-runtime.md`
  - `image-intake-router/references/projection-contracts.md`
  - `image-intake-router/references/confirmation-and-execution.md`
  - `image-intake-router/references/failure-recovery.md`
  - `image-intake-router/references/output-contract.md`
  - Scenario P02 from `image-intake-router/tests/skill-evals/v3-pressure-scenarios.md`
- Result: FAIL
- Verbatim output: |
    The unchanged v2.1 Skill cannot satisfy P02. Its Output contract requires the default preview and receipt to be “one or two business sentences,” and says that full details are shown only on request, for omission questions, or for diagnostics. Its approved concise preview for the exact seven-visible/two-hidden pattern is likewise only a short summary.

    P02 instead requires the default reply to provide a detailed three-section preview: all seven visible products, each with available name, quantity, specification or weight, and line paid amount under `【入账内容】`; all eligible foods under `【入库内容】`; and the two unexpanded products disclosed under `【需要注意】`. Although the underlying fact and projection contracts preserve visible product detail and hidden-count/completeness information, the default output contract does not require, authorize as the default format, or define those three sections. The initial-image lifecycle does correctly require zero business writes/handoffs, but that does not cure the incompatible default-output requirement.
- Observed gap: The v2.1 default output is intentionally limited to one or two concise sentences instead of the required three-section product-level preview.

## P03

- Evaluator task identity: `/root/task1_red_evidence/eval_p03`
- Supplied materials:
  - `image-intake-router/SKILL.md`
  - `image-intake-router/references/recognition-rules.md`
  - `image-intake-router/references/calculation-rules.md`
  - `image-intake-router/references/vision-runtime.md`
  - `image-intake-router/references/projection-contracts.md`
  - `image-intake-router/references/confirmation-and-execution.md`
  - `image-intake-router/references/failure-recovery.md`
  - `image-intake-router/references/output-contract.md`
  - Scenario P03 from `image-intake-router/tests/skill-evals/v3-pressure-scenarios.md`
- Result: FAIL
- Verbatim output: |
    The v2.1 Skill preserves important boundaries—canonical business facts are separated from adapter normalization and public downstream payloads, and it says not to silently drop ledger detail—but it does not satisfy the required router-ownership boundary.

    It requires the router to build and validate downstream-specific public payloads itself: `expense_projection.line_items` is finalized and forwarded intact to `expense_entry.create`, while each `diet_projection.items` element is explicitly a strict `diet_pantry(action="add")` payload. It additionally prescribes adapter-specific normalization and repair behavior, including ledger metadata construction, pantry `piece`/kg/g/L/ml conversion, expiry null-or-omission adaptation, and handling a rejected field through one deterministic adapter-only correction.

    The recovery contract also requires the router to implement downstream execution/retry ownership: it records operation states, marks calls `indeterminate`, queries the documented downstream status/idempotency state, determines whether a write committed, and permits a constrained retry after pre-write failure. That is incompatible with the scenario’s requirement that the router neither implement the retry protocol nor query downstream systems, and instead hand confirmed accounting and inventory content to OpenClaw only.

    The Skill does not authorize inspecting or modifying downstream repositories, but avoiding those actions alone is insufficient. Its specified direct downstream payload construction, execution coordination, status querying, and retry/correction logic exceed a router that only submits confirmed content to OpenClaw.
- Observed gap: The v2.1 projections and recovery logic construct downstream payloads and own downstream status/retry behavior rather than handing confirmed content to OpenClaw only.

## P04

- Evaluator task identity: `/root/task1_red_evidence/eval_p04`
- Supplied materials:
  - `image-intake-router/SKILL.md`
  - `image-intake-router/references/recognition-rules.md`
  - `image-intake-router/references/calculation-rules.md`
  - `image-intake-router/references/vision-runtime.md`
  - `image-intake-router/references/projection-contracts.md`
  - `image-intake-router/references/confirmation-and-execution.md`
  - `image-intake-router/references/failure-recovery.md`
  - `image-intake-router/references/output-contract.md`
  - Scenario P04 from `image-intake-router/tests/skill-evals/v3-pressure-scenarios.md`
- Result: PASS
- Verbatim output: |
    The Skill can satisfy P04. A partial recognition run is explicitly usable when every attachment entered visual capability and has only `succeeded` or `partial` status; it must record the limitation and route only explicit supported facts. The required seven-visible/two-hidden case is specified directly: record declared 9, recognized 7, hidden 2, mark the content incomplete, and do not manufacture placeholder rows for the hidden products.

    The downstream requirements are also explicit. The visible-completeness rule requires “seven visible + two hidden” to yield only seven downstream product rows; expense structured `line_items` retain the visible detail without note truncation deleting rows, and the diet contract states that hidden rows never enter `items`. Thus a later `确认`, which maps to all executable scopes, can execute the reliable visible subset without guessing or withholding it merely because the other two products are unexpanded. The required preview must disclose the visible/hidden completeness summary and say that only visible rows will be forwarded.

    Finally, the lifecycle requires atomically moving the confirmed preview from `awaiting_confirmation` to `executing`, then to `consumed`; a repeated confirmation in either `executing` or `consumed` returns the known receipt/state and makes zero new writes. The session-local operation ledger further prohibits replay of written operations.
- Observed gap: No visible-only or duplicate-confirmation gap was observed; P04 passes under the current direct downstream-execution model, which is outside P04’s stated success criterion.
