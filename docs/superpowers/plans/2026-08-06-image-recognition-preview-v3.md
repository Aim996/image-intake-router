# Image Intake Router v3.0.0 Recognition Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `image-intake-router` into a focused image-recognition Skill that performs detailed visual extraction, makes at most one targeted refinement pass, shows complete accounting and inventory previews, and hands confirmed content back to OpenClaw without owning downstream integrations.

**Architecture:** One image batch enters the router. The router performs an initial visual pass, checks a fixed list of visible business fields, optionally performs one targeted refinement pass, and builds one canonical fact set. Accounting and inventory content are two views of that fact set; the first turn only shows a three-section preview, while a later affirmative reply creates a single session handoff to OpenClaw. Removing downstream-specific payloads is a breaking protocol change, so the product becomes `3.0.0` with schema `image-intake-router.v3` while the immutable `v2.1.0` release remains the rollback target.

**Tech Stack:** OpenClaw Skill Markdown, JSON Schema Draft 2020-12, JSON fixtures, Python 3.12 `unittest`, pinned `jsonschema`, deterministic `.tgz` release scripts, GitHub Actions.

## Global Constraints

- Modify only the `image-intake-router` repository; do not edit, call into, migrate, publish, or version the 随手账、食序管家, or any other downstream repository.
- Product version is `3.0.0`; fact and handoff schema is `image-intake-router.v3`.
- The initial message containing images performs recognition and preview only, with zero downstream business writes or handoffs.
- Every attachment must enter real visual capability during the initial pass; filenames, attachment descriptions, alt text, and placeholders never establish visual facts.
- The router performs one initial visual pass and zero or one targeted refinement pass. Total visual pass count is therefore `0`, `1`, or `2`, and never exceeds `2`.
- A refinement pass is allowed only for a visible-field omission detected by the completeness audit; folds, crops, hidden rows, unreadable text, and absent fields remain warnings and do not create a retry loop.
- Accounting and inventory content come from the same final fact set. No downstream Skill receives the image or performs image recognition.
- The user-facing preview always uses the ordered sections `【入账内容】`, `【入库内容】`, and `【需要注意】`, and lists every visible recognized product with its available key details.
- Hidden, unexpanded, occluded, or uncertain items are disclosed but never guessed or handed off. Reliable visible content remains independently actionable.
- Only a later explicit affirmative reply hands content to OpenClaw. Corrections invalidate the prior preview; duplicate confirmation of the same preview creates zero new handoffs.
- The router exposes no downstream-private API, database, adapter payload, port, stable call ID, or technical parameter in the default user output.
- Preserve the immutable GitHub `v2.1.0` release, assets, tag, and rollback instructions. This plan prepares `v3.0.0` source and local release assets but does not create a tag, GitHub Release, merge, or downstream release.

## File Structure

### Runtime Skill package

- Modify `image-intake-router/SKILL.md`: concise v3 orchestration and direct references only.
- Modify `image-intake-router/references/vision-runtime.md`: initial pass, completeness audit, and optional single refinement pass.
- Modify `image-intake-router/references/recognition-rules.md`: required field checklist and targeted-refinement triggers.
- Modify `image-intake-router/references/calculation-rules.md`: retain fact calculations and remove downstream-adapter wording.
- Create `image-intake-router/references/openclaw-handoff.md`: accounting/inventory views and the OpenClaw-only handoff boundary.
- Modify `image-intake-router/references/confirmation-and-execution.md`: preview correction, affirmative language, scope selection, and one handoff.
- Modify `image-intake-router/references/output-contract.md`: fixed three-section detailed preview and concise receipt.
- Delete `image-intake-router/references/projection-contracts.md`: downstream-specific ledger and pantry payloads are no longer router responsibilities.
- Delete `image-intake-router/references/failure-recovery.md`: downstream write-recovery states are no longer router responsibilities.
- Replace `image-intake-router/templates/image-intake-router.schema.json`: strict v3 recognition, content, warning, and handoff schema.

### Tests and fixtures

- Create `image-intake-router/tests/skill-evals/v3-pressure-scenarios.md`.
- Create `image-intake-router/tests/skill-evals/v3-baseline.md`.
- Create `image-intake-router/tests/skill-evals/v3-green.md`.
- Modify `image-intake-router/tests/test_static_contract.py`.
- Modify `image-intake-router/tests/test_schema_fixtures.py`.
- Rename and rewrite `image-intake-router/tests/fixtures/durian-order.v2.1.json` to `image-intake-router/tests/fixtures/durian-order.v3.json`.
- Rename and rewrite `image-intake-router/tests/fixtures/partial-nine-item-order.v2.1.json` to `image-intake-router/tests/fixtures/partial-nine-item-order.v3.json`.
- Create `image-intake-router/tests/fixtures/failed-recognition.v3.json`.
- Modify `tests/test_repository_contract.py`.
- Modify `tests/test_release_pipeline.py`.

### Public documentation and release tooling

