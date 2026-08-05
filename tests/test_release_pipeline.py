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
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertEqual(checksum.read_text(encoding="utf-8"), f"{digest}  {archive.name}\n")
            with tarfile.open(archive, "r:gz") as tar:
                names = tar.getnames()
            self.assertTrue(all(name.startswith("image-intake-router-2.0.0/") for name in names))

    def test_requested_version_must_match_version_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "does not match VERSION"):
                build_release(ROOT, Path(directory), requested_version="2.0.1")
