# image-intake-router 2.0.0 Open-Source Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `image-intake-router` 2.0.0 into a public, MIT-licensed OpenClaw project with a reproducible prebuilt archive, checksum, safe installation and update documentation, tag-driven GitHub Actions, and a verified GitHub Release.

**Architecture:** Keep the Markdown Skill and JSON Schema as the runtime product. Add a Python-standard-library release layer that builds an allowlisted deterministic tarball and independently verifies its checksum, members, extraction safety, and isolated installation. Keep source-only tests and scripts outside the release archive; let a tag workflow create the Release only after all gates pass.

**Tech Stack:** OpenClaw Skill Markdown, JSON Schema 2020-12, Python 3.11+ standard library, `unittest`, Git, GitHub Actions, GitHub CLI available on hosted runners.

## Global Constraints

- Product version is exactly `2.0.0`; Git tag is exactly `v2.0.0`.
- Protocol version remains exactly `image-intake-router.v2`; a SemVer patch does not rewrite the protocol identifier.
- Release assets are exactly `image-intake-router-2.0.0.tgz` and `image-intake-router-2.0.0.tgz.sha256`.
- Runtime archive root is exactly `image-intake-router-2.0.0/`.
- Runtime archive includes no `.git`, `.github`, source tests, build scripts, caches, logs, databases, backups, secrets, credentials, tokens, raw images, or local configuration.
- Project has no persistent data, database, migration, or backup directory; do not invent one.
- Do not modify the personal expense ledger, personal diet pantry, their databases, or their repositories.
- Do not automatically enable this Skill or disable `food-image-intake` in a live OpenClaw installation.
- Use MIT License with copyright `2026 Aim996`.
- Do not create, move, or overwrite an existing `v2.0.0` tag or Release.
- Repository becomes Public only after the Release and both assets are independently verified.

---

## File Responsibility Map

- `VERSION`: sole machine-readable product SemVer.
- `README.md`: ordinary-user overview with Release-first install and safety guidance.
- `LICENSE`: MIT license text.
- `CHANGELOG.md`: user-visible 2.0.0 Added/Changed/Fixed/Security record.
- `RELEASE_NOTES.md`: exact notes consumed by the tag workflow.
- `docs/INSTALL.md`: Release installation and real OpenClaw acceptance.
- `docs/UPGRADING.md`: fixed-version update and rollback without touching downstream data.
- `docs/AI-PROMPTS.md`: three copy-ready AI prompts.
- `image-intake-router/SKILL.md`: runtime entry; adds product version metadata without changing behavior.
- `.gitignore`: excludes sensitive/local/build artifacts while allowing source and release definitions.
- `scripts/build_release.py`: version validation, runtime allowlist, deterministic tarball, checksum.
- `scripts/verify_release.py`: checksum, archive safety, member, Schema, reference, and isolated-install verification.
- `tests/test_repository_contract.py`: version, documentation, license, ignore, and workflow text contracts.
- `tests/test_release_pipeline.py`: build and verification behavior tests.
- `.github/workflows/ci.yml`: source validation on pushes and pull requests.
- `.github/workflows/release.yml`: tag-only build, verify, and GitHub Release creation.

---

