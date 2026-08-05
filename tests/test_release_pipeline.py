import gzip
import hashlib
import io
import shutil
import tarfile
import tempfile
import unittest
from pathlib import Path

from scripts.build_release import build_release, read_version, runtime_members
from scripts.verify_release import verify_release

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

    def test_runtime_allowlist_uses_repository_reference_files(self) -> None:
        names = {path.as_posix() for path in runtime_members(ROOT)}
        self.assertTrue(
            {
                "image-intake-router/references/calculation-rules.md",
                "image-intake-router/references/confirmation-and-execution.md",
                "image-intake-router/references/failure-recovery.md",
                "image-intake-router/references/output-contract.md",
                "image-intake-router/references/projection-contracts.md",
                "image-intake-router/references/recognition-rules.md",
            }.issubset(names)
        )

    def test_build_has_fixed_name_root_and_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive, checksum = build_release(ROOT, Path(directory))
            self.assertEqual(archive.name, "image-intake-router-2.0.0.tgz")
            self.assertEqual(checksum.name, archive.name + ".sha256")
            first_archive_bytes = archive.read_bytes()
            second_archive, second_checksum = build_release(ROOT, Path(directory))
            self.assertEqual(second_archive.read_bytes(), first_archive_bytes)
            self.assertEqual(second_checksum, checksum)
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertEqual(checksum.read_text(encoding="utf-8"), f"{digest}  {archive.name}\n")
            with tarfile.open(archive, "r:gz") as tar:
                members = tar.getmembers()
            names = [member.name for member in members]
            prefix = "image-intake-router-2.0.0"
            expected_names = [f"{prefix}/{path.as_posix()}" for path in runtime_members(ROOT)]
            self.assertEqual(names, expected_names)
            self.assertEqual(names, sorted(names))
            self.assertEqual(len(names), 15)
            self.assertEqual(
                {name for name in names if "/references/" in name},
                {
                    f"{prefix}/image-intake-router/references/calculation-rules.md",
                    f"{prefix}/image-intake-router/references/confirmation-and-execution.md",
                    f"{prefix}/image-intake-router/references/failure-recovery.md",
                    f"{prefix}/image-intake-router/references/output-contract.md",
                    f"{prefix}/image-intake-router/references/projection-contracts.md",
                    f"{prefix}/image-intake-router/references/recognition-rules.md",
                },
            )
            self.assertNotIn(f"{prefix}/image-intake-router/tests/test_static_contract.py", names)
            self.assertFalse(any(name.startswith(f"{prefix}/scripts/") for name in names))
            self.assertFalse(any(name.startswith(f"{prefix}/.github/") for name in names))
            for member in members:
                self.assertEqual((member.uid, member.gid, member.mtime), (0, 0, 0))
                self.assertEqual((member.uname, member.gname, member.mode), ("root", "root", 0o644))

    def test_missing_allowlist_file_does_not_overwrite_existing_release_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture_root = Path(directory) / "fixture"
            shutil.copytree(ROOT, fixture_root, ignore=shutil.ignore_patterns("dist", "__pycache__"))
            (fixture_root / "README.md").unlink()
            output_dir = Path(directory) / "output"
            output_dir.mkdir()
            archive = output_dir / "image-intake-router-2.0.0.tgz"
            checksum = output_dir / f"{archive.name}.sha256"
            original_archive = b"existing archive"
            original_checksum = "existing checksum\n"
            archive.write_bytes(original_archive)
            checksum.write_text(original_checksum, encoding="utf-8", newline="\n")

            with self.assertRaisesRegex(FileNotFoundError, "missing release files: README.md"):
                build_release(fixture_root, output_dir)

            self.assertEqual(archive.read_bytes(), original_archive)
            self.assertEqual(checksum.read_text(encoding="utf-8"), original_checksum)

    def test_requested_version_must_match_version_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "does not match VERSION"):
                build_release(ROOT, Path(directory), requested_version="2.0.1")

    def test_verified_archive_installs_without_source_tree(self) -> None:
        with tempfile.TemporaryDirectory() as output, tempfile.TemporaryDirectory() as install:
            archive, checksum = build_release(ROOT, Path(output))
            report = verify_release(archive, checksum, Path(install))
            self.assertEqual(report.version, "2.0.0")
            self.assertTrue((report.installed_skill / "SKILL.md").is_file())
            self.assertTrue(
                (report.installed_skill / "templates/image-intake-router.schema.json").is_file()
            )

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