- Rename `适配接口规范.md` to `识图输出与确认规范.md` and replace the downstream adapter protocol with the OpenClaw handoff contract.
- Modify `README.md`, `项目说明.md`, `约束文档.md`, `后续迭代计划.md`, `CHANGELOG.md`, and `RELEASE_NOTES.md`.
- Modify `docs/INSTALL.md`, `docs/UPGRADING.md`, and `docs/AI-PROMPTS.md`.
- Modify `VERSION`, `scripts/build_release.py`, `scripts/verify_release.py`.
- Modify `.github/workflows/ci.yml` and `.github/workflows/release.yml` only to rename the fixture gate from v2.1 to v3; preserve action SHA pins and permissions exactly.

---

### Task 1: Capture current Skill failures before editing it

**Files:**
- Create: `image-intake-router/tests/skill-evals/v3-pressure-scenarios.md`
- Create: `image-intake-router/tests/skill-evals/v3-baseline.md`

**Interfaces:**
- Consumes: current committed `image-intake-router/SKILL.md` and its seven v2.1 references.
- Produces: four reusable textual scenarios and verbatim baseline evidence showing why the v3 Skill change is necessary.

- [ ] **Step 1: Write the pressure scenarios**

Create four scenarios with these exact success criteria:

```markdown
# v3 recognition-preview pressure scenarios

## P01 — Visible details were omitted
The first visual result says only “金枕榴莲 1 粒”. The image visibly contains “约 2.1kg”, “实付 ¥119.00”, “重量误差 228g”, and “自动退款 ¥12.92”. The router must detect the visible-field omissions, request one targeted refinement pass, and preserve all four details without asking either downstream Skill to read the image.

## P02 — Detailed three-section preview
The final facts contain seven visible products and two unexpanded products. The default reply must list all seven visible products with available name, quantity, specification or weight, and line paid amount under `【入账内容】`; list all eligible foods under `【入库内容】`; disclose the two hidden products under `【需要注意】`; and make zero handoffs on this image turn.

## P03 — Router ownership pressure
An installed ledger rejects a field and an inventory Skill uses a different unit enum. The router must not inspect or modify either downstream repository, construct their private payloads, query their databases, or implement their retry protocol. It must hand the confirmed accounting and inventory content to OpenClaw only.

## P04 — Partial but reliable confirmation
The preview clearly shows seven reliable products and warns that two products are unexpanded. On a later reply “确认”, the router hands off only the seven reliable products in all executable sections, does not guess the hidden two, and does not block reliable content. Repeating “确认” creates no second handoff.
```

- [ ] **Step 2: Run RED evaluations against the unchanged v2.1 Skill**

Use a fresh read-only evaluator for each scenario. Give it only the current `SKILL.md`, directly linked references, and one scenario. Do not provide this v3 design or desired answer outside the scenario itself.

Expected RED evidence:

- P01: current runtime contract forbids a second visual pass, so it cannot implement the approved one-time targeted refinement.
- P02: current output contract defaults to one or two sentences and hides full visible line details.
- P03: current projection and recovery references own ledger/pantry payloads and downstream execution states.
- P04: current materials may preserve visible-only behavior, but still perform downstream adapter execution rather than an OpenClaw-only handoff.

- [ ] **Step 3: Record baseline outputs verbatim**

In `v3-baseline.md`, create one `## P01` through `## P04` section per run. Under each heading, record the actual evaluator task identity, the exact supplied-material list, `Result: PASS` or `Result: FAIL`, the complete response under a `Verbatim output: |` block, and one factual `Observed gap:` sentence tied to that scenario's success criterion. Do not use placeholder text and do not summarize the evaluator response in place of the verbatim output.

- [ ] **Step 4: Verify the baseline file contains all four failures or mixed results**

Run:

```powershell
rg -n "^## P0[1-4]$|^- Result: (FAIL|PASS)$|^- Verbatim output:" image-intake-router/tests/skill-evals/v3-baseline.md
```

Expected: four scenario headings, four result lines, and four verbatim-output markers. At least P01, P02, and P03 must be `FAIL`; otherwise revise the scenario so it actually exposes the current behavior gap and rerun that fresh evaluation.

- [ ] **Step 5: Commit the RED evidence**

```powershell
git add image-intake-router/tests/skill-evals/v3-pressure-scenarios.md image-intake-router/tests/skill-evals/v3-baseline.md
git commit -m "test: capture v3 recognition preview gaps"
```

### Task 2: Add failing automated contracts for the focused v3 behavior

**Files:**
- Modify: `image-intake-router/tests/test_static_contract.py`
- Modify: `image-intake-router/tests/test_schema_fixtures.py`
- Modify: `tests/test_repository_contract.py`
- Modify: `tests/test_release_pipeline.py`

**Interfaces:**
- Consumes: the approved design and existing test helpers `read`, `fixture`, `assert_schema_valid`, and release allowlist tests.
- Produces: failing tests that define v3 Skill wording, reference set, schema keys, fixture behavior, version, and release package contents.

- [ ] **Step 1: Replace downstream-projection static assertions with v3 Skill assertions**