### Task 1: Lock Repository, Version, Documentation, and License Contracts

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_repository_contract.py`
- Create: `VERSION`
- Create: `LICENSE`
- Create: `CHANGELOG.md`
- Create: `RELEASE_NOTES.md`
- Create: `docs/INSTALL.md`
- Create: `docs/UPGRADING.md`
- Create: `docs/AI-PROMPTS.md`
- Modify: `README.md`
- Modify: `项目说明.md`
- Modify: `.gitignore`
- Modify: `image-intake-router/SKILL.md`

**Interfaces:**
- Consumes: current repository root and existing 2.0.0 Skill contract.
- Produces: `VERSION == "2.0.0"`, complete public documentation, MIT license, and stable headings used by later build tests.

- [ ] **Step 1: Write failing repository contract tests**

Create an empty `tests/__init__.py`, then create `tests/test_repository_contract.py` with these concrete assertions:

```python
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8").replace("\r\n", "\n")

    def test_release_files_exist(self) -> None:
        required = [
            "VERSION", "LICENSE", "CHANGELOG.md", "RELEASE_NOTES.md",
            "docs/INSTALL.md", "docs/UPGRADING.md", "docs/AI-PROMPTS.md",
        ]
        self.assertEqual([name for name in required if not (ROOT / name).is_file()], [])

    def test_version_is_consistent(self) -> None:
        self.assertEqual(self.read("VERSION"), "2.0.0\n")
        for path in ["README.md", "项目说明.md", "CHANGELOG.md", "RELEASE_NOTES.md"]:
            self.assertIn("2.0.0", self.read(path), path)
        self.assertIn("version: 2.0.0", self.read("image-intake-router/SKILL.md"))

    def test_docs_cover_required_operations(self) -> None:
        expected = {
            "README.md": ["GitHub Release", "数据保存位置", "回滚", "MIT"],
            "docs/INSTALL.md": ["SHA-256", "OpenClaw", "真实验收", "food-image-intake"],
            "docs/UPGRADING.md": ["更新前", "固定版本", "回滚", "未修改数据库"],
            "docs/AI-PROMPTS.md": ["全新安装提示词", "安全更新提示词", "安装验收提示词"],
        }
        for path, phrases in expected.items():
            text = self.read(path)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{path}: {phrase}")

    def test_license_and_changelog_are_release_ready(self) -> None:
        license_text = self.read("LICENSE")
        self.assertIn("MIT License", license_text)
        self.assertIn("Copyright (c) 2026 Aim996", license_text)
        changelog = self.read("CHANGELOG.md")
        for heading in ["Added", "Changed", "Fixed", "Security"]:
            self.assertRegex(changelog, rf"(?m)^### {heading}$")
        self.assertIn("不涉及数据库结构变化", changelog)

    def test_gitignore_covers_local_and_sensitive_artifacts(self) -> None:
        text = self.read(".gitignore")
        for pattern in [".env", "*.sqlite", "*.db", "backups/", "dist/", "coverage/"]:
            self.assertIn(pattern, text)

    def test_public_docs_have_no_developer_machine_path(self) -> None:
        project_doc = self.read("项目说明.md")
        self.assertNotRegex(project_doc, r"[A-Za-z]:\\")
        self.assertNotIn("暂存副本", project_doc)
```

- [ ] **Step 2: Run the new tests and confirm the red state**

Run:

```powershell
python -m unittest tests.test_repository_contract -v
```

Expected: failures for missing `VERSION`, `LICENSE`, CHANGELOG, release notes, and docs.

- [ ] **Step 3: Add exact version and MIT license**

Create `VERSION` containing exactly:

```text
2.0.0
```

Create `LICENSE` using the standard MIT terms beginning with:

```text
MIT License

Copyright (c) 2026 Aim996
```

and including the complete permission grant and warranty disclaimer.

- [ ] **Step 4: Add public release documentation**

Write the four documents with these exact top-level headings:

```markdown
# Changelog
## [2.0.0] - 2026-08-05
### Added
### Changed
### Fixed
### Security
```

```markdown
# image-intake-router 2.0.0 Release Notes
## 安装
## 更新
## 数据与迁移
## 已知限制
## 回滚
```

```markdown
# 安装 image-intake-router
## 系统要求
## 从 GitHub Release 安装
## OpenClaw 配置与重载
## 真实验收
## 常见错误
```

```markdown
# 更新与回滚 image-intake-router
## 更新前检查
## 下载固定版本
## 安装新版本
## 健康检查
## 回滚
## 数据安全结论
```

`docs/AI-PROMPTS.md` must contain the exact headings `全新安装提示词`, `安全更新提示词`, and `安装验收提示词`, and every prompt must prohibit modifying unrelated projects or claiming success from shell output alone.

- [ ] **Step 5: Rewrite README as a Release-first guide and strengthen ignore rules**

README sections must be:

```markdown
# image-intake-router
## 主要功能
## 当前稳定版本
## 系统要求
## 最简单的安装方法
## 使用示例
## 更新方法
## 数据保存位置与数据安全
## 备份与恢复
## 常见问题
## 开发者验证
## License
```

Extend `.gitignore` with `.env`, `.env.*`, `*.sqlite`, `*.sqlite3`, `*.db`, `backups/`, `dist/`, `build/`, `coverage/`, `.coverage`, temporary archives, and local configuration patterns. Do not ignore `.github`, `scripts`, `docs`, or `image-intake-router/templates`.

Rewrite `项目说明.md` so that it no longer contains a developer-machine absolute path or describes the repository as a staging copy. Keep the product architecture and constraints, but make GitHub Release installation the public default and link to `docs/INSTALL.md` and `docs/UPGRADING.md`.

Add this product metadata under `metadata.openclaw` in `image-intake-router/SKILL.md`:

```yaml
    version: 2.0.0
