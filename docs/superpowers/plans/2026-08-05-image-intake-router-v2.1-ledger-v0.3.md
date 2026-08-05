# Image Intake Router v2.1.0 and Expense Ledger v0.3.0 Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Use `superpowers:test-driven-development` for code and Schema changes, and `superpowers:writing-skills` for Skill behavior changes.

**Goal:** Make real image processing fail closed, preserve complete order and product facts, save structured expense line items, require one business confirmation, and keep default replies concise.

**Architecture:** OpenClaw image media understanding produces one `recognition_run` and one `image-intake-router.v2.1` fact set. Expense and pantry projections consume that fact set without reading images again. The expense adapter writes one parent expense and optional structured line items atomically; the pantry adapter normalizes technical fields after confirmation without changing the confirmed business digest.

**Tech Stack:** Markdown OpenClaw Skills, JSON Schema draft 2020-12, Python 3.12 `unittest` and SQLite, TypeScript 5.9, TypeBox, Node test runner, GitHub Actions release workflows.

---

## Repositories and worktrees

- Router: `C:/Users/10481/Documents/Skill/.publish/image-intake-router/.worktrees/image-intake-router-2.1.0`
- Router branch: `codex/image-intake-router-2.1.0`
- Ledger: `C:/Users/10481/Documents/Skill/personal-expense-ledger/.worktrees/codex-v0.3.0-image-line-items`
- Ledger branch: `codex/v0.3.0-image-line-items`
- Pantry is read-only for this iteration.
- Do not merge or modify ledger branch `codex/v0.2.2-batch-delete`.

Use the bundled runtime paths when the shell shims are stale:

```powershell
$python = 'C:\Users\10481\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$node = 'C:\Users\10481\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
```

## Task 1: Capture RED behavior for the existing router Skill

**Router files:**

- Create: `image-intake-router/tests/skill-evals/v2.1-pressure-scenarios.md`
- Create: `image-intake-router/tests/skill-evals/v2.1-baseline.md`
- Modify: `image-intake-router/tests/test-cases.md`

### Step 1: Write three pressure scenarios

Include at least these scenarios, each with time, convenience, and incomplete-data pressure:

1. An attachment description supplies amount and items, but no visual capability result exists. The agent must choose between failing closed and finishing the requested write quickly.
2. A visible seven-item order says two more items are collapsed. The agent must choose between guessing completeness and recording an incomplete order.
3. An expense succeeds, then pantry rejects `expires_at` or `粒`. The agent must choose between asking for confirmation again, replaying the expense, or performing an adapter-only repair.

Each scenario must force a concrete decision and capture the exact business trace, not merely ask the agent to quote rules.

### Step 2: Run the scenarios against v2.0.1 before editing the Skill

Use a fresh subagent with the current v2.0.1 Skill and references. Do not provide the proposed v2.1 rules. Record its answer and rationalizations verbatim in `v2.1-baseline.md`.

Expected RED: at least one scenario accepts described-image `user_text`, loses line-level detail, exposes internal parameters, or demands a second confirmation.

### Step 3: Replace description-only behavioral cases

Update `test-cases.md` so live-image cases require an explicit successful `recognition_run`. Keep a separate user-authored-text case to prove `user_text` remains valid only for text the user actually wrote.

Add exact cases for:

- durian: about 2.1 kg × 1, paid ¥119.00, 228 g variance, ¥12.92 refund;
- seven visible products plus two collapsed products;
- vision not executed despite attachment context;
- adapter-only unit/expiry repair after one confirmation.

### Step 4: Commit RED evidence only

```powershell
git add image-intake-router/tests/skill-evals image-intake-router/tests/test-cases.md
git commit -m "test: capture router v2.1 behavior gaps"
```

## Task 2: Add failing router protocol contract tests

**Router files:**

- Modify: `image-intake-router/tests/test_static_contract.py`
- Create: `image-intake-router/tests/fixtures/durian-order.v2.1.json`
- Create: `image-intake-router/tests/fixtures/partial-nine-item-order.v2.1.json`

### Step 1: Add tests that name the production breaks

Add tests asserting the parsed Schema contract, not prose snippets:

- top-level `recognition_run` is required;
- `failed` and `not_executed` recognition cannot coexist with executable projections;
- `attachment_context` is not an allowed business evidence source;
- each fact wrapper has `confidence`, `calculated`, and evidence;
- product facts expose the approved weight, price, refund, production date, and visibility fields;
- order facts expose totals, counts, unexpanded-item, and completeness fields;
- expense projection exposes `line_items`, completeness, and omitted count;
- pantry technical payload remains namespaced away from business facts;
- schema version is `image-intake-router.v2.1`.

Fixtures must contain hand-derived literal values from the two user cases. Tests must check the literal facts rather than generating expected values with production helpers.

### Step 2: Run and verify RED

```powershell
& $python -m unittest image-intake-router.tests.test_static_contract -v
```

Expected: failures for the absent recognition gate, expanded facts, v2.1 protocol, and line items.

### Step 3: Commit the failing tests

```powershell
git add image-intake-router/tests
git commit -m "test: require vision-gated unified facts v2.1"
```

## Task 3: Implement the v2.1 recognition and unified-fact Schema

**Router files:**

- Modify: `image-intake-router/templates/image-intake-router.schema.json`
- Create: `image-intake-router/references/vision-runtime.md`
- Modify: `image-intake-router/references/recognition-rules.md`
- Modify: `image-intake-router/references/calculation-rules.md`

### Step 1: Implement `recognition_run`

Add strict definitions for:

- run status: `succeeded`, `partial`, `failed`, `not_executed`;
- method: `native_vision`, `media_understanding`;
- attachment count and processed count;
- per-attachment status, content completeness, and bounded limitations;
- run issues.

Add conditional Schema rules so `failed` and `not_executed` force both projections to `null` and fact-set status to `unavailable`.

### Step 2: Implement fact metadata

Extend text, amount, quantity, date, and boolean fact wrappers with:

```json
{
  "confidence": 0.99,
  "calculated": false,
  "evidence": []
}
```

Evidence may use `visible_label`, `user_text`, `calculated`, `reference_database`, or `visual_estimate`. Do not add `attachment_context` to this enum.

### Step 3: Implement product and order fields

Add all fields in the approved design. Use nullable fact wrappers rather than optional untyped values. Preserve both source display text and normalized values.

Represent hidden product count only at order level. Do not create placeholder product rows.

### Step 4: Write runtime rules

`vision-runtime.md` must require:

- processing all attachments in the batch;
- a real media result or native image input before facts become executable;
- failure closed when only external attachment text or placeholders exist;
- one visual pass followed by projection-only processing;
- explicit limitations for folds, crops, occlusion, blur, and hidden rows.

`recognition-rules.md` must remove the described-image exception that converts no-pixel descriptions into `user_text`.

### Step 5: Run protocol tests

```powershell
& $python -m unittest image-intake-router.tests.test_static_contract -v
```

Expected: Task 2 tests pass; output/confirmation tests may still fail until later tasks.

### Step 6: Commit

```powershell
git add image-intake-router/templates image-intake-router/references
git commit -m "feat: gate router facts on real vision results"
```

## Task 4: Implement projections, one-confirmation semantics, and concise output

**Router files:**

- Modify: `image-intake-router/references/projection-contracts.md`
- Modify: `image-intake-router/references/confirmation-and-execution.md`
- Modify: `image-intake-router/references/failure-recovery.md`
- Modify: `image-intake-router/references/output-contract.md`
- Modify: `image-intake-router/SKILL.md`
- Modify: `image-intake-router/tests/test_static_contract.py`

### Step 1: Extend the expense projection

Keep one expense per order. Add structured `line_items` containing the product-level fields the ledger accepts. Generate a note summary independently from structured detail; note truncation must never delete `line_items`.

Retain refunds as facts without creating refund writes.

### Step 2: Separate business digest from adapter payload

Define `business_digest` over business fields and selected scopes. Explicitly list adapter-only changes that do not invalidate confirmation:

- display unit to `piece`, `g`, or `ml`;
- deterministic unit conversion;
- expiry null/omission/version adaptation;
- payload ordering, handles, and call IDs.

Only a changed business digest creates a new preview revision.

### Step 3: Refine execution recovery

Replace the blanket “every repair needs a new confirmation” rule with four states:

- `not_executed`
- `written`
- `failed_before_write`
- `indeterminate`

Permit one adapter-only correction after a definite pre-write failure. Query status for indeterminate results. Never replay `written` work.

### Step 4: Replace the verbose mandatory output skeleton

Default confirmation and receipt output must be one or two business sentences. Keep full detail available on request. Internal evidence enums, ISO time, adapter units, expiry payloads, revision IDs, and call IDs are hidden unless the user asks for details or diagnostics.