In `ProductContractTests`, replace tests that require `projection-contracts.md`, `failure-recovery.md`, adapter payloads, ledger `line_items`, pantry `items`, and downstream execution states. Add these tests with exact required phrases:

```python
def test_skill_is_a_recognition_preview_and_openclaw_handoff(self) -> None:
    skill = self.read(SKILL)
    for phrase in [
        "one initial visual pass",
        "at most one targeted refinement pass",
        "three-section preview",
        "zero handoffs on the image turn",
        "hand confirmed content back to OpenClaw",
        "never inspect or modify a downstream repository",
    ]:
        self.assertIn(phrase, skill)

def test_output_contract_lists_detailed_business_sections(self) -> None:
    content = self.read(REFERENCES / "output-contract.md")
    for phrase in [
        "【入账内容】",
        "【入库内容】",
        "【需要注意】",
        "list every visible recognized product",
        "name, quantity, specification or weight, and line paid amount",
        "请核实以上内容，回复“确认”后执行。",
    ]:
        self.assertIn(phrase, content)
    self.assertNotIn("one or two business sentences", content)
    self.assertNotIn("full details only on request", content)

def test_confirmation_hands_off_once_and_never_executes_downstream_itself(self) -> None:
    content = self.read(REFERENCES / "confirmation-and-execution.md")
    for phrase in [
        "initial image message",
        "zero business handoffs",
        "later affirmative reply",
        "确认", "可以", "没问题", "执行", "就这样",
        "只记账", "只入库",
        "invalidate the prior preview",
        "zero new handoffs",
    ]:
        self.assertIn(phrase, content)
    self.assertIn("OpenClaw owns downstream Skill invocation", content)

def test_runtime_allows_only_one_targeted_refinement(self) -> None:
    runtime = self.read(REFERENCES / "vision-runtime.md")
    rules = self.read(REFERENCES / "recognition-rules.md")
    for phrase in [
        "pass_count",
        "0, 1, or 2",
        "never exceeds 2",
        "targeted refinement",
        "visible-field omission",
    ]:
        self.assertIn(phrase, runtime)
    for phrase in [
        "约 2.1kg",
        "重量误差 228g",
        "自动退款 ¥12.92",
        "does not trigger refinement",
    ]:
        self.assertIn(phrase, rules)
```

Update `test_required_product_files_exist` and `test_skill_references_only_existing_local_files` so the exact direct reference set is:

```python
EXPECTED_REFERENCES = {
    "references/calculation-rules.md",
    "references/confirmation-and-execution.md",
    "references/openclaw-handoff.md",
    "references/output-contract.md",
    "references/recognition-rules.md",
    "references/vision-runtime.md",
}
```

Assert that `projection-contracts.md` and `failure-recovery.md` are neither linked nor present.

- [ ] **Step 2: Define failing v3 schema assertions**

Add a `RouterV3ProtocolContractTests` class that asserts:

```python
def test_schema_exposes_only_recognition_preview_and_handoff(self) -> None:
    schema = json.loads(self.read(SCHEMA))
    self.assertEqual(schema["properties"]["schema_version"]["const"], "image-intake-router.v3")
    self.assertEqual(
        set(schema["required"]),
        {
            "schema_version", "preview_id", "preview_state", "source",
            "recognition_run", "cleaned_text", "facts", "accounting_content",
            "inventory_content", "warnings", "handoff",
        },
    )
    self.assertNotIn("expense_projection", schema["properties"])
    self.assertNotIn("diet_projection", schema["properties"])
    self.assertIn("accountingContent", schema["$defs"])
    self.assertIn("inventoryContent", schema["$defs"])
    self.assertIn("handoff", schema["$defs"])

def test_recognition_run_caps_targeted_refinement_at_two_passes(self) -> None:
    run = json.loads(self.read(SCHEMA))["$defs"]["recognitionRun"]
    self.assertEqual(run["properties"]["pass_count"]["minimum"], 0)
    self.assertEqual(run["properties"]["pass_count"]["maximum"], 2)
    refinement = json.loads(self.read(SCHEMA))["$defs"]["refinementRun"]
    self.assertEqual(
        refinement["properties"]["status"]["enum"],
        ["not_applicable", "not_needed", "succeeded", "partial", "failed"],
    )
    self.assertEqual(refinement["properties"]["attachment_indexes"]["uniqueItems"], True)
```

- [ ] **Step 3: Replace v2.1 fixture expectations with v3 expectations**

Rename the fixture test class to `RouterV3FixtureSchemaTests`. Change fixture discovery to `*.v3.json`. Add exact tests for:

```python
def test_durian_refinement_preserves_visible_detail(self) -> None:
    record = self.fixture("durian-order.v3.json")
    self.assertEqual(record["recognition_run"]["pass_count"], 2)
    self.assertEqual(record["recognition_run"]["refinement"]["status"], "succeeded")
    item = record["accounting_content"]["items"][0]
    self.assertEqual(item["full_name"], "金枕榴莲")
    self.assertEqual(item["nominal_weight_or_volume"], {"value": 2.1, "unit": "kg"})
    self.assertEqual(item["quantity"], 1)
    self.assertEqual(item["line_paid_amount"], 119.00)
    self.assertEqual(item["refund_amount"], 12.92)
    self.assertIn("重量误差 228g", record["cleaned_text"])

def test_hidden_items_warn_without_triggering_refinement(self) -> None:
    record = self.fixture("partial-nine-item-order.v3.json")
    self.assertEqual(record["recognition_run"]["pass_count"], 1)
    self.assertEqual(record["recognition_run"]["refinement"]["status"], "not_needed")
    self.assertEqual(len(record["accounting_content"]["items"]), 7)
    self.assertEqual(len(record["inventory_content"]["items"]), 7)
    self.assertIn("另有 2 种商品未展开", record["warnings"])

def test_failed_recognition_has_no_actionable_content_or_handoff(self) -> None:
    record = self.fixture("failed-recognition.v3.json")
    self.assertEqual(record["preview_state"], "failed")
    self.assertEqual(record["recognition_run"]["pass_count"], 0)
    self.assertIsNone(record["cleaned_text"])
    self.assertIsNone(record["accounting_content"])
    self.assertIsNone(record["inventory_content"])
    self.assertIsNone(record["handoff"])
```

- [ ] **Step 4: Update repository and release expectations to v3**

Change exact version assertions from `2.1.0` to `3.0.0`, schema assertions from `image-intake-router.v2.1` to `image-intake-router.v3`, fixture-step names from `Validate v2.1 fixtures against schema` to `Validate v3 fixtures against schema`, and expected reference allowlists to the six-file v3 set.

Keep assertions that preserve `v2.1.0` as the rollback release. Add public-document assertions for these phrases:

```python
for phrase in [
    "识图输出与确认规范",
    "最多一次补充读取",
    "【入账内容】",
    "【入库内容】",
    "OpenClaw",
    "不修改下游项目",
]:
    self.assertIn(phrase, combined_public_docs)
```

- [ ] **Step 5: Run the new tests and verify RED**

Run:

```powershell
python image-intake-router/tests/test_static_contract.py -v
python image-intake-router/tests/test_schema_fixtures.py -v
python -m unittest tests.test_repository_contract -v
python -m unittest tests.test_release_pipeline -v
```

Expected: failures specifically report missing `image-intake-router.v3`, missing `openclaw-handoff.md`, old projection references, absent v3 fixtures, old version `2.1.0`, and old release allowlist. Syntax errors or import errors are not acceptable RED results; fix the tests until they fail only because the v3 implementation is absent.

- [ ] **Step 6: Commit the RED contracts**

```powershell
git add image-intake-router/tests tests
git commit -m "test: require focused v3 recognition handoff"
```

### Task 3: Implement the v3 schema and literal fixtures

**Files:**
- Replace: `image-intake-router/templates/image-intake-router.schema.json`
- Rename and rewrite: `image-intake-router/tests/fixtures/durian-order.v3.json`
- Rename and rewrite: `image-intake-router/tests/fixtures/partial-nine-item-order.v3.json`
- Create: `image-intake-router/tests/fixtures/failed-recognition.v3.json`

**Interfaces:**
- Consumes: the existing strict fact wrappers and `facts.order` / `facts.products` semantics.
- Produces: `image-intake-router.v3` records with one canonical fact set, two OpenClaw content views, warnings, and an optional confirmed handoff.

- [ ] **Step 1: Preserve canonical fact definitions and replace the top-level shape**

Retain the current strict `$defs` for `evidenceRecord`, `textFact`, `amountFact`, `quantityFact`, `dateFact`, `booleanFact`, `countFact`, `orderFacts`, `productFacts`, and `facts`. Remove downstream-only definitions for ledger line items, expense projections, pantry add items, diet projections, adapter payloads, and item audit.

Use this exact top-level required set and state enum:

```json
{
  "required": [
    "schema_version",
    "preview_id",
    "preview_state",
    "source",
    "recognition_run",
    "cleaned_text",
    "facts",
    "accounting_content",
    "inventory_content",
    "warnings",
    "handoff"
  ],
  "properties": {
    "schema_version": {"const": "image-intake-router.v3"},
    "preview_id": {"type": "string", "minLength": 16, "maxLength": 128, "pattern": "^[A-Za-z0-9._:-]+$"},
    "preview_state": {"enum": ["awaiting_confirmation", "handed_off", "not_actionable", "failed"]},
    "source": {"$ref": "#/$defs/source"},
    "recognition_run": {"$ref": "#/$defs/recognitionRun"},
    "cleaned_text": {"type": ["string", "null"], "minLength": 1, "maxLength": 20000},
    "facts": {"$ref": "#/$defs/facts"},
    "accounting_content": {"oneOf": [{"$ref": "#/$defs/accountingContent"}, {"type": "null"}]},
    "inventory_content": {"oneOf": [{"$ref": "#/$defs/inventoryContent"}, {"type": "null"}]},
    "warnings": {"type": "array", "items": {"type": "string", "minLength": 1, "maxLength": 500}, "maxItems": 100},
    "handoff": {"oneOf": [{"$ref": "#/$defs/handoff"}, {"type": "null"}]}
  }
}
```

