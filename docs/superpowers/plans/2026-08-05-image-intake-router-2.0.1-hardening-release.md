# image-intake-router 2.0.1 Hardening Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish an immutable `v2.0.1` patch release that closes every Critical/Important/Minor finding from the final `v2.0.0` review without changing the image-routing protocol or downstream data.

**Architecture:** Preserve the 15-member, standard-library-only release format and harden its two trust boundaries: source files entering the deterministic builder and archive files entering the isolated verifier. Put exact cross-platform install instructions in public docs, isolate GitHub Release write permission in a dependent publication job, and publish only after task reviews plus a whole-branch review are clean.

**Tech Stack:** OpenClaw Skill Markdown, JSON Schema 2020-12, Python 3.11+ standard library, `unittest`, Git, GitHub Actions, GitHub Release.

## Global Constraints

- Existing public tag and Release `v2.0.0` are immutable: do not move, overwrite, delete, replace, or edit their assets.
- New product version is exactly `2.0.1`; new annotated tag is exactly `v2.0.1`.
- Protocol identifier remains exactly `image-intake-router.v2`.
- Release custom assets are exactly `image-intake-router-2.0.1.tgz` and `image-intake-router-2.0.1.tgz.sha256`.
- Runtime archive root is exactly `image-intake-router-2.0.1/` and contains the same exact 15 allowlisted regular UTF-8 text files as 2.0.0.
- The six governing reference files remain `calculation-rules.md`, `confirmation-and-execution.md`, `failure-recovery.md`, `output-contract.md`, `projection-contracts.md`, and `recognition-rules.md`; do not rename, copy, or replace them.
- Python release tooling remains standard-library-only; do not add PyYAML or another runtime dependency.
- Do not add a database, migration, backup directory, user data, raw images, credentials, tokens, logs, caches, or local configuration.
- Do not enable the Skill or change a live OpenClaw installation.
- No force push, branch overwrite, tag movement, Release overwrite, or deletion.
- GitHub action pins resolved from the official action repositories on 2026-08-05 are: checkout `11d5960a326750d5838078e36cf38b85af677262`, setup-python `a26af69be951a213d495a4c3e4e4022e16d87065`, upload-artifact `ea165f8d65b6e75b540449e92b4886f43607fa02`, and download-artifact `d3f86a106a0bac45b974a628896c90dbdf5c8093`.
- If GitHub Actions again fails before job startup because of the account billing lock, use only the already authorized draft-first official GitHub API fallback, then independently download and verify both public assets before marking the Release complete.

---

### Task 1: Set Version 2.0.1 and Make Installation Unambiguous

**Files:**
- Modify: `tests/test_repository_contract.py`
- Modify: `VERSION`
- Modify: `image-intake-router/SKILL.md`
- Modify: `README.md`
- Modify: `项目说明.md`
- Modify: `CHANGELOG.md`
- Modify: `RELEASE_NOTES.md`
- Modify: `docs/INSTALL.md`
- Modify: `docs/UPGRADING.md`
- Modify: `docs/AI-PROMPTS.md`

**Interfaces:**
- Consumes: immutable 2.0.0 history and the existing Release-first documentation structure.
- Produces: `VERSION == "2.0.1"`, matching Skill metadata and public documents, exact asset names, and platform-specific installation instructions used by later release gates.

- [ ] **Step 1: Write failing repository contract tests**

Change the version contract to require `2.0.1`, then add a test that requires the exact public release URL, exact asset names, wrapper layout, installable nested directory, and Windows/Linux/NAS verification guidance:

```python
    def test_install_docs_name_exact_assets_platforms_and_layout(self) -> None:
        readme = self.read("README.md")
        install = self.read("docs/INSTALL.md")
        for phrase in [
            "https://github.com/Aim996/image-intake-router/releases/tag/v2.0.1",
            "image-intake-router-2.0.1.tgz",
            "image-intake-router-2.0.1.tgz.sha256",
        ]:
            self.assertIn(phrase, readme + install)
        for phrase in [
            "Windows PowerShell",
            "Linux",
            "NAS",
            "Get-FileHash",
            "sha256sum -c",
            "image-intake-router-2.0.1/image-intake-router/",
            "<OPENCLAW_SKILLS_DIR>",
        ]:
            self.assertIn(phrase, install)
        self.assertNotIn("(RELEASE_NOTES.md)", readme)
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Run:

```powershell
python -m unittest tests.test_repository_contract.RepositoryContractTests.test_version_is_consistent tests.test_repository_contract.RepositoryContractTests.test_install_docs_name_exact_assets_platforms_and_layout -v
```

Expected: failures showing 2.0.0 and missing exact installation guidance.

- [ ] **Step 3: Update versioned product metadata and history**

Set `VERSION` to exactly `2.0.1\n` and `image-intake-router/SKILL.md` metadata version to `2.0.1`. Add a topmost `## [2.0.1] - 2026-08-05` changelog section that records:

- strict source-path and archive-version validation,
- strict supported frontmatter parsing,
- isolated workflow publication permissions and immutable action pins,
- exact cross-platform installation guidance,
- no protocol, Schema, database, migration, backup, or user-data change.

Keep the historical 2.0.0 section unchanged.

- [ ] **Step 4: Write exact Release-first installation documentation**

Use the absolute release URL `https://github.com/Aim996/image-intake-router/releases/tag/v2.0.1`. Name both custom assets exactly. Document this archive layout:

```text
image-intake-router-2.0.1/
├── VERSION
├── README.md
├── LICENSE
├── CHANGELOG.md
├── docs/
└── image-intake-router/
    ├── SKILL.md
    ├── references/
    └── templates/
```

State explicitly that only `image-intake-router-2.0.1/image-intake-router/` is the installable Skill directory. Use portable placeholder `<OPENCLAW_SKILLS_DIR>` and include these verification commands:

```powershell
Get-FileHash -Algorithm SHA256 .\image-intake-router-2.0.1.tgz
Get-Content .\image-intake-router-2.0.1.tgz.sha256
```

```bash
sha256sum -c image-intake-router-2.0.1.tgz.sha256
```

Add separate Windows PowerShell, Linux shell, and NAS guidance; NAS guidance must distinguish SSH/terminal extraction from a NAS GUI while preserving the wrapper/nested-directory rule. Replace README's relative `RELEASE_NOTES.md` link with the absolute v2.0.1 Release URL. Update `项目说明.md`, `docs/UPGRADING.md`, `docs/AI-PROMPTS.md`, and `RELEASE_NOTES.md` to 2.0.1 while retaining the no-database and rollback boundaries.

- [ ] **Step 5: Run repository and Skill contracts and confirm GREEN**

Run:

```powershell
python -m unittest tests.test_repository_contract -v
python image-intake-router\tests\test_static_contract.py -v
python -m json.tool image-intake-router\templates\image-intake-router.schema.json
```

Expected: all repository and Skill tests pass; Schema parses; protocol remains `image-intake-router.v2`.

- [ ] **Step 6: Commit Task 1**

Stage only the files listed for Task 1 and commit:

```powershell
git commit -m "docs: prepare image router 2.0.1"
```

---

### Task 2: Reject Symlinked or Escaping Builder Sources

**Files:**
- Modify: `tests/test_release_pipeline.py`
- Modify: `scripts/build_release.py`

**Interfaces:**
- Consumes: exact 15-member `release_members()` and version 2.0.1 fixtures from Task 1.
- Produces: `_validated_source_file(root: Path, relative: Path) -> Path`, used by both allowlist preflight and canonical payload reads.

- [ ] **Step 1: Write a failing real-symlink test**

Add `test_symlinked_release_source_does_not_overwrite_existing_assets`. Build a complete temporary release root, create both an outside UTF-8 file and pre-existing output assets, replace `README.md` with a symlink to the outside file, and require:

```python
with self.assertRaisesRegex(ValueError, "unsafe release source: README.md"):
    build_release(fixture_root, output_dir)
self.assertEqual(archive.read_bytes(), original_archive)
self.assertEqual(checksum.read_text(encoding="utf-8"), original_checksum)
```

Use `self.skipTest(...)` only if the current OS refuses creation of an actual symlink; Linux CI must execute the assertion. Add a second subtest whose `docs/` parent is a symlink to an outside directory and require an unsafe-source failure for an allowlisted doc.

- [ ] **Step 2: Run the focused test and confirm RED**

Run:

```powershell
python -m unittest tests.test_release_pipeline.ReleaseBuildTests.test_symlinked_release_source_does_not_overwrite_existing_assets -v
```

Expected: the current builder packages the outside content or reports a non-safety error instead of rejecting it.

- [ ] **Step 3: Implement one strict source-path validator**

Add `_validated_source_file` with these rules:

```python
def _validated_source_file(root: Path, relative: Path) -> Path:
    candidate = root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError(f"unsafe release source: {relative.as_posix()}")
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as error:
        raise FileNotFoundError(relative.as_posix()) from error
    if root not in resolved.parents or not resolved.is_file():
        raise ValueError(f"unsafe release source: {relative.as_posix()}")
    return candidate
```

`build_release` already resolves `root`; retain that invariant. Make `runtime_members` aggregate missing allowlisted files as before while propagating unsafe-source errors. Make `_canonical_text_bytes` call the same validator immediately before reading so validation is not bypassed by a separate read path. Preserve the preflight-before-output-mutation behavior.

- [ ] **Step 4: Run focused and complete release tests and confirm GREEN**

Run:

```powershell
python -m unittest tests.test_release_pipeline.ReleaseBuildTests.test_symlinked_release_source_does_not_overwrite_existing_assets -v
python -m unittest tests.test_release_pipeline -v
```

Expected: the new test and all release tests pass with no output mutation on rejection.

- [ ] **Step 5: Commit Task 2**

```powershell
git add scripts/build_release.py tests/test_release_pipeline.py
git commit -m "security: reject escaping release sources"
```

---

### Task 3: Strictly Verify Archive Version, Frontmatter, and Member Types

**Files:**
- Modify: `tests/test_release_pipeline.py`
- Modify: `scripts/verify_release.py`

**Interfaces:**
- Consumes: deterministic 2.0.1 archive and exact member allowlist.
- Produces: strict archive-root `VERSION` equality and a strict supported frontmatter mapping subset used by `_smoke_check`.

- [ ] **Step 1: Generalize the archive-member rewrite test helper**

Replace the Skill-specific helper with `_rewrite_member(archive, checksum, member_name, transform)` and keep `_rewrite_skill` as a thin call if it improves readability. The helper must rewrite the checksum after rebuilding the test archive.

- [ ] **Step 2: Write failing archive VERSION and frontmatter tests**

Add a test that rewrites `image-intake-router-2.0.1/VERSION` to `9.9.9\n`, recomputes the checksum, and requires `ValueError("archive VERSION does not match filename")` before any install directory is created.

Add a table-driven frontmatter test whose malformed inputs include:

```text
metadata: scalar
  openclaw:
    version: 2.0.1
```

and duplicate keys, a tab-indented key, a skipped indentation level, and a line without `:`. Every case must contain apparently matching `name` and `version` fields where applicable and still raise `ValueError("invalid SKILL.md frontmatter")`.

- [ ] **Step 3: Write failing tests for every archive-type rejection branch**

Add focused fixtures for an absolute member path, symlink, hardlink, directory/non-regular member, wrong root, and duplicate member. Require the existing error categories: `unsafe archive member`, `unsafe archive member type`, `wrong archive root`, or `archive member set does not match release allowlist` as appropriate. Remove the unused `gzip` import; retain `io`, which is used by real tar fixtures.