```

- [ ] **Step 6: Run repository and existing Skill contracts**

Run:

```powershell
python -m unittest tests.test_repository_contract -v
python image-intake-router\tests\test_static_contract.py -v
python -m json.tool image-intake-router\templates\image-intake-router.schema.json
```

Expected: repository tests pass, existing 12 Skill tests pass, Schema parse exits 0.

- [ ] **Step 7: Commit Task 1**

```powershell
git add VERSION LICENSE CHANGELOG.md RELEASE_NOTES.md README.md 项目说明.md .gitignore docs/INSTALL.md docs/UPGRADING.md docs/AI-PROMPTS.md image-intake-router/SKILL.md tests/__init__.py tests/test_repository_contract.py
git commit -m "docs: prepare image intake router 2.0.0 release"
```

---

### Task 2: Build a Deterministic Allowlisted Release Archive

**Files:**
- Create: `scripts/__init__.py`
- Create: `scripts/build_release.py`
- Create: `tests/test_release_pipeline.py`

**Interfaces:**
- Consumes: repository `VERSION` and files created by Task 1.
- Produces: `read_version(root: Path) -> str`, pure `release_members() -> tuple[Path, ...]`, validating `runtime_members(root: Path) -> tuple[Path, ...]`, and `build_release(root: Path, output_dir: Path, requested_version: str | None = None) -> tuple[Path, Path]`.

- [ ] **Step 1: Write failing build tests**

Create `tests/test_release_pipeline.py` with:

```python
import gzip
import hashlib
import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from scripts.build_release import build_release, read_version, runtime_members

ROOT = Path(__file__).resolve().parents[1]


class ReleaseBuildTests(unittest.TestCase):
    def test_read_version_is_exact(self) -> None:
        self.assertEqual(read_version(ROOT), "2.0.0")

    def test_runtime_allowlist_excludes_source_only_files(self) -> None:
        names = {path.as_posix() for path in runtime_members(ROOT)}
        self.assertIn("image-intake-router/SKILL.md", names)
        self.assertIn("image-intake-router/templates/image-intake-router.schema.json", names)
        self.assertNotIn("image-intake-router/tests/test_static_contract.py", names)
        self.assertFalse(any(name.startswith("scripts/") for name in names))
        self.assertFalse(any(name.startswith(".github/") for name in names))

    def test_build_has_fixed_name_root_and_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive, checksum = build_release(ROOT, Path(directory))
            self.assertEqual(archive.name, "image-intake-router-2.0.0.tgz")
            self.assertEqual(checksum.name, archive.name + ".sha256")
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertEqual(checksum.read_text(encoding="utf-8"), f"{digest}  {archive.name}\n")
            with tarfile.open(archive, "r:gz") as tar:
                names = tar.getnames()
            self.assertTrue(all(name.startswith("image-intake-router-2.0.0/") for name in names))

    def test_requested_version_must_match_version_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "does not match VERSION"):
                build_release(ROOT, Path(directory), requested_version="2.0.1")
```

- [ ] **Step 2: Run build tests and confirm import failure**

Run:

```powershell
python -m unittest tests.test_release_pipeline -v
```

Expected: FAIL because `scripts.build_release` does not exist.

- [ ] **Step 3: Implement version validation and runtime allowlist**

In `scripts/build_release.py`, implement the allowlist and builder as follows; add the standard imports for `argparse`, `gzip`, `hashlib`, `io`, `re`, `tarfile`, and `Path`:

```python
PROJECT_NAME = "image-intake-router"
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
ROOT_FILES = ("VERSION", "README.md", "LICENSE", "CHANGELOG.md")
DOC_FILES = ("docs/INSTALL.md", "docs/UPGRADING.md", "docs/AI-PROMPTS.md")
REFERENCE_FILES = (
    "confirmation-protocol.md",
    "diet-adapter.md",
    "expense-adapter.md",
    "intent-routing.md",
    "unified-facts.md",
    "validation.md",
)