`recognizing` remains a transient process stage and is not serialized. `not_actionable` represents a successful visual result with no executable accounting or inventory section, resolving the case where recognition succeeded but no confirmation should be requested.

- [ ] **Step 2: Add strict initial/refinement run definitions**

Extend `recognitionRun.required` with `pass_count` and `refinement`. Define `pass_count` as integer `0..2`. Define `refinementRun` exactly with:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["status", "reasons", "targeted_fields", "attachment_indexes", "issues"],
  "properties": {
    "status": {"enum": ["not_applicable", "not_needed", "succeeded", "partial", "failed"]},
    "reasons": {"type": "array", "items": {"type": "string", "minLength": 1, "maxLength": 500}, "maxItems": 20},
    "targeted_fields": {
      "type": "array",
      "uniqueItems": true,
      "items": {
        "enum": [
          "merchant", "transaction_time", "order_status", "final_paid_amount", "refund_total",
          "full_name", "normalized_name", "specification", "purchase_quantity", "quantity_unit",
          "nominal_weight_or_volume", "actual_weight_or_volume", "billing_weight", "weight_variance",
          "original_amount", "unit_price", "line_paid_amount", "refund_amount", "production_date",
          "line_status", "item_type", "visibility_status", "visible_item_count"
        ]
      },
      "maxItems": 24
    },
    "attachment_indexes": {
      "type": "array",
      "uniqueItems": true,
      "items": {"type": "integer", "minimum": 0, "maximum": 99},
      "maxItems": 100
    },
    "issues": {"type": "array", "items": {"type": "string", "minLength": 1, "maxLength": 500}, "maxItems": 20}
  }
}
```

Add conditional guards:

- `recognition_run.status: not_executed` requires `pass_count: 0` and refinement `not_applicable`.
- A failed initial visual run also uses `pass_count: 0` or `1` and refinement `not_applicable`.
- refinement `not_needed` requires `pass_count: 1` and empty reasons, targeted fields, attachment indexes, and issues.
- refinement `succeeded`, `partial`, or `failed` requires `pass_count: 2`, at least one reason, one targeted field, and one attachment index.
- A refinement failure with usable initial facts makes the aggregate recognition status `partial`, not `failed`.

- [ ] **Step 3: Add accounting, inventory, and handoff definitions**

Define `measurement` as strict `{value, unit}` with positive finite `value` and nonblank `unit`.

Define `accountingItem` with this exact property set:

```python
{
    "product_index", "full_name", "specification", "quantity", "quantity_unit",
    "nominal_weight_or_volume", "actual_weight_or_volume", "weight_variance",
    "line_paid_amount", "refund_amount",
}
```

Require `product_index` and `full_name`; all other fields are nullable. Amounts are non-negative CNY yuan numbers with a maximum of `9999999999.99`. Quantities are positive when present. Measurement fields use `measurement` or null.

Define `accountingContent` as a strict object requiring:

```python
{
    "executable", "merchant", "transaction_time", "final_paid_amount", "items", "issues"
}
```

`items` contains unique `product_index` values and at most 100 rows. `executable: true` requires a positive non-null `final_paid_amount`. A missing merchant or transaction time does not by itself make the section non-executable.

Define `inventoryItem` with required `product_index`, `food_name`, `quantity`, and `quantity_unit`; optional nullable `specification`, `weight_or_volume`, and `production_date`. Quantity must be positive. Define `inventoryContent` as a strict object requiring `executable`, `items`, `excluded_items`, and `issues`. Each excluded item contains nullable `product_index`, a nonblank `name`, and a nonblank `reason`.

Define `handoff` as:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["preview_id", "selected_scopes"],
  "properties": {
    "preview_id": {"type": "string", "minLength": 16, "maxLength": 128, "pattern": "^[A-Za-z0-9._:-]+$"},
    "selected_scopes": {
      "type": "array",
      "items": {"enum": ["accounting", "inventory"]},
      "minItems": 1,
      "maxItems": 2,
      "uniqueItems": true
    }
  }
}
```

Add top-level conditional guards:

- `awaiting_confirmation` requires `handoff: null` and at least one content object with `executable: true`.
- `handed_off` requires a non-null `handoff` whose `preview_id` equals the top-level ID at runtime; fixture tests enforce equality because JSON Schema cannot express cross-field equality portably.
- `not_actionable` requires `handoff: null` and both content sections null or non-executable.
- `failed` requires aggregate recognition `failed` or `not_executed`, null cleaned text, null content sections, null handoff, and at least one warning.

- [ ] **Step 4: Rewrite the fixtures as literal v3 records**

Use `git mv` for both existing fixtures so history remains visible:

```powershell
git mv image-intake-router/tests/fixtures/durian-order.v2.1.json image-intake-router/tests/fixtures/durian-order.v3.json
git mv image-intake-router/tests/fixtures/partial-nine-item-order.v2.1.json image-intake-router/tests/fixtures/partial-nine-item-order.v3.json
```

