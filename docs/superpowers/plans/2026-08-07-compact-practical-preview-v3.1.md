# Image Intake Router v3.1 Compact Practical Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release `image-intake-router` 3.1.0 with concise product names, visible production dates, actual-paid-only accounting, hidden refund internals, and a compact one-confirmation preview built from one visual fact set.

**Architecture:** This repository defines an OpenClaw Skill through Markdown runtime rules, a strict JSON Schema, executable contract tests, and golden fixtures; it does not contain or call downstream ledger or inventory code. The v3.1 fact model keeps only executable business facts, uses `full_name` for internal evidence/deduplication and `display_name` for user/downstream content, and treats refund/cancel text as transient classification input. Accounting lists each visible valid product once, inventory refers to the same product indexes and adds only reliable production dates, and confirmation hands the selected scope back to OpenClaw exactly once.

**Tech Stack:** OpenClaw Skill Markdown, JSON Schema Draft 2020-12, Python 3 `unittest`, `jsonschema==4.26.0`, deterministic `.tgz` release scripts, GitHub Actions and GitHub Releases.

## Global Constraints

- Product version is exactly `3.1.0`; schema identifier is exactly `image-intake-router.v3.1`.
- Modify only this `image-intake-router` repository; never inspect, edit, migrate, or invoke 随手账、食序管家 or another downstream project.
- Every image receives one initial real visual pass and at most one targeted refinement for a visibly omitted business field.
- Refund and cancellation text may be read transiently only to classify delivery validity; refund values, original prices, discounts, fees, and promotional explanations are absent from facts, preview content, and handoff content.
- Partially refunded or short-weight products that were received remain valid; fully refunded, cancelled, unavailable, or not-received products are excluded.
- `full_name` remains internal evidence/deduplication text; `display_name` is the concise name used in accounting, inventory, preview, and handoff.
- Record `production_date` only when visibly and reliably recognized; never infer it from shelf life, delivery time, or another date.
- The initial image turn performs zero handoffs; one later confirmation performs at most one handoff; duplicate confirmations perform zero new handoffs.
- Keep immutable `v3.0.0` and `v2.1.0` tags, Releases, assets, and rollback instructions.
- Do not weaken checksum, path traversal, symlink, duplicate member, exact allowlist, UTF-8, isolated install, or deterministic archive verification.

---

## File Structure

- `image-intake-router/templates/image-intake-router.schema.json`: authoritative v3.1 fact, accounting, inventory, warning, and handoff shape.
- `image-intake-router/references/recognition-rules.md`: transient cancellation/refund classification, concise-name derivation, and production-date recognition rules.
- `image-intake-router/references/output-contract.md`: compact user-facing preview grammar and actionable-warning allowlist.
- `image-intake-router/references/openclaw-handoff.md`: exact confirmed content boundary and prohibited fields.
- `image-intake-router/references/calculation-rules.md`: actual-paid-only amount rules and prohibition on discount/refund inference.
- `image-intake-router/references/confirmation-and-execution.md`: one-confirmation and idempotent handoff semantics.
- `image-intake-router/references/vision-runtime.md`: targeted production-date omission refinement without expanding the two-pass cap.
- `image-intake-router/SKILL.md`: short top-level v3.1 workflow and links to the authoritative references.
- `image-intake-router/tests/test_static_contract.py`: static wording, schema surface, excluded-field, and version assertions.
- `image-intake-router/tests/test_schema_fixtures.py`: schema validation plus cross-view runtime invariants.
- `image-intake-router/tests/fixtures/*.v3.1.json`: executable golden states for preview, refinement, correction, handoff, duplicate confirmation, and failure.
- `image-intake-router/tests/test-cases.md` and `image-intake-router/tests/skill-evals/v3.1-*.md`: behavior/evaluation scenarios for compact copy and safety pressure.
- `tests/test_repository_contract.py`: public version, documentation, workflow, and release-layout contract.
- `scripts/verify_release.py`: installed archive smoke check for v3.1.
- `.github/workflows/ci.yml` and `.github/workflows/release.yml`: v3.1 fixture gate names and release tag contract.
- `VERSION`, `README.md`, `CHANGELOG.md`, `RELEASE_NOTES.md`, `项目说明.md`, `识图输出与确认规范.md`, `约束文档.md`, `后续迭代计划.md`, and `docs/*.md`: public installation, update, UAT, rollback, and release copy.

