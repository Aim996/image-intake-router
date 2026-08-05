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