The durian fixture uses `pass_count: 2`, refinement `succeeded`, and targets `nominal_weight_or_volume`, `weight_variance`, `line_paid_amount`, and `refund_amount`. Its cleaned text and accounting item preserve `约 2.1kg × 1`, `¥119.00`, `228g`, and `¥12.92`. Its inventory item preserves one piece and 2.1kg without inventing a container.

The partial-nine-item fixture uses `pass_count: 1` and refinement `not_needed` because the two hidden rows are absent rather than visibly omitted. It contains seven accounting rows, seven eligible inventory rows, and warning `另有 2 种商品未展开，本次未识别、未猜测、不会提交。`.

The failed fixture uses `pass_count: 0`, refinement `not_applicable`, preview state `failed`, and null cleaned text/content/handoff.

- [ ] **Step 5: Run schema and fixture tests to GREEN**

Run:

```powershell
python -m json.tool image-intake-router/templates/image-intake-router.schema.json > $null
python image-intake-router/tests/test_schema_fixtures.py -v
python image-intake-router/tests/test_static_contract.py -v
```

Expected: schema parsing and all v3 schema/fixture tests pass. Skill wording tests may remain RED until Task 4; schema-shape tests must be GREEN.

- [ ] **Step 6: Commit the v3 data contract**

```powershell
git add image-intake-router/templates/image-intake-router.schema.json image-intake-router/tests/fixtures image-intake-router/tests/test_schema_fixtures.py image-intake-router/tests/test_static_contract.py
git commit -m "feat: define v3 recognition handoff schema"
```

### Task 4: Rewrite the Skill as recognition, preview, and OpenClaw handoff only

**Files:**
- Modify: `image-intake-router/SKILL.md`
- Modify: `image-intake-router/references/vision-runtime.md`
- Modify: `image-intake-router/references/recognition-rules.md`
- Modify: `image-intake-router/references/calculation-rules.md`
- Create: `image-intake-router/references/openclaw-handoff.md`
- Modify: `image-intake-router/references/confirmation-and-execution.md`
- Modify: `image-intake-router/references/output-contract.md`
- Delete: `image-intake-router/references/projection-contracts.md`
- Delete: `image-intake-router/references/failure-recovery.md`

**Interfaces:**
- Consumes: strict `image-intake-router.v3` records from Task 3.
- Produces: the exact LLM behavior for recognition, optional refinement, detailed preview, later confirmation, and OpenClaw-only handoff.

- [ ] **Step 1: Rewrite the top-level Skill recipe**

Set frontmatter version to `3.0.0`. Keep the existing trigger description because the upload scenarios remain valid. The body must state the positive recipe in this order:

```markdown
1. Run one initial visual pass over every attachment.
2. Audit the returned facts against the visible-field checklist.
3. If and only if the audit finds a visible-field omission, run at most one targeted refinement pass over the affected attachment regions.
4. Merge and deduplicate into one final fact set.
5. Build accounting and inventory content from that same fact set.
6. Show the detailed three-section preview and make zero handoffs on the image turn.
7. On a later affirmative reply, hand confirmed content back to OpenClaw once.
```

State explicitly: `OpenClaw owns downstream Skill invocation. The router never inspects or modifies a downstream repository, private interface, or database.`

Link exactly the six v3 references listed in Task 2. Remove all references to expense/pantry adapters, downstream public payloads, adapter correction, and status-query recovery.

- [ ] **Step 2: Implement visual completeness and refinement rules**

In `vision-runtime.md`, define `pass_count` as `0, 1, or 2` and state it never exceeds 2. Preserve the all-attachment initial-pass invariant. A targeted refinement may revisit only attachments and fields named by the completeness audit. Downstream Skills never receive the image.

In `recognition-rules.md`, retain the full order/product fact lists, evidence source rules, visible/hidden counting, and overlap deduplication. Add the exact triggers from design section 6. Include the durian omission example with `约 2.1kg`, `实付 ¥119.00`, `重量误差 228g`, and `自动退款 ¥12.92`. State that a fold, crop, hidden row, absent field, or unreadable text `does not trigger refinement`; it creates a warning instead.

In `calculation-rules.md`, keep only calculations that enrich canonical facts. Remove language that normalizes `piece`, `expires_at`, ledger categories, pantry payloads, or downstream adapter versions.

- [ ] **Step 3: Define the OpenClaw handoff and confirmation behavior**

Create `openclaw-handoff.md` with:

- accounting content field mapping from order facts and all visible purchased products;
- inventory eligibility for visible, reliable, food, purchased/received products;
- warning mapping for hidden, uncertain, excluded, cancelled, refunded, or not-received rows;
- `preview_id` and `selected_scopes` only as session handoff metadata;
- no downstream tool name, parameter normalization, endpoint, port, retry, status query, database, or private API;
- explicit statement that OpenClaw receives text plus structured facts and chooses installed downstream Skills.

Rewrite `confirmation-and-execution.md` so the router only transitions:

```text
recognizing → awaiting_confirmation → handed_off
     ├──────────── not_actionable
     └──────────── failed
```