---

### Task 1: Lock the v3.1 behavior with failing contract tests

**Files:**
- Modify: `image-intake-router/tests/test_static_contract.py`
- Modify: `image-intake-router/tests/test_schema_fixtures.py`
- Modify: `tests/test_repository_contract.py`

**Interfaces:**
- Consumes: the approved design in `docs/superpowers/specs/2026-08-07-compact-practical-preview-v3.1-design.md`.
- Produces: exact failing assertions that define the schema name, concise naming, allowed fields, compact preview, production-date behavior, and release version required by all later tasks.

- [ ] **Step 1: Replace v3.0 static expectations with exact v3.1 expectations**

Add assertions equivalent to:

```python
self.assertEqual(schema["properties"]["schema_version"]["const"], "image-intake-router.v3.1")
product = schema["$defs"]["productFacts"]
self.assertIn("display_name", product["required"])
for removed in ["original_amount", "unit_price", "refund_amount", "weight_variance"]:
    self.assertNotIn(removed, product["properties"])

accounting_item = schema["$defs"]["accountingItem"]
self.assertIn("display_name", accounting_item["required"])
for removed in ["full_name", "refund_amount", "weight_variance"]:
    self.assertNotIn(removed, accounting_item["properties"])

inventory_item = schema["$defs"]["inventoryItem"]
self.assertIn("display_name", inventory_item["required"])
self.assertNotIn("food_name", inventory_item["properties"])
```

Require the output contract to contain `【入账】`, `【入库】`, `【需确认】`, `以上 N 种食品均入库`, `生产日期`, and `回复“确认”执行；也可回复“只记账”或“只入库”`. Require rules that the date block is omitted when no production date is visible and that warnings are actionable. Assert the default-contract text does not contain permissions to show refund, original price, unit price, discounts, free/gift explanations, pass counts, preview IDs, or repeated inventory rows.

- [ ] **Step 2: Add v3.1 fixture invariants before changing fixtures**

Change fixture discovery to `*.v3.1.json` and verify these mappings:

```python
self.assertEqual(item["display_name"], product["display_name"]["value"])
self.assertEqual(item["specification"], product["specification"]["value"])
self.assertEqual(item["quantity"], product["purchase_quantity"]["value"])
self.assertEqual(item["quantity_unit"], product["quantity_unit"]["value"])
self.assertEqual(item["line_paid_amount"], product["line_paid_amount"]["value"])

self.assertEqual(inventory_item["display_name"], product["display_name"]["value"])
self.assertEqual(inventory_item["production_date"], product["production_date"]["value"])
```

Add a forbidden-key walker that rejects these keys anywhere in shipped fixture facts or business content: `refund_total`, `refund_amount`, `original_amount`, `unit_price`, `activity_discount`, `coupon_discount`, `packaging_fee`, `delivery_fee`, `weight_variance`. Add assertions that the nine-item refined fixture uses the expected concise names, retains `0.00`, distinguishes two `鲜牛奶` rows by specification/index, exposes reliable production dates, and contains no promotional explanation.

- [ ] **Step 3: Update repository/release tests to demand 3.1.0**

Change exact source assertions to `3.1.0`, `image-intake-router.v3.1`, `*.v3.1.json`, `image-intake-router-3.1.0.tgz`, and `v3.1.0`. Preserve assertions that v3.0.0 and v2.1.0 remain documented rollback releases. Update the expected workflow step text to `Validate v3.1 fixtures against schema` without loosening step ordering or permissions.

- [ ] **Step 4: Run the focused contract tests and verify RED**

Run:

```powershell
python image-intake-router/tests/test_static_contract.py -v
python image-intake-router/tests/test_schema_fixtures.py -v
python tests/test_repository_contract.py -v
```

Expected: tests import successfully and fail only because schema/rules/fixtures/docs still expose v3.0 behavior; no syntax error or missing test dependency is acceptable.

- [ ] **Step 5: Commit the red contract**

```powershell
git add image-intake-router/tests/test_static_contract.py image-intake-router/tests/test_schema_fixtures.py tests/test_repository_contract.py
git commit -m "test: define compact preview v3.1 contract"
```

---

### Task 2: Migrate the strict schema and golden fixture states