def read_version(root: Path) -> str:
    text = (root / "VERSION").read_text(encoding="utf-8")
    version = text.strip()
    if text.replace("\r\n", "\n") != f"{version}\n":
        raise ValueError("VERSION must contain one version and one trailing newline")
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"invalid VERSION: {version!r}")
    return version


def release_members() -> tuple[Path, ...]:
    members = [Path(name) for name in (*ROOT_FILES, *DOC_FILES)]
    members.append(Path(PROJECT_NAME, "SKILL.md"))
    members.extend(Path(PROJECT_NAME, "references", name) for name in REFERENCE_FILES)
    members.append(Path(PROJECT_NAME, "templates", "image-intake-router.schema.json"))
    return tuple(sorted(members, key=lambda path: path.as_posix()))


def runtime_members(root: Path) -> tuple[Path, ...]:
    members = release_members()
    missing = [path.as_posix() for path in members if not (root / path).is_file()]
    if missing:
        raise FileNotFoundError("missing release files: " + ", ".join(missing))
    return members


def build_release(
    root: Path,
    output_dir: Path,
    requested_version: str | None = None,
) -> tuple[Path, Path]:
    root = root.resolve()
    version = read_version(root)
    if requested_version is not None and requested_version != version:
        raise ValueError(f"requested version {requested_version} does not match VERSION {version}")

    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"{PROJECT_NAME}-{version}.tgz"
    checksum = output_dir / f"{archive.name}.sha256"
    prefix = f"{PROJECT_NAME}-{version}"

    with archive.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as gzip_file:
            with tarfile.open(fileobj=gzip_file, mode="w") as tar:
                for relative in runtime_members(root):
                    data = (root / relative).read_bytes()
                    info = tarfile.TarInfo(f"{prefix}/{relative.as_posix()}")
                    info.size = len(data)
                    info.uid = info.gid = 0
                    info.uname = info.gname = "root"
                    info.mtime = 0
                    info.mode = 0o644
                    tar.addfile(info, io.BytesIO(data))

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8", newline="\n")
    return archive, checksum
