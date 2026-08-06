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

- Evaluator task identity: `/root/task1_red_evidence/eval_p04_fix1`
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
- Result: FAIL
- Verbatim output: |
    P04 is not fully satisfied. The v2.1 materials do require the correct partial-content behavior: a seven-visible/two-hidden order is recorded as declared 9, recognized/visible 7, hidden 2, with incomplete detail; no hidden-product placeholder rows are manufactured; hidden rows never enter the pantry payload; and the “Visible completeness” rule says that only seven product rows proceed downstream. The preview must retain the completeness warning and say only visible rows were forwarded, so the reliable seven are not blocked merely because two are unexpanded.

    They also require confirmation idempotency for direct execution. A later `确认` confirms the latest business digest, the preview moves atomically through `executing` to `consumed`, and a repeated confirmation of either state returns the known safe receipt/state with zero new writes. Thus the contract prevents a second direct expense/pantry execution.

    However, P04 expressly defines “handoff” as returning the confirmed accounting and inventory content to OpenClaw for orchestration, and v2.1 does not specify such a return handoff. Instead, it explicitly requires direct downstream execution: the finalized ledger-public projection is “forwarded intact to `expense_entry.create`”; diet `items` are final strict `diet_pantry(action="add")` payloads; and “Independent execution” says to execute the selected expense scope and each eligible pantry item independently with public payloads. The receipt reports downstream committed outcomes. Direct router calls to those adapters are not the stipulated return of confirmed content to OpenClaw for orchestration.

    Therefore, although visible-only routing and repeat-confirmation idempotency are covered, the scenario’s essential “router hands off” requirement is unmet, so the unchanged v2.1 materials fail P04.
- Observed gap: The v2.1 router directly executes expense and pantry adapters after confirmation instead of handing the seven reliable accounting and inventory products back to OpenClaw for orchestration.