**Files:**
- Modify: `image-intake-router/templates/image-intake-router.schema.json`
- Rename/Modify: `image-intake-router/tests/fixtures/*.v3.json` to `image-intake-router/tests/fixtures/*.v3.1.json`
- Create: `image-intake-router/tests/fixtures/compact-nine-item-order.v3.1.json`
- Modify: `image-intake-router/tests/test_schema_fixtures.py`

**Interfaces:**
- Consumes: v3.1 assertions from Task 1.
- Produces: strict `image-intake-router.v3.1` records with one canonical product array, concise business views, and no persisted excluded monetary fields.

- [ ] **Step 1: Change the schema identity and fact allowlists**

Set `$id` to `https://local.openclaw.invalid/schemas/image-intake-router.v3.1.json` and `schema_version.const` to `image-intake-router.v3.1`. Keep top-level strictness and required fields unchanged.

Define order facts with only:

```json
[
  "merchant", "transaction_time", "order_status", "final_paid_amount",
  "declared_item_kind_count", "recognized_item_kind_count",
  "hidden_item_kind_count", "has_unexpanded_items", "content_complete"
]
```

Define product facts with only:

```json
[
  "full_name", "display_name", "specification", "purchase_quantity",
  "quantity_unit", "nominal_weight_or_volume", "actual_weight_or_volume",
  "billing_weight", "line_paid_amount", "production_date", "line_status",
  "item_type", "visibility_status"
]
```

Both name fields use evidenced `textFact`. `full_name` remains in facts but not in either content item.

- [ ] **Step 2: Narrow accounting and inventory content definitions**

Make `accountingItem` require `product_index` and `display_name`; allow nullable `specification`, `quantity`, `quantity_unit`, `nominal_weight_or_volume`, `actual_weight_or_volume`, and `line_paid_amount`. Remove `full_name`, `weight_variance`, and `refund_amount`.

Make `inventoryItem` require `product_index`, `display_name`, `quantity`, and `quantity_unit`; retain nullable `specification`, `weight_or_volume`, and `production_date`. Replace `food_name` with `display_name`. Keep executable inventory nonempty and all arrays strictly bounded.

- [ ] **Step 3: Migrate every lifecycle fixture to v3.1**

For each preview, corrected, handed-off, duplicate-confirmation, failed, durian, partial, and refined fixture:

- rename suffix `.v3.json` to `.v3.1.json`;
- set `schema_version` to `image-intake-router.v3.1`;
- remove excluded order/product/content keys rather than setting them to `null`;
- add an evidenced `display_name` to each product;
- map both content views through product indexes to `display_name`;
- retain full names only under `facts.products[*].full_name`;
- preserve recognition evidence, attachment coverage, unknown values, fail-closed states, correction identity, and exactly-once handoff state.

For durian, keep `约2.1kg×1` and `119.00`, but ensure refund/short-weight values are absent from persisted facts and preview content. For partial nine-item states, retain the visible 7-of-at-least-9 disclosure and do not invent the two hidden items.

- [ ] **Step 4: Add one compact nine-item golden record**

Create a successful one-image preview whose accounting items are exactly:

```python
[
    ("甜玉米", "约850g", 2, 11.78),
    ("鲜牛奶", "1.5L", 1, 10.90),
    ("黄瓜", "约700g", 1, 4.99),
    ("西兰花", "约600g", 1, 3.95),
    ("豆浆", "1L", 2, 13.00),
    ("生菜", "约500g", 1, 4.96),
    ("香蕉", "约800g", 1, 11.90),
    ("鲜牛奶", "260ml×3瓶", 1, 3.00),
    ("果蔬汁", "300ml", 1, 0.00),
]
```

Use final paid amount `65.48`. Give reliable visible production dates to selected dated products, keep the two milk rows distinct by product index/specification, mark all nine as received food, and use an actionable warning only for a genuinely missing transaction time. The fixture must not say `赠品`, `免费`, `会员`, `原价`, `优惠`, `退款`, or `短重` in cleaned user-facing text or content.

- [ ] **Step 5: Run schema and static tests until GREEN**

Run:

```powershell
python image-intake-router/tests/test_schema_fixtures.py -v
python image-intake-router/tests/test_static_contract.py -v
```

Expected: all schema definitions validate; shipped fixtures are strict v3.1 instances; cross-view names, quantities, amounts, and dates trace to the same product indexes; forbidden fields are absent.