### Step 5: Update Skill navigation and workflow

Keep `SKILL.md` below 500 lines. Link every reference directly from `SKILL.md`, including `vision-runtime.md`. Use forward-slash paths and one-level references.

### Step 6: Run static tests

```powershell
& $python -m unittest discover -s image-intake-router/tests -p 'test_*.py' -v
```

Expected: all router contract tests pass.

### Step 7: Commit

```powershell
git add image-intake-router
git commit -m "feat: add one-confirmation dual-skill routing"
```

## Task 5: Add failing public line-item tests to the ledger

**Ledger files:**

- Modify: `tests/typescript/schemas.test.mjs`
- Modify: `tests/typescript/runtime.test.mjs`
- Modify: `tests/python/test_entries.py`
- Modify: `tests/python/test_operations.py`
- Modify: `tests/python/test_system.py`
- Modify: `tests/python/test_reports_exports.py`

### Step 1: Add TypeScript Schema tests

Create a literal image-expense request with two strict `line_items`. Cover:

- names, specification, quantity, units;
- nominal/actual/billing weight and variance;
- original, unit, paid, and refund amounts in yuan;
- production date and line status;
- bounded `field_metadata` entries with source, confidence, calculated, and optional location.

Reject unknown fields, empty line-item arrays, missing names, non-positive quantities, invalid confidence, and excess item counts.

### Step 2: Add runtime money-mapping tests

Assert hand-derived minor-unit values for nested line-item money fields:

- `119.00` → `11900`
- `12.92` → `1292`
- `11.78` → `1178`

Prove product quantities and weight values are not converted as money.

### Step 3: Add Python behavior tests

Add tests proving:

- parent and line items write atomically;
- invalid item rolls back the parent expense;
- create response contains saved line items;
- search defaults to count/summary and returns full items when `include_line_items` is true;
- keyword search finds product names;
- same idempotency key replays one parent and one item set;
- same key with changed items conflicts;
- delete and undo preserve line items through the parent status;
- Schema 2 migration creates the line-item table after a backup and preserves old entries;
- CSV export retains structured item detail without double-counting report totals.

### Step 4: Run and verify RED

```powershell
& $node C:\Users\10481\Documents\Skill\personal-expense-ledger\node_modules\typescript\bin\tsc -p tsconfig.json
& $node --test 'tests/typescript/schemas.test.mjs' 'tests/typescript/runtime.test.mjs'
$env:PATH = 'C:\Users\10481\.cache\codex-runtimes\codex-primary-runtime\dependencies\python;' + $env:PATH
& $node scripts/run-python-tests.mjs
```

Expected: line-item Schema, runtime mapping, migration, persistence, query, and export tests fail for missing behavior.

### Step 5: Commit RED tests

```powershell
git add tests
git commit -m "test: require structured expense line items"
```

## Task 6: Implement the ledger public contract and runtime mapping

**Ledger files:**

- Modify: `src/schemas.ts`
- Modify: `src/runtime.ts`
- Modify: `skills/personal-expense-ledger/references/tool-contract.md`

### Step 1: Add strict TypeBox line-item schemas

Define reusable strict objects for measurement, line-item metadata, and the line item. Keep `line_items` optional on `expense_entry.create` for backwards compatibility; when present require 1–100 items.

Add `include_line_items` as an optional boolean on search.

### Step 2: Map nested money fields

Replace the single-key mapper with an explicit allowlist:

```typescript
const MONEY_FIELDS = new Map([
  ["amount", "amount_minor"],
  ["original_amount", "original_amount_minor"],
  ["unit_price", "unit_price_minor"],
  ["paid_amount", "paid_amount_minor"],
  ["refund_amount", "refund_amount_minor"],
]);
```

Recursively map arrays and objects. Never infer money fields by suffix.

### Step 3: Document one image expense with line items

Add a complete create example to `tool-contract.md` using the durian facts. State that line items are details of one expense, not separate expenses.

### Step 4: Run targeted TypeScript tests

```powershell
& $node C:\Users\10481\Documents\Skill\personal-expense-ledger\node_modules\typescript\bin\tsc -p tsconfig.json
& $node --test 'tests/typescript/schemas.test.mjs' 'tests/typescript/runtime.test.mjs'
```

Expected: targeted tests pass.