```

`release_members` is the single exact allowlist shared with the verifier without reading the source tree. `runtime_members` must fail if any expected file is missing and must never enumerate arbitrary repository files into the archive.

- [ ] **Step 4: Implement deterministic tar and SHA-256 generation**

The implementation above writes files in sorted archive-name order. Keep these normalized `TarInfo` values as a tested contract:

```python
info.uid = 0
info.gid = 0
info.uname = "root"
info.gname = "root"
info.mtime = 0
info.mode = 0o644
```

Use `gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0)` around `tarfile.open(fileobj=gzip_file, mode="w")`. Write checksum text as lowercase SHA-256, two spaces, filename, newline. Add a CLI supporting `--root`, `--output-dir`, and `--version`.

- [ ] **Step 5: Run build tests and inspect archive members**

Run:

```powershell
python -m unittest tests.test_release_pipeline.ReleaseBuildTests -v
python -m scripts.build_release --root . --output-dir dist --version 2.0.0
python -c "import tarfile; print('\n'.join(tarfile.open('dist/image-intake-router-2.0.0.tgz').getnames()))"
```

Expected: tests pass; member list contains only the approved runtime and documentation files beneath one versioned root.

- [ ] **Step 6: Commit Task 2**

```powershell
git add scripts/__init__.py scripts/build_release.py tests/test_release_pipeline.py
git commit -m "build: add deterministic release archive"
```

---

### Task 3: Verify Archives and Perform Isolated Installation Smoke Tests

**Files:**
- Create: `scripts/verify_release.py`
- Modify: `tests/test_release_pipeline.py`

**Interfaces:**
- Consumes: Task 2 archive and checksum.
- Produces: immutable `VerificationReport(version: str, archive_sha256: str, member_count: int, installed_skill: Path)` and `verify_release(archive: Path, checksum: Path, install_root: Path) -> VerificationReport`.

- [ ] **Step 1: Add failing verifier tests**

Append tests that:

```python
from scripts.verify_release import verify_release

    def test_verified_archive_installs_without_source_tree(self) -> None:
        with tempfile.TemporaryDirectory() as output, tempfile.TemporaryDirectory() as install:
            archive, checksum = build_release(ROOT, Path(output))
            report = verify_release(archive, checksum, Path(install))
            self.assertEqual(report.version, "2.0.0")
            self.assertTrue((report.installed_skill / "SKILL.md").is_file())
            self.assertTrue((report.installed_skill / "templates/image-intake-router.schema.json").is_file())

    def test_checksum_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as output, tempfile.TemporaryDirectory() as install:
            archive, checksum = build_release(ROOT, Path(output))
            checksum.write_text("0" * 64 + f"  {archive.name}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                verify_release(archive, checksum, Path(install))

    def test_path_traversal_member_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as output, tempfile.TemporaryDirectory() as install:
            archive = Path(output) / "image-intake-router-2.0.0.tgz"
            payload = b"escape"
            with tarfile.open(archive, "w:gz") as tar:
                info = tarfile.TarInfo("image-intake-router-2.0.0/../escape.txt")
                info.size = len(payload)
                tar.addfile(info, io.BytesIO(payload))
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            checksum = Path(output) / f"{archive.name}.sha256"
            checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsafe archive member"):
                verify_release(archive, checksum, Path(install))
```

- [ ] **Step 2: Run verifier tests and confirm the red state**

Run:

```powershell
python -m unittest tests.test_release_pipeline -v
```

Expected: FAIL because `scripts.verify_release` is missing.

- [ ] **Step 3: Implement checksum and archive-safety validation**

In `scripts/verify_release.py`, add imports for `hashlib`, `json`, `re`, `shutil`, `tarfile`, `tempfile`, `dataclass`, `Path`, and `PurePosixPath`, then implement:

```python
from scripts.build_release import PROJECT_NAME, release_members


@dataclass(frozen=True)
class VerificationReport:
    version: str
    archive_sha256: str
    member_count: int
    installed_skill: Path


def _archive_version(archive: Path) -> str:
    match = re.fullmatch(
        rf"{re.escape(PROJECT_NAME)}-([0-9]+\.[0-9]+\.[0-9]+)\.tgz",
        archive.name,
    )
    if match is None:
        raise ValueError(f"invalid archive filename: {archive.name}")
    return match.group(1)


def _verified_digest(archive: Path, checksum: Path) -> str:
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    line = checksum.read_text(encoding="utf-8").rstrip("\n")
    fields = line.split("  ", maxsplit=1)
    if fields != [digest, archive.name]:
        raise ValueError("checksum mismatch")
    return digest


def _validated_members(tar: tarfile.TarFile, version: str) -> list[tarfile.TarInfo]:
    prefix = f"{PROJECT_NAME}-{version}"
    expected = {f"{prefix}/{path.as_posix()}" for path in release_members()}
    members = tar.getmembers()
    names: list[str] = []
    for member in members:
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe archive member: {member.name}")
        if not member.isfile() or member.issym() or member.islnk():
            raise ValueError(f"unsafe archive member type: {member.name}")
        if not path.parts or path.parts[0] != prefix:
            raise ValueError(f"wrong archive root: {member.name}")
        names.append(member.name)
    if len(names) != len(set(names)) or set(names) != expected:
        raise ValueError("archive member set does not match release allowlist")
    return members


def _safe_extract(
    tar: tarfile.TarFile,
    members: list[tarfile.TarInfo],
    extraction_root: Path,
) -> None:
    extraction_root = extraction_root.resolve()
    for member in members:
        target = (extraction_root / PurePosixPath(member.name)).resolve()
        if target != extraction_root and extraction_root not in target.parents:
            raise ValueError(f"unsafe archive member: {member.name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        source = tar.extractfile(member)
        if source is None:
            raise ValueError(f"unreadable archive member: {member.name}")
        target.write_bytes(source.read())


def _smoke_check(installed_skill: Path, version: str) -> None:
    skill_text = (installed_skill / "SKILL.md").read_text(encoding="utf-8")
    if re.search(r"(?m)^name:\s*image-intake-router\s*$", skill_text) is None:
        raise ValueError("installed SKILL.md has wrong name")
    if re.search(rf"(?m)^\s*version:\s*{re.escape(version)}\s*$", skill_text) is None:
        raise ValueError("installed SKILL.md has wrong version")
    references = sorted(set(re.findall(r"\]\((references/[^)#]+)", skill_text)))
    if not references:
        raise ValueError("installed SKILL.md has no reference links")
    missing = [name for name in references if not (installed_skill / name).is_file()]
    if missing:
        raise ValueError("missing installed references: " + ", ".join(missing))
    schema_path = installed_skill / "templates" / "image-intake-router.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema_version = schema["properties"]["schema_version"]["const"]
    if schema_version != "image-intake-router.v2":
        raise ValueError(f"unexpected schema version: {schema_version}")


def verify_release(archive: Path, checksum: Path, install_root: Path) -> VerificationReport:
    version = _archive_version(archive)
    digest = _verified_digest(archive, checksum)
    with tempfile.TemporaryDirectory() as directory:
        extraction_root = Path(directory)
        with tarfile.open(archive, "r:gz") as tar:
            members = _validated_members(tar, version)
            _safe_extract(tar, members, extraction_root)
        source_skill = extraction_root / f"{PROJECT_NAME}-{version}" / PROJECT_NAME
        installed_skill = install_root / "skills" / PROJECT_NAME
        installed_skill.parent.mkdir(parents=True, exist_ok=True)
        if installed_skill.exists():
            raise FileExistsError(f"install target already exists: {installed_skill}")
        shutil.copytree(source_skill, installed_skill)

    _smoke_check(installed_skill, version)
    return VerificationReport(version, digest, len(members), installed_skill)
```

The verifier must use pure `release_members()` for the expected set, never `runtime_members(root)`, so archive validation and installed smoke checks do not read the repository source tree. Keep the explicit rejections for absolute paths, `..`, non-regular members, wrong roots, duplicates, and allowlist differences.

- [ ] **Step 4: Implement manual safe extraction and smoke checks**

Do not use unchecked `extractall`. For each validated regular file, resolve the destination and confirm it remains under the extraction root before copying its bytes. Then copy the extracted `image-intake-router/` to `install_root / "skills" / "image-intake-router"`.

Smoke checks must:

- parse `SKILL.md` frontmatter name and version,
- resolve every Markdown reference linked from `SKILL.md`,
- parse the JSON Schema,
- assert Schema `schema_version` is `image-intake-router.v2`,
- assert no source directory path is read after installation.

Add a CLI:

```powershell
python -m scripts.verify_release --archive dist/image-intake-router-2.0.0.tgz --checksum dist/image-intake-router-2.0.0.tgz.sha256 --install-root build/smoke
```

- [ ] **Step 5: Run positive and negative verifier tests**

Run:

```powershell
python -m unittest tests.test_release_pipeline -v
python -m scripts.verify_release --archive dist/image-intake-router-2.0.0.tgz --checksum dist/image-intake-router-2.0.0.tgz.sha256 --install-root build/smoke
```

Expected: all tests pass; CLI prints version, SHA-256, member count, and installed Skill path.

- [ ] **Step 6: Commit Task 3**

```powershell
git add scripts/verify_release.py tests/test_release_pipeline.py
git commit -m "test: verify release archive and isolated install"
```

---

### Task 4: Add CI and Tag-Driven GitHub Release Workflows

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/release.yml`
- Modify: `tests/test_repository_contract.py`

**Interfaces:**
- Consumes: Task 1 metadata and Task 2–3 commands.
- Produces: PR/push CI and a tag workflow that creates a Release only after successful verification.

- [ ] **Step 1: Add failing workflow contract tests**

Extend repository tests:

```python
    def test_ci_and_release_workflows_gate_publication(self) -> None:
        ci = self.read(".github/workflows/ci.yml")
        release = self.read(".github/workflows/release.yml")
        required_commands = [
            "tests.test_repository_contract",
            "image-intake-router/tests/test_static_contract.py",
            "tests.test_release_pipeline",
            "scripts.build_release",
            "scripts.verify_release",
        ]
        for workflow in [ci, release]:
            for command in required_commands:
                self.assertIn(command, workflow)
        self.assertIn("tags:", release)
        self.assertIn("'v*'", release)
        self.assertIn("contents: write", release)
        self.assertIn("gh release create", release)
        self.assertIn("RELEASE_NOTES.md", release)
        self.assertIn("dist/*.tgz", release)
        self.assertIn("dist/*.sha256", release)
        self.assertNotIn("continue-on-error: true", release)
        self.assertIn("pull_request:", ci)
```

- [ ] **Step 2: Run workflow contract test and confirm missing-file failure**

Run:

```powershell
python -m unittest tests.test_repository_contract.RepositoryContractTests.test_ci_and_release_workflows_gate_publication -v
```

Expected: FAIL because workflows are missing.

- [ ] **Step 3: Implement `.github/workflows/ci.yml`**

Trigger on `push` to `main` and `codex/**`, plus all pull requests. Use `actions/checkout@v4`, `actions/setup-python@v5` with Python `3.12`, then run repository contracts, existing Skill tests, Schema parse, release pipeline tests, build, and verifier CLI.

- [ ] **Step 4: Implement `.github/workflows/release.yml`**

Use:

```yaml
name: Release
on:
  push:
    tags:
      - 'v*'
permissions:
  contents: write
```

The shell must derive `VERSION_FROM_TAG="${GITHUB_REF_NAME#v}"`, compare it byte-for-byte with `VERSION`, run every test and build command, then execute:

```bash
if gh release view "$GITHUB_REF_NAME" >/dev/null 2>&1; then
  echo "Release already exists: $GITHUB_REF_NAME" >&2
  exit 1
fi
gh release create "$GITHUB_REF_NAME" \
  dist/*.tgz dist/*.sha256 \
  --title "image-intake-router $VERSION_FROM_TAG" \
  --notes-file RELEASE_NOTES.md
```

Set `GH_TOKEN: ${{ github.token }}` only on the release-creation step.

- [ ] **Step 5: Run workflow and source contracts locally**

Run:

```powershell
python -m unittest tests.test_repository_contract -v
python -m unittest tests.test_release_pipeline -v
git diff --check
```

Expected: PASS and no whitespace errors.

- [ ] **Step 6: Commit Task 4**

```powershell
git add .github/workflows/ci.yml .github/workflows/release.yml tests/test_repository_contract.py
git commit -m "ci: publish verified release assets from tags"
```

---

### Task 5: Run the Complete Local Release Gate

**Files:**
- Verify: all tracked project files
- Generate but do not commit: `dist/image-intake-router-2.0.0.tgz`
- Generate but do not commit: `dist/image-intake-router-2.0.0.tgz.sha256`
- Generate but do not commit: `build/smoke/`

**Interfaces:**
- Consumes: complete source tree and release scripts.
- Produces: locally verified release assets and exact SHA-256 for GitHub comparison.

- [ ] **Step 1: Run formatting, contracts, unit tests, and Schema validation**

Run:

```powershell
git diff --check
python -m unittest tests.test_repository_contract -v
python -m unittest tests.test_release_pipeline -v
python image-intake-router\tests\test_static_contract.py -v
python -m json.tool image-intake-router\templates\image-intake-router.schema.json
```

Expected: every command exits 0. Type checking is not applicable because the project has no configured type checker; record it as not applicable.

- [ ] **Step 2: Prove deterministic builds**

Build twice into separate temporary output directories:

```powershell
python -m scripts.build_release --root . --output-dir build/repro-a --version 2.0.0
python -m scripts.build_release --root . --output-dir build/repro-b --version 2.0.0
```

Compare SHA-256 of both `.tgz` files and require equality.

- [ ] **Step 3: Build final assets and verify archive contents**

Run:

```powershell
python -m scripts.build_release --root . --output-dir dist --version 2.0.0
python -m scripts.verify_release --archive dist/image-intake-router-2.0.0.tgz --checksum dist/image-intake-router-2.0.0.tgz.sha256 --install-root build/smoke
```

List all tar members and confirm no source tests, scripts, workflow, cache, data, or credential artifact exists.

- [ ] **Step 4: Scan tracked files and assets for forbidden material**

Search tracked and archive member names for `.env`, database extensions, `node_modules`, caches, logs, backups, raw image extensions, private keys, tokens, local absolute user paths, and `.git`. Intentional installation examples may use generic placeholders such as `$OPENCLAW_SKILLS_DIR`, never an actual user home path.

- [ ] **Step 5: Verify Git state and commit any final release-only corrections**

Run:

```powershell
git status --short
git diff --check
git ls-files
```

`dist/` and `build/` must be ignored. If a release-only correction was required, stage only project files, rerun the complete gate, and commit with:

```powershell
git commit -m "fix: close image router release gate"
```

---

### Task 6: Publish Branch, Merge to Main, and Create the Version Tag

**Files:**
- No source edits expected.
- Push: `codex/release-image-intake-router-2.0.0`
- Update: remote `main`
- Create: annotated tag `v2.0.0`

**Interfaces:**
- Consumes: clean, fully verified release branch and local asset digest.
- Produces: remote main commit and immutable release tag.

- [ ] **Step 1: Confirm tag and Release do not already exist**

Run local and remote tag checks:

```powershell
git tag --list v2.0.0
git ls-remote --tags origin refs/tags/v2.0.0
```

Both outputs must be empty. In the authenticated GitHub UI, confirm there is no `v2.0.0` Release. If any exists, stop without changing it.

- [ ] **Step 2: Push the release branch**

```powershell
git push -u origin codex/release-image-intake-router-2.0.0
```

Verify the remote branch head equals the local head.

- [ ] **Step 3: Fast-forward local main and push it**

With a clean working tree:

```powershell
git switch main
git merge --ff-only codex/release-image-intake-router-2.0.0
git push origin main
```

Rerun the complete local release gate on `main`. Do not delete the release branch until the GitHub Release is verified.

- [ ] **Step 4: Create and push the annotated tag**

```powershell
git tag -a v2.0.0 -m "image-intake-router 2.0.0"
git push origin v2.0.0
```

Record the tagged commit SHA and verify it equals remote `main`.

---

### Task 7: Verify GitHub Actions, Release Assets, and Public Visibility

**Files:**
- No local source edits expected.
- Verify remote workflow run, Release, assets, and visibility.

**Interfaces:**
- Consumes: pushed `v2.0.0` tag.
- Produces: public GitHub repository and verified formal Release.

- [ ] **Step 1: Wait for the tag workflow to finish**

Open the repository Actions page in the authenticated GitHub browser. Locate the workflow run whose ref is `v2.0.0`. Wait until it reaches a terminal state. If it fails, preserve the failed state, diagnose the first failing job, and do not report a release.

- [ ] **Step 2: Verify Release metadata and assets**

Open `https://github.com/Aim996/image-intake-router/releases/tag/v2.0.0` and confirm:

- title is `image-intake-router 2.0.0`,
- notes include install, update, data/migration, known limitations, and rollback,
- assets include exactly `image-intake-router-2.0.0.tgz` and `image-intake-router-2.0.0.tgz.sha256` in addition to GitHub-generated source archives.

- [ ] **Step 3: Download and independently verify assets**

Download both custom assets to a fresh temporary directory through the authenticated browser. Compute SHA-256 of the downloaded `.tgz`, parse the downloaded `.sha256`, require equality, and run `scripts.verify_release` against the downloaded files with a fresh install root.

- [ ] **Step 4: Change repository visibility to Public**

Only after Steps 1–3 pass, use repository Settings to change `Aim996/image-intake-router` from Private to Public. Confirm the repository page displays `Public`, MIT License is visible, README renders, and the Release remains accessible.

- [ ] **Step 5: Final Git and data-safety audit**

Confirm:

- local and remote `main` commit SHA match,
- tag `v2.0.0` points to that commit,
- local working tree has no tracked changes,
- no database, migration, backup, user data, secret, log, cache, or raw image was committed or published,
- database modification: none,
- database migration: none,
- project backup directory: none,
- user data deleted: none.

- [ ] **Step 6: Report the formal release**

Provide repository URL, branch, commit SHA, `v2.0.0`, Release URL, asset names, SHA-256, supported OpenClaw/Python environments, install/update/rollback summaries, data-safety facts, every executed check and result, unverified items, and the exact created/modified/deleted file list.