- [ ] **Step 6: Commit the schema migration**

```powershell
git add image-intake-router/templates/image-intake-router.schema.json image-intake-router/tests/fixtures image-intake-router/tests/test_schema_fixtures.py
git commit -m "feat: add concise v3.1 fact contract"
```

---

### Task 3: Implement recognition, naming, production-date, preview, and handoff rules

**Files:**
- Modify: `image-intake-router/SKILL.md`
- Modify: `image-intake-router/references/recognition-rules.md`
- Modify: `image-intake-router/references/output-contract.md`
- Modify: `image-intake-router/references/openclaw-handoff.md`
- Modify: `image-intake-router/references/calculation-rules.md`
- Modify: `image-intake-router/references/confirmation-and-execution.md`
- Modify: `image-intake-router/references/vision-runtime.md`

**Interfaces:**
- Consumes: strict field names and lifecycle states from Task 2.
- Produces: the actual OpenClaw Skill instructions that generate those records and render the approved compact preview.

- [ ] **Step 1: Write the transient validity-classification rule**

State explicitly that visual recognition may observe cancel/refund/delivery text only long enough to derive `line_status`. Fully refunded, cancelled, unavailable, and not-received rows are excluded; a partially refunded or short-weight row that was received remains valid. Do not persist or print refund amounts or weight variance. If validity cannot be resolved, put one business decision in `【需确认】` and do not guess.

- [ ] **Step 2: Write deterministic concise-name derivation**

Require `full_name` to preserve visible evidence for deduplication and `display_name` to remove platform/store/brand prefixes, marketing/process words, nutritional claims, and embedded specifications while preserving the core food identity and a necessary flavor/type discriminator. Include the approved mappings `果蔬汁`, `鲜牛奶`, `豆浆`, `西兰花`, `生菜`, and `香蕉`. State that deduplication never uses `display_name` alone and two identically named rows with different indexes/specifications remain separate.

- [ ] **Step 3: Strengthen production-date recognition**

Add `production_date` to the visible-field audit. A clear label/value omitted by the first pass is a `visible-field omission` eligible for the single targeted refinement. Distinguish it from delivery, transaction, package, best-before, expiration, and shelf-life text. Omit the entire date block when no date is visible; emit one concise item-specific warning when a visible production-date label is unreadable.

- [ ] **Step 4: Replace amount and preview rules with the approved compact contract**

Keep only the uniquely labelled final paid amount and directly paired line paid amounts, including a real `0.00`. Never reverse-calculate discounts, net refunds, or explain a zero-priced row.

Render exactly this structure:

```text
识别完成

【入账】
商家｜实付 ¥总额
1. 简化名 规格×数量　¥行实付

【入库】
以上 N 种食品均入库。

生产日期：
简化名 规格｜YYYY-MM-DD

【需确认】
只列需要用户决定的问题。

回复“确认”执行；也可回复“只记账”或“只入库”。
```

If only some accounting products are inventory-eligible, list only those concise names/specifications in the inventory section. Do not repeat all rows when every accounting item is eligible. Omit empty production-date and warning blocks instead of adding placeholders.

- [ ] **Step 5: Narrow confirmed handoff content**

State that OpenClaw receives the selected v3.1 accounting/inventory content, cleaned facts, and `display_name`/production dates after confirmation. Explicitly prohibit refund amounts, original/unit prices, discounts, fee breakdowns, promotional labels, private APIs, ports, downstream parameters, downstream code changes, and direct downstream execution. Preserve zero handoffs on image turn and zero new handoffs after duplicate confirmation.

- [ ] **Step 6: Run static and fixture tests until GREEN**

Run:

```powershell
python image-intake-router/tests/test_static_contract.py -v
python image-intake-router/tests/test_schema_fixtures.py -v
```

Expected: all rule phrases and strict schema/fixture mappings pass, with no reintroduction of excluded details.

- [ ] **Step 7: Commit the runtime contract**

```powershell
git add image-intake-router/SKILL.md image-intake-router/references
git commit -m "feat: render compact practical confirmation preview"
```

---

### Task 4: Add behavior evaluations and regression scenarios