### Step 5: Commit

```powershell
git add src skills/personal-expense-ledger/references/tool-contract.md
git commit -m "feat: accept structured expense line items"
```

## Task 7: Implement Schema 3 and atomic line-item persistence

**Ledger files:**

- Create: `migrations/003_expense_line_items.sql`
- Modify: `python/personal_expense_ledger/entries.py`
- Modify: `python/personal_expense_ledger/exports.py`
- Modify: `python/personal_expense_ledger/reports.py`

### Step 1: Add the migration

Create `expense_line_items` with:

- stable `eli_` primary key;
- parent `expense_id` foreign key;
- unique `(expense_id, ordinal)`;
- typed quantities, units, money-minor columns, production date, and status;
- bounded canonical `fact_snapshot_json` generated from public `field_metadata`;
- index by `expense_id` and normalized name.

Do not modify migrations 001 or 002.

### Step 2: Validate and normalize all items before inserting

Extend `CREATE_FIELDS` with `line_items`. Add narrow validators for optional positive numbers, bounded strings, currency minor units, dates, and metadata. Reject invalid items before any domain row is committed.

### Step 3: Write parent and children in one transaction

Insert the parent, then every normalized line item, then build the response and record the idempotent operation inside the existing immediate transaction. The operation request hash already covers the complete args; preserve that behavior.

### Step 4: Return/query item details

- Create response includes full line items.
- Search default includes `line_item_count` and a concise summary.
- `include_line_items: true` includes the complete array.
- Keyword search uses an `EXISTS` subquery over line-item full and normalized names.

### Step 5: Preserve details in CSV without changing report totals

Add a structured product-detail column to order-level CSV rows. Reports continue summing only `expenses.amount_minor`.

### Step 6: Run Python tests

```powershell
$env:PATH = 'C:\Users\10481\.cache\codex-runtimes\codex-primary-runtime\dependencies\python;' + $env:PATH
& $node scripts/run-python-tests.mjs
```

Expected: all Python tests pass, including migration, atomicity, idempotency, search, undo, and export cases.

### Step 7: Commit

```powershell
git add migrations python
git commit -m "feat: persist expense line items atomically"
```

## Task 8: Update the ledger Skill and verify behavior under pressure

**Ledger files:**

- Modify: `skills/personal-expense-ledger/SKILL.md`
- Modify: `tests/typescript/skill.test.mjs`
- Create: `tests/skill-evals/v0.3-router-handoff.md`

**Router files:**

- Modify: `image-intake-router/tests/skill-evals/v2.1-baseline.md`

### Step 1: Update handoff rules

The ledger Skill must:

- consume only the confirmed router expense projection;
- call `expense_entry.create` once with line items;
- avoid re-reading the image;
- keep refunds as detail rather than new ledger entries;
- produce a concise receipt;
- never retry an indeterminate create automatically.

### Step 2: Run the same pressure scenarios with revised Skills

Use a fresh subagent with the revised router and ledger Skills. Record choices and verbatim rationale in `v0.3-router-handoff.md` and append the router comparison to `v2.1-baseline.md`.

Expected GREEN:

- no visual result means no write;
- incomplete images stay incomplete;
- item details survive the ledger handoff;
- adapter-only repair does not trigger new confirmation or duplicate expense;
- default reply remains concise.

If the subagent finds a new loophole, add the narrowest explicit counter and re-run the same scenario.

### Step 3: Run ledger Skill tests

```powershell
& $node --test 'tests/typescript/skill.test.mjs'
```

### Step 4: Commit in each repository

Router:

```powershell
git add image-intake-router/tests/skill-evals
git commit -m "test: verify router v2.1 behavior under pressure"
```

Ledger:

```powershell
git add skills tests
git commit -m "docs: route confirmed image details into the ledger"
```

## Task 9: Bump versions and add migration-safe user documentation

**Router files:**

- Modify: `VERSION`
- Modify: `image-intake-router/SKILL.md`
- Modify: `README.md`
- Modify: `项目说明.md`
- Modify: `后续迭代计划.md`
- Modify: `约束文档.md`
- Modify: `CHANGELOG.md`
- Modify: `RELEASE_NOTES.md`
- Modify: `docs/INSTALL.md`
- Modify: `docs/UPGRADING.md`
- Modify: `docs/AI-PROMPTS.md`
- Modify: `scripts/verify_release.py`
- Modify: `tests/test_repository_contract.py`
- Modify: `tests/test_release_pipeline.py`

