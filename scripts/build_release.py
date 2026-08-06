import argparse
import gzip
import hashlib
import io
import re
import tarfile
from pathlib import Path


PROJECT_NAME = "image-intake-router"
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
ROOT_FILES = ("VERSION", "README.md", "LICENSE", "CHANGELOG.md")
DOC_FILES = ("docs/INSTALL.md", "docs/UPGRADING.md", "docs/AI-PROMPTS.md")
REFERENCE_FILES = (
    "calculation-rules.md",
    "confirmation-and-execution.md",
    "failure-recovery.md",
    "output-contract.md",
    "projection-contracts.md",
    "recognition-rules.md",
    "vision-runtime.md",
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


def runtime_members(root: Path) -> tuple[Path, ...]:
    members = release_members()
    missing = []
    for path in members:
        try:
            _validated_source_file(root, path)
        except FileNotFoundError:
            missing.append(path.as_posix())
    if missing:
        raise FileNotFoundError("missing release files: " + ", ".join(missing))
    return members


def _canonical_text_bytes(root: Path, relative: Path) -> bytes:
    try:
        text = _validated_source_file(root, relative).read_bytes().decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"release file must be UTF-8: {relative.as_posix()}") from error
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def build_release(
    root: Path,
    output_dir: Path,
    requested_version: str | None = None,
) -> tuple[Path, Path]:
    root = root.resolve()
    version = read_version(root)
    if requested_version is not None and requested_version != version:
        raise ValueError(f"requested version {requested_version} does not match VERSION {version}")

    members = runtime_members(root)
    payloads = tuple((relative, _canonical_text_bytes(root, relative)) for relative in members)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"{PROJECT_NAME}-{version}.tgz"
    checksum = output_dir / f"{archive.name}.sha256"
    prefix = f"{PROJECT_NAME}-{version}"

    with archive.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as gzip_file:
            with tarfile.open(fileobj=gzip_file, mode="w") as tar:
                for relative, data in payloads:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a deterministic release archive.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    parser.add_argument("--version")
    args = parser.parse_args()
    build_release(args.root, args.output_dir, requested_version=args.version)


if __name__ == "__main__":
    main()