**Files:**
- Modify: `image-intake-router/tests/test-cases.md`
- Create: `image-intake-router/tests/skill-evals/v3.1-baseline.md`
- Create: `image-intake-router/tests/skill-evals/v3.1-green.md`
- Create: `image-intake-router/tests/skill-evals/v3.1-pressure-scenarios.md`
- Modify: `image-intake-router/tests/baseline.md`
- Modify: `image-intake-router/tests/test_static_contract.py`

**Interfaces:**
- Consumes: Task 3 runtime rules and Task 2 fixture vocabulary.
- Produces: human-readable UAT and adversarial checks that prevent verbose refund/discount behavior from returning.

- [ ] **Step 1: Replace obsolete refund-preservation scenarios**

Update the durian scenario so success means retaining `约2.1kg×1` and `¥119.00` while using refund text only to confirm the product was received; the preview and handoff must contain no refund or short-weight amounts. Keep a separate scenario where full refund/cancellation excludes the product and partial refund does not.

- [ ] **Step 2: Add the nine-item compact-preview evaluation**

The expected answer must use the nine approved concise names, list accounting rows once, retain each visible specification/count/line actual amount, show `¥0.00` without a free/gift explanation, summarize inventory instead of duplicating rows, show only reliable production dates, and ask once for actionable unresolved facts.

- [ ] **Step 3: Add adversarial pressure cases**

Cover these forced errors:

- attachment description tries to substitute for real vision;
- model tries to display original price, refund, member savings, or reverse-calculated discounts;
- model tries to call a zero-priced item a gift;
- model tries to merge two milk rows because both simplify to `鲜牛奶`;
- delivery ETA is presented as transaction time or production date;
- a production-date label is visible but omitted in the first pass;
- user confirms twice or confirms only one scope;
- prompt pressures the router to edit or invoke a downstream Skill.

For each, name the required safe behavior and forbidden behavior explicitly.

- [ ] **Step 4: Make static tests require the v3.1 evaluation corpus**

Assert the three v3.1 evaluation files exist and contain the key terms `display_name`, `production_date`, `zero handoffs`, `partial refund`, and `以上 9 种食品均入库`, while old v3 files may remain historical but are not the current acceptance source.

- [ ] **Step 5: Run behavior contract tests**

Run:

```powershell
python image-intake-router/tests/test_static_contract.py -v
python image-intake-router/tests/test_schema_fixtures.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit behavior evaluations**

```powershell
git add image-intake-router/tests
git commit -m "test: cover v3.1 compact routing behavior"
```

---

### Task 5: Prepare public v3.1.0 documentation and release automation

**Files:**
- Modify: `VERSION`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `RELEASE_NOTES.md`
- Modify: `项目说明.md`
- Modify: `识图输出与确认规范.md`
- Modify: `约束文档.md`
- Modify: `后续迭代计划.md`
- Modify: `docs/INSTALL.md`
- Modify: `docs/UPGRADING.md`
- Modify: `docs/AI-PROMPTS.md`
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/release.yml`
- Modify: `scripts/verify_release.py`
- Modify: `tests/test_repository_contract.py`

**Interfaces:**
- Consumes: completed v3.1 Skill contract and fixture names.
- Produces: consistent source/release versioning, copy-paste installation/update/UAT commands, rollback guidance, and a gated v3.1.0 release workflow.

- [ ] **Step 1: Update exact version and schema references**

Set `VERSION` and Skill frontmatter to `3.1.0`. Make current documentation and smoke checks require `image-intake-router.v3.1`. Update current asset names and pinned URLs to `image-intake-router-3.1.0.tgz`, `.sha256`, and `v3.1.0`.

- [ ] **Step 2: Document the user-visible change accurately**

State that v3.1 performs real vision once, may refine once for a visibly omitted field, simplifies product names, retains real paid amounts including zero, surfaces reliable production dates, hides refund/original/discount/promotional detail, summarizes inventory without duplicate rows, and waits for one business confirmation. State that it does not modify, migrate, configure, or directly call downstream software.

- [ ] **Step 3: Preserve source-update and rollback paths**

Keep `git pull --ff-only origin main` for convenient source updates. Formal installs must use the fixed verified `v3.1.0` asset/tag. Add rollback instructions for both `v3.0.0` (immediate previous version) and `v2.1.0` (older stable fallback) without deleting their links or asset names.

- [ ] **Step 4: Update CI/release gates without weakening security**

