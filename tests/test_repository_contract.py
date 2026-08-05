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
        self.assertIn("permissions:\n  contents: read", ci)
        self.assertIn(
            "uses: actions/checkout@v4\n        with:\n          persist-credentials: false",
            release,
        )