- [ ] **Step 4: Run the new tests and confirm RED**

Run the new VERSION, malformed-frontmatter, and archive-type tests by fully qualified unittest names. Expected: VERSION and malformed structural cases are accepted by the current verifier, demonstrating the defects; archive branch tests may already pass and serve as regression characterization.

- [ ] **Step 5: Validate the extracted root VERSION before installation**

After safe extraction and before `shutil.copytree`, strictly read `<extraction_root>/image-intake-router-<version>/VERSION` as UTF-8 and require its bytes to equal `f"{version}\n".encode("utf-8")`. Any decode or value mismatch raises `ValueError("archive VERSION does not match filename")`. Do not create the install target before this check succeeds.

- [ ] **Step 6: Replace the permissive frontmatter walker with a strict supported subset**

Retain standard-library-only parsing. For every nonblank, noncomment frontmatter line:

- reject tabs,
- require indentation in exact two-space increments,
- require a nonempty key matching `[A-Za-z0-9_-]+`,
- reject lines without `:`,
- reject duplicate full key paths,
- treat `key:` as a mapping parent and `key: value` as a scalar leaf,
- allow children only below a mapping parent,
- reject indentation skips and children below scalar leaves.

Return the same `dict[tuple[str, ...], str]` interface so `_smoke_check` continues to require top-level `name` and nested `metadata.openclaw.version`.

- [ ] **Step 7: Run focused and complete release tests and confirm GREEN**

Run:

```powershell
python -m unittest tests.test_release_pipeline -v
```

Expected: all builder/verifier positive and negative tests pass with pristine output.

- [ ] **Step 8: Commit Task 3**

```powershell
git add scripts/verify_release.py tests/test_release_pipeline.py
git commit -m "security: harden release verification"
```

---

### Task 4: Isolate Release Write Permission and Publish Exact Assets

**Files:**
- Modify: `tests/test_repository_contract.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/release.yml`

**Interfaces:**
- Consumes: Task 1 exact 2.0.1 filenames and the Task 2-3 build/verify commands.
- Produces: read-only verification job, dependent write-scoped publication job, immutable action pins, and exactly two explicit Release asset arguments.

- [ ] **Step 1: Write failing structural workflow contracts**

Require:

- immutable action SHAs from Global Constraints in both workflows,
- Release workflow-level `permissions: {}` or equivalent no-access default,
- one `verify` job with `contents: read`,
- one dependent `publish` job with exactly one occurrence of `contents: write`,
- `GH_TOKEN` appears exactly once and only in the release-creation step,
- explicit version-derived `.tgz` and `.tgz.sha256` arguments,
- no `dist/*.tgz` or `dist/*.sha256` globs,
- pinned upload/download artifact actions and `if-no-files-found: error`.

The contract should split the workflow text at `\n  publish:` and assert permission/token placement in the relevant half instead of relying only on repository-wide substring presence.

- [ ] **Step 2: Run the workflow contract and confirm RED**

Run:

```powershell
python -m unittest tests.test_repository_contract.RepositoryContractTests.test_ci_and_release_workflows_gate_publication -v
```

Expected: failure on workflow-level write permission, mutable action tags, absent job split, and glob assets.

- [ ] **Step 3: Pin CI actions**

Use:

```yaml
- uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
- uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5
```

Keep CI `contents: read` and all existing gates.

- [ ] **Step 4: Split Release verification and publication jobs**

Set workflow-level `permissions: {}`. The `verify` job has `contents: read`, performs checkout/setup/tests/build/verify, then uploads only `dist/` and `RELEASE_NOTES.md` as an internal artifact named `verified-release` using the pinned upload action, `if-no-files-found: error`, and a short retention period.

The `publish` job must:

```yaml
needs: verify
permissions:
  actions: read
  contents: write
```

It downloads `verified-release` with the pinned download action, derives `VERSION_FROM_TAG`, and defines these exact paths:

```bash
ARCHIVE="verified-release/dist/image-intake-router-$VERSION_FROM_TAG.tgz"
CHECKSUM="$ARCHIVE.sha256"
NOTES="verified-release/RELEASE_NOTES.md"
```

Require all three files, reject any custom file set other than the expected two files under `verified-release/dist`, fail if the Release already exists, and execute:

```bash
gh release create "$GITHUB_REF_NAME" \
  "$ARCHIVE" "$CHECKSUM" \
  --title "image-intake-router $VERSION_FROM_TAG" \
  --notes-file "$NOTES"
```

Set `GH_TOKEN: ${{ github.token }}` only on this final shell step.

- [ ] **Step 5: Run repository, release, Skill, Schema, and diff gates**

Run:

```powershell
python -m unittest tests.test_repository_contract -v
python -m unittest tests.test_release_pipeline -v
python image-intake-router\tests\test_static_contract.py -v
python -m json.tool image-intake-router\templates\image-intake-router.schema.json
git diff --check
```

Expected: all commands pass.

- [ ] **Step 6: Commit Task 4**

```powershell
git add .github/workflows/ci.yml .github/workflows/release.yml tests/test_repository_contract.py
git commit -m "ci: isolate image router release permissions"
```

---

### Task 5: Run the Complete 2.0.1 Local Release Gate

**Files:**
- Verify: all tracked project files.
- Generate but do not commit: `dist/image-intake-router-2.0.1.tgz` and `.sha256`.
- Generate but do not commit: isolated build/install/scan evidence under ignored `build/`.

**Interfaces:**
- Consumes: reviewed Tasks 1-4.
- Produces: canonical 2.0.1 asset SHA-256 and evidence required by final review and publication.

- [ ] **Step 1: Run all tests, Schema parse, and diff check**

Run repository contracts, release pipeline tests, Skill static contracts, JSON Schema parse, and `git diff --check`. Every command must exit zero.

- [ ] **Step 2: Prove cross-directory reproducibility**

Build from the feature worktree and a fresh checkout of the same commit into unique ignored directories. Require byte-identical `.tgz` files and identical `.sha256` contents.

- [ ] **Step 3: Build final assets and run isolated installation**

Build `dist/image-intake-router-2.0.1.tgz`, verify its checksum, require exactly 15 allowlisted members, and install into a fresh `build/` smoke root.

- [ ] **Step 4: Run forbidden-material scan**

Scan tracked filenames/content and every archive member filename/content for environment files, dependencies, caches, logs, databases, backups, raw images, keys, tokens, credentials, `.git`, and actual local-user paths. Four hit classes must be zero.

- [ ] **Step 5: Verify Git state**

Require a clean tracked worktree, ignored `build/` and `dist/`, and no database/migration/backup/user-data changes.

---

## Post-Implementation Review and Publication

After all five tasks have clean task reviews, run the mandatory whole-branch review against `995fb10f73905c3e403ffc32c59147ab63fae49c`. Fix all Critical/Important findings in one fix wave and run one scoped re-review. Do not publish until that review is clean.

Then, under the user's explicit authorization for the complete 2.0.1 release:

1. Reconfirm remote branch `codex/release-image-intake-router-2.0.1`, tag `v2.0.1`, and Release `v2.0.1` do not exist.
2. Ordinary-push the reviewed release branch, fast-forward `main`, and ordinary-push `main`; no force.
3. Re-run the full release gate on updated `main`.
4. Create an annotated `v2.0.1` pointing to the reviewed `main` commit and ordinary-push it.
5. Observe the tag workflow. If it cannot start because the known billing lock remains, create a draft Release through the authorized official API fallback, upload exactly the two custom assets, download and hash-verify both, publish the draft, and keep the already-public repository Public.
6. Independently download both assets from public URLs, require checksum equality and a 15-member isolated install, then verify the GitHub Release is Latest and points to the exact reviewed commit.