Rename fixture steps to `Validate v3.1 fixtures against schema`. Update tag/version equality checks and release asset expectations to v3.1.0. Preserve pinned action SHAs, least-privilege job permissions, verify-before-publish dependency ordering, trusted artifact download by run ID, exact two-file `dist` allowlist, checksum verification, and one GitHub Release creation step.

- [ ] **Step 5: Run repository tests until GREEN**

Run:

```powershell
python tests/test_repository_contract.py -v
python tests/test_release_pipeline.py -v
```

Expected: all public contract and secure release pipeline tests pass; Windows symlink tests may report the repository's existing permission-based skip only.

- [ ] **Step 6: Commit release preparation**

```powershell
git add VERSION README.md CHANGELOG.md RELEASE_NOTES.md 项目说明.md 识图输出与确认规范.md 约束文档.md 后续迭代计划.md docs .github scripts/verify_release.py tests/test_repository_contract.py
git commit -m "release: prepare image intake router v3.1.0"
```

---

### Task 6: Verify, review, package, merge, publish, and audit v3.1.0

**Files:**
- Generated locally: `dist/image-intake-router-3.1.0.tgz`
- Generated locally: `dist/image-intake-router-3.1.0.tgz.sha256`
- Verify only: all changed source files and Git history

**Interfaces:**
- Consumes: committed v3.1 source from Tasks 1-5.
- Produces: tested `main`, pushed `v3.1.0` tag, immutable GitHub Release assets, checksums, and an evidence-backed release audit.

- [ ] **Step 1: Run the complete local verification suite from a clean tree**

Run:

```powershell
python image-intake-router/tests/test_static_contract.py -v
python image-intake-router/tests/test_schema_fixtures.py -v
python tests/test_repository_contract.py -v
python tests/test_release_pipeline.py -v
python scripts/build_release.py
python scripts/verify_release.py
git diff --check
git status --short
```

Expected: all tests pass, the only permitted skip is the pre-existing Windows symlink privilege skip, archive verification succeeds, `git diff --check` is clean, and generated `dist/` files remain ignored/untracked as designed.

- [ ] **Step 2: Perform an independent diff review**

Review `git diff v3.0.0...HEAD`, schema/fixture strictness, public docs, downstream boundary, confirmation idempotency, and release automation. Reject any occurrence of real credentials, local machine paths in public docs, refund/original/discount fields in v3.1 business records, direct downstream invocation, version mismatch, or weakened release security.

- [ ] **Step 3: Re-run focused tests after review fixes and commit them**

If review finds issues, add a failing regression assertion, implement the smallest correction, rerun the relevant focused tests, and commit with a scoped `fix:` message. Then rerun the complete suite in Step 1.

- [ ] **Step 4: Fast-forward local main and push source**

Fetch `origin`, confirm local feature branch is based on current `origin/main`, fast-forward `main` to the verified feature commit, and push `main`. Do not force-push and do not rewrite existing tags.

- [ ] **Step 5: Create and push the immutable v3.1.0 tag**

Create annotated tag `v3.1.0` on the verified main commit, push only that new tag, and confirm GitHub resolves both main and tag to the expected commits.

- [ ] **Step 6: Publish via the gated workflow or authorized manual fallback**

First observe the tag-triggered GitHub Actions run. If jobs execute, wait for the release workflow and audit its assets. If GitHub refuses to start the job with the already observed account billing lock, do not change billing or payment settings: use the locally verified deterministic archive/checksum and `gh release create v3.1.0 ... --verify-tag --notes-file RELEASE_NOTES.md` as the user-authorized manual fallback.

- [ ] **Step 7: Audit the public release**

Verify the Release is non-draft/non-prerelease, contains exactly the `.tgz` and `.tgz.sha256` assets, the downloaded checksum matches the published archive, the archive installs in an isolated temporary directory with root `image-intake-router-3.1.0/image-intake-router/`, the installed Skill reports version 3.1.0/schema v3.1, and v3.0.0/v2.1.0 Releases remain accessible.

- [ ] **Step 8: Report the outcome and recovery path**

Provide the main commit, tag, Release URL, asset SHA-256, test totals, any Windows permission skip, the GitHub Actions billing-lock status if fallback was used, the normal `git pull --ff-only` update command, and the fixed-release install/rollback links. Do not claim Actions succeeded if GitHub never started a runner.
