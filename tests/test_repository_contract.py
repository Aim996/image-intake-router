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
        self.assertEqual(self.read("VERSION"), "2.0.1\n")
        for path in ["README.md", "项目说明.md", "CHANGELOG.md", "RELEASE_NOTES.md"]:
            self.assertIn("2.0.0", self.read(path), path)
        self.assertIn("version: 2.0.1", self.read("image-intake-router/SKILL.md"))

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
        for action in [
            "actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4",
            "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5",
        ]:
            self.assertIn(action, ci)
            self.assertIn(action, release)
        self.assertIn("tags:", release)
        self.assertIn("'v*'", release)
        self.assertIn("permissions: {}", release)
        self.assertIn(
            "actions/upload-artifact@65462800fd760344b1a7b4382951275a0abb4808 # v4",
            release,
        )
        self.assertIn(
            "actions/download-artifact@fa0a91b85d4f404e444e00e005971372dc801d16 # v4",
            release,
        )
        verify, *publish_parts = release.split("\n  publish:", 1)
        self.assertEqual(len(publish_parts), 1, "release workflow must split verify and publish")
        publish = publish_parts[0]
        self.assertIn("\n  verify:", verify)
        self.assertIn("permissions:\n      contents: read", verify)
        self.assertNotIn("contents: write", verify)
        self.assertNotIn("GH_TOKEN", verify)
        self.assertIn("needs: verify", publish)
        self.assertIn("permissions:\n      actions: read\n      contents: write", publish)
        self.assertEqual(release.count("contents: write"), 1)
        self.assertEqual(release.count("GH_TOKEN"), 1)
        self.assertIn("- name: Create GitHub Release", publish)
        release_step = publish.split("- name: Create GitHub Release", 1)[1]
        self.assertIn("GH_TOKEN: ${{ github.token }}", release_step)
        self.assertIn("name: verified-release", verify)
        self.assertIn("path: |\n            dist/\n            RELEASE_NOTES.md", verify)
        self.assertIn("if-no-files-found: error", verify)
        self.assertIn("retention-days: 1", verify)
        self.assertIn("name: verified-release", publish)
        self.assertIn('ARCHIVE="verified-release/dist/image-intake-router-$VERSION_FROM_TAG.tgz"', publish)
        self.assertIn('CHECKSUM="$ARCHIVE.sha256"', publish)
        self.assertIn('NOTES="verified-release/RELEASE_NOTES.md"', publish)
        self.assertIn('"$ARCHIVE" "$CHECKSUM"', publish)
        self.assertIn('--notes-file "$NOTES"', publish)
        self.assertNotIn("dist/*.tgz", release)
        self.assertNotIn("dist/*.sha256", release)
        self.assertIn("gh release view", publish)
        self.assertIn("Release already exists", publish)
        self.assertNotIn("continue-on-error: true", release)
        self.assertIn("pull_request:", ci)
        self.assertIn("permissions:\n  contents: read", ci)
        self.assertIn("persist-credentials: false", release)
