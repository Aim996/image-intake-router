import argparse
import hashlib
import json
import re
import shutil
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

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


def _frontmatter_values(skill_text: str) -> dict[tuple[str, ...], str]:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", skill_text, re.DOTALL)
    if match is None:
        raise ValueError("invalid SKILL.md frontmatter")

    values: dict[tuple[str, ...], str] = {}
    stack: list[tuple[str, bool]] = []
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line:
            raise ValueError("invalid SKILL.md frontmatter")
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2:
            raise ValueError("invalid SKILL.md frontmatter")
        level = indent // 2
        if level > len(stack):
            raise ValueError("invalid SKILL.md frontmatter")
        stack = stack[:level]
        if level and not stack[level - 1][1]:
            raise ValueError("invalid SKILL.md frontmatter")
        key, separator, value = line[indent:].partition(":")
        if not separator or re.fullmatch(r"[A-Za-z0-9_-]+", key) is None:
            raise ValueError("invalid SKILL.md frontmatter")
        path = tuple(name for name, _ in stack) + (key,)
        if path in values:
            raise ValueError("invalid SKILL.md frontmatter")
        value = value.strip()
        values[path] = value
        stack.append((key, not value))
    return values


def _expected_references() -> set[str]:
    return {
        path.relative_to(PROJECT_NAME).as_posix()
        for path in release_members()
        if path.parts[:2] == (PROJECT_NAME, "references")
    }


def _installed_regular_file(installed_skill: Path, relative: str) -> Path:
    relative_path = PurePosixPath(relative)
    if (
        relative_path.is_absolute()
        or ".." in relative_path.parts
        or not relative_path.parts
    ):
        raise ValueError(f"unsafe installed reference: {relative}")
    root = installed_skill.resolve()
    candidate = installed_skill / relative_path
    target = candidate.resolve()
    if target == root or root not in target.parents:
        raise ValueError(f"unsafe installed reference: {relative}")
    if candidate.is_symlink() or not target.is_file():
        raise ValueError(f"missing installed reference: {relative}")
    target.read_bytes()
    return target


def _smoke_check(installed_skill: Path, version: str) -> None:
    skill_path = _installed_regular_file(installed_skill, "SKILL.md")
    skill_text = skill_path.read_text(encoding="utf-8")
    frontmatter = _frontmatter_values(skill_text)
    if frontmatter.get(("name",)) != PROJECT_NAME:
        raise ValueError("installed SKILL.md has wrong name")
    if frontmatter.get(("metadata", "openclaw", "version")) != version:
        raise ValueError("installed SKILL.md has wrong version")
    references = set(re.findall(r"\]\((references/[^)#]+)", skill_text))
    for reference in references:
        _installed_regular_file(installed_skill, reference)
    if references != _expected_references():
        raise ValueError("installed reference set does not match release allowlist")
    schema_path = _installed_regular_file(
        installed_skill, "templates/image-intake-router.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema_version = schema["properties"]["schema_version"]["const"]
    if schema_version != "image-intake-router.v3.1":
        raise ValueError(f"unexpected schema version: {schema_version}")


def verify_release(archive: Path, checksum: Path, install_root: Path) -> VerificationReport:
    version = _archive_version(archive)
    digest = _verified_digest(archive, checksum)
    with tempfile.TemporaryDirectory() as directory:
        extraction_root = Path(directory)
        with tarfile.open(archive, "r:gz") as tar:
            members = _validated_members(tar, version)
            _safe_extract(tar, members, extraction_root)
        archive_root = extraction_root / f"{PROJECT_NAME}-{version}"
        version_bytes = (archive_root / "VERSION").read_bytes()
        try:
            version_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("archive VERSION does not match filename") from None
        if version_bytes != f"{version}\n".encode("utf-8"):
            raise ValueError("archive VERSION does not match filename")
        source_skill = archive_root / PROJECT_NAME
        installed_skill = install_root / "skills" / PROJECT_NAME
        installed_skill.parent.mkdir(parents=True, exist_ok=True)
        if installed_skill.exists():
            raise FileExistsError(f"install target already exists: {installed_skill}")
        shutil.copytree(source_skill, installed_skill)

    _smoke_check(installed_skill, version)
    return VerificationReport(version, digest, len(members), installed_skill)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify a release archive and install it for a smoke test."
    )
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--checksum", type=Path, required=True)
    parser.add_argument("--install-root", type=Path, required=True)
    args = parser.parse_args()
    report = verify_release(args.archive, args.checksum, args.install_root)
    print(f"version: {report.version}")
    print(f"sha256: {report.archive_sha256}")
    print(f"member count: {report.member_count}")
    print(f"installed skill: {report.installed_skill}")


if __name__ == "__main__":
    main()