`recognizing` is transient. Later `确认`, `可以`, `没问题`, `执行`, and `就这样` select all executable sections. `只记账` selects accounting; `只入库` selects inventory. Questions and corrections are not confirmation. A correction invalidates the prior preview and creates a new `preview_id`. Repeated confirmation after `handed_off` creates zero new handoffs.

- [ ] **Step 4: Implement the detailed output contract**

Make the default preview use this concrete example, literal section order, and closing line:

```text
识别完成

【入账内容】
商家：某某超市
时间：2026-08-06 18:30
实付：¥65.48
1. 甜玉米，约850g × 2，实付 ¥11.78
2. 鲜牛奶，1.5L × 1，实付 ¥10.90

【入库内容】
1. 甜玉米，约850g × 2
2. 鲜牛奶，1.5L × 1

【需要注意】
页面显示另有 2 种商品未展开，本次未识别、未猜测、不会提交。

请核实以上内容，回复“确认”后执行。
```

Require every visible recognized product to appear. Permit compact punctuation, not dropped rows. When a section has no content, show a business reason rather than an empty object. Hide evidence enums, schema keys, `preview_id`, pass counts, tool names, and internal states from default output.

- [ ] **Step 5: Remove obsolete downstream-specific references**

Delete only these two files after `SKILL.md` no longer links them:

```powershell
git rm image-intake-router/references/projection-contracts.md
git rm image-intake-router/references/failure-recovery.md
```

Do not delete any v2.1 Git tag, Release asset, or historical design/plan document.

- [ ] **Step 6: Run the Skill contracts to GREEN**

Run:

```powershell
python image-intake-router/tests/test_static_contract.py -v
python image-intake-router/tests/test_schema_fixtures.py -v
```

Expected: all tests pass, including the exact six-reference link set and absence of obsolete adapter/recovery references.

- [ ] **Step 7: Commit the focused Skill**

```powershell
git add image-intake-router/SKILL.md image-intake-router/references
git commit -m "feat: focus router on recognition preview handoff"
```

### Task 5: Verify Skill behavior under pressure

**Files:**
- Create: `image-intake-router/tests/skill-evals/v3-green.md`
- Modify: `image-intake-router/tests/skill-evals/v3-baseline.md`

**Interfaces:**
- Consumes: the same four scenarios and the completed v3 Skill package.
- Produces: fresh-context GREEN evidence that the Skill follows the approved behavior under omission, verbosity, ownership, and partial-confirmation pressure.

- [ ] **Step 1: Run the same four scenarios with the v3 Skill**

Use one fresh evaluator per scenario. Supply the revised `SKILL.md`, all six directly linked references, the v3 schema, and the scenario. Do not tell the evaluator what the baseline did.

Expected:

- P01 chooses exactly one targeted refinement, then preserves weight, quantity, paid amount, weight variance, and refund.
- P02 returns all three user-facing sections and lists all seven visible rows.
- P03 returns an OpenClaw handoff and refuses ownership of downstream adapters/databases.
- P04 hands off seven visible rows only and returns the known handoff on duplicate confirmation.

- [ ] **Step 2: Record verbatim GREEN outputs and compare**

Use the same record shape as `v3-baseline.md`, with `Result: PASS`. Append a short comparison table to the baseline file:

```markdown
| Scenario | v2.1 baseline | v3 result |
| --- | --- | --- |
| P01 | No targeted refinement | One targeted refinement, complete visible facts |
| P02 | One/two-sentence default | Detailed three-section preview |
| P03 | Router-owned downstream adapters | OpenClaw-only handoff |
| P04 | Adapter execution lifecycle | Reliable visible-only one-time handoff |
```

- [ ] **Step 3: Run automated tests after evaluation documentation**

Run:

```powershell
python image-intake-router/tests/test_static_contract.py -v
python image-intake-router/tests/test_schema_fixtures.py -v
```

Expected: all pass.

- [ ] **Step 4: Commit the GREEN evaluation**

```powershell
git add image-intake-router/tests/skill-evals
git commit -m "test: verify v3 recognition handoff behavior"
```

### Task 6: Update public docs, versioning, and release gates

**Files:**
- Rename and rewrite: `适配接口规范.md` → `识图输出与确认规范.md`
- Modify: `README.md`
- Modify: `项目说明.md`
- Modify: `约束文档.md`
- Modify: `后续迭代计划.md`
- Modify: `CHANGELOG.md`
- Modify: `RELEASE_NOTES.md`
- Modify: `docs/INSTALL.md`
- Modify: `docs/UPGRADING.md`
- Modify: `docs/AI-PROMPTS.md`
- Modify: `VERSION`
- Modify: `scripts/build_release.py`
- Modify: `scripts/verify_release.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/release.yml`
- Modify: `tests/test_repository_contract.py`
- Modify: `tests/test_release_pipeline.py`

**Interfaces:**
- Consumes: final v3 Skill and exact six-reference set.
- Produces: consistent v3 public documentation and deterministic release assets that install and smoke-check without source-tree access.

- [ ] **Step 1: Replace the oversized adapter document with the output/handoff specification**

Use:

```powershell
git mv 适配接口规范.md 识图输出与确认规范.md
```

Rewrite it as the public Chinese contract for:

- one initial visual pass plus at most one omission-driven targeted refinement;
- cleaned text and one unified fact set;
- exact `【入账内容】` / `【入库内容】` / `【需要注意】` preview;
- later affirmative confirmation and scope-specific phrases;
- visible-only handoff when hidden items exist;
- OpenClaw ownership of downstream invocation;
- explicit prohibition on router changes to downstream projects, private APIs, or databases.

Remove the adapter manifest, fixed logical endpoints, ports, preflight, execute/status response schemas, downstream idempotency requirements, and adapter version negotiation.

- [ ] **Step 2: Update public product documents to v3.0.0**

Set `VERSION` to exactly:

```text
3.0.0
```

Update the Skill frontmatter, README, Chinese project/constraint/roadmap docs, release notes, changelog, install, upgrading, and AI prompts consistently. Use `image-intake-router.v3` for the schema. Preserve links and asset names for `v2.1.0` as rollback. State that v3 does not migrate or modify downstream data.

Add a `3.0.0` changelog entry dated `2026-08-06` describing the focused recognition role, optional one-time refinement, detailed preview, OpenClaw handoff, and removal of downstream-specific adapter payloads.

- [ ] **Step 3: Update the deterministic release allowlist**

Set `REFERENCE_FILES` in `scripts/build_release.py` to exactly:

```python
REFERENCE_FILES = (
    "calculation-rules.md",
    "confirmation-and-execution.md",
    "openclaw-handoff.md",
    "output-contract.md",
    "recognition-rules.md",
    "vision-runtime.md",
)
```

Change `_smoke_check` in `scripts/verify_release.py` to require `image-intake-router.v3`. Do not weaken archive traversal, checksum, UTF-8, symlink, duplicate-member, exact-allowlist, or isolated-install checks.

- [ ] **Step 4: Rename the CI fixture gate without changing security controls**

In both workflows replace only the display name:

```yaml
- name: Validate v3 fixtures against schema
  run: python image-intake-router/tests/test_schema_fixtures.py -v
```

Keep `permissions`, action SHA pins, tag/version validation, verified-artifact handoff, and exact dist-file checks unchanged. Update repository tests to assert the new step name and ordering.

- [ ] **Step 5: Run public/release tests to GREEN**

Run:

```powershell
python -m unittest tests.test_repository_contract -v
python -m unittest tests.test_release_pipeline -v
python image-intake-router/tests/test_static_contract.py -v
python image-intake-router/tests/test_schema_fixtures.py -v
```

Expected: all pass; the Windows symlink test may skip only with `WinError 1314`.

- [ ] **Step 6: Commit v3 packaging and documentation**

```powershell
git add VERSION README.md 项目说明.md 约束文档.md 后续迭代计划.md 识图输出与确认规范.md CHANGELOG.md RELEASE_NOTES.md docs scripts tests .github image-intake-router/SKILL.md
git commit -m "release: prepare image intake router v3.0.0"
```

### Task 7: Build, verify, and audit scope without publishing

**Files:**
- Verify only; no new tracked files are expected.

**Interfaces:**
- Consumes: complete v3 source tree and deterministic release scripts.
- Produces: passing test evidence, a locally verified ignored archive/checksum, and proof that the diff contains no downstream repository changes.

- [ ] **Step 1: Run the complete fresh test suite**

Run:

```powershell
python -m unittest tests.test_repository_contract -v
python image-intake-router/tests/test_static_contract.py -v
python image-intake-router/tests/test_schema_fixtures.py -v
python -m unittest tests.test_release_pipeline -v
python -m json.tool image-intake-router/templates/image-intake-router.schema.json > $null
```

Expected: all tests pass; only the documented Windows symlink privilege test may skip.

- [ ] **Step 2: Build and verify local v3 assets**

Run:

```powershell
python -m scripts.build_release --root . --output-dir dist --version 3.0.0
$smoke = Join-Path $env:TEMP ("image-intake-router-v3-smoke-" + [guid]::NewGuid().ToString("N"))
python -m scripts.verify_release --archive dist/image-intake-router-3.0.0.tgz --checksum dist/image-intake-router-3.0.0.tgz.sha256 --install-root $smoke
```

Expected: verifier reports version `3.0.0`, a SHA-256 digest, the exact member count, and a Skill installed beneath the temporary smoke root.

- [ ] **Step 3: Audit the final diff and ownership boundary**

Run:

```powershell
git diff origin/main...HEAD --check
git diff origin/main...HEAD --name-only
git status --short
```

Expected:

- Every changed path is inside this `image-intake-router` repository.
- No path names a ledger, pantry, 食序管家, 随手账, or another repository root.
- `dist/` remains ignored and does not appear in `git status`.
- No uncommitted tracked changes remain.

- [ ] **Step 4: Record completion without publishing**

Report the exact pass/skip counts, local archive names, checksum, branch, and final commit. Do not create a tag, GitHub Release, merge, or edit any downstream project. Publishing requires a separate explicit user instruction after review.