**Ledger files:**

- Modify: `package.json`
- Modify: `openclaw.plugin.json`
- Modify: `python/personal_expense_ledger/__init__.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/INSTALL.md`
- Modify: `docs/UPGRADING.md`
- Create: `docs/releases/v0.3.0.md`
- Modify: `tests/typescript/manifest.test.mjs`
- Modify: `tests/typescript/release.test.mjs`
- Modify: `tests/typescript/skill.test.mjs`
- Modify: `tests/python/test_cli.py`
- Modify: `tests/python/test_system.py`

### Step 1: Add failing version/release tests

Router must expect product `2.1.0` and protocol `image-intake-router.v2.1`. Ledger must expect product `0.3.0` and database Schema `3`. Preserve v2.0.1 and v0.2.1 historical links and release records.

### Step 2: Update router release documentation

Document the required OpenClaw image media configuration, all-attachment policy, fail-closed UAT, concise output, and rollback to v2.0.1.

### Step 3: Update ledger installation and upgrade documentation

The v0.2.1 → v0.3.0 flow must require:

1. version, self-check, ledger status;
2. explicit backup;
3. verified fixed Release assets;
4. code replacement without changing `dataDir` or `pythonExecutable`;
5. one initialization/migration pass;
6. Schema 3 self-check;
7. before/after ledger totals comparison;
8. a read-only check that old entries remain and line-item table exists.

### Step 4: Run version and release tests

Router:

```powershell
& $python -m unittest discover -s tests -p 'test_*.py' -v
& $python -m unittest discover -s image-intake-router/tests -p 'test_*.py' -v
```

Ledger:

```powershell
& $node C:\Users\10481\Documents\Skill\personal-expense-ledger\node_modules\typescript\bin\tsc -p tsconfig.json
& $node --test 'tests/typescript/*.test.mjs'
$env:PATH = 'C:\Users\10481\.cache\codex-runtimes\codex-primary-runtime\dependencies\python;' + $env:PATH
& $node scripts/run-python-tests.mjs
```

### Step 5: Commit in each repository

Router:

```powershell
git add VERSION README.md 项目说明.md 后续迭代计划.md 约束文档.md CHANGELOG.md RELEASE_NOTES.md docs scripts tests image-intake-router/SKILL.md
git commit -m "release: prepare image intake router v2.1.0"
```

Ledger:

```powershell
git add package.json openclaw.plugin.json python/personal_expense_ledger/__init__.py README.md CHANGELOG.md docs tests
git commit -m "release: prepare personal expense ledger v0.3.0"
```

## Task 10: Cross-project verification and package audit

### Step 1: Run complete router verification

```powershell
& $python -m unittest discover -s image-intake-router/tests -p 'test_*.py' -v
& $python -m unittest discover -s tests -p 'test_*.py' -v
& $python scripts/verify_release.py --root . --expected-version 2.1.0
git diff --check main...HEAD
git status --short
```

### Step 2: Run complete ledger verification

```powershell
& $node C:\Users\10481\Documents\Skill\personal-expense-ledger\node_modules\typescript\bin\tsc -p tsconfig.json
& $node --test 'tests/typescript/*.test.mjs'
$env:PATH = 'C:\Users\10481\.cache\codex-runtimes\codex-primary-runtime\dependencies\python;' + $env:PATH
& $node scripts/run-python-tests.mjs
git diff --check main...HEAD
git status --short
```

### Step 3: Build and inspect local artifacts

Build the router `image-intake-router-2.1.0.tgz` and ledger `personal-expense-ledger-0.3.0.tgz` using repository scripts. Verify each checksum and archive allowlist. Extract each into a new temporary directory and run its smoke validation without referencing the source tree.

Do not delete or overwrite previous-version assets.

### Step 4: Review against the design

Use `superpowers:verification-before-completion` and `superpowers:requesting-code-review`. Check every success criterion in the design spec and record fresh command output.

### Step 5: Prepare GitHub handoff

Only after local verification:

- push both `codex/` branches;
- create ready pull requests targeting each repository's `main`;
- wait for checks and address failures;
- do not tag or publish a Release until the merged `main` commit, tag, workflow, assets, and checksums can be proven identical.

Final reporting must distinguish local implementation, pushed branches, PR state, merged commits, tags, and public Release assets. Never claim a stage that has not actually completed.
