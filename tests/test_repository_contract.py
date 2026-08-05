import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8").replace("\r\n", "\n")

    def _assert_release_workflow_contract(self, ci: str, release: str) -> None:
        def steps(workflow: str) -> list[tuple[str, str]]:
            return re.findall(
                r"(?ms)^      - ([^\n]+)\n(.*?)(?=^      - |\Z)", workflow
            )

        def named_step(step_list: list[tuple[str, str]], name: str) -> str:
            matches = [body for header, body in step_list if header == f"name: {name}"]
            self.assertEqual(len(matches), 1, name)
            return matches[0]

        def action_reference(header: str, body: str) -> str:
            references = []
            direct = re.fullmatch(
                r"uses: (actions/[A-Za-z0-9._/-]+@[0-9a-f]{40})(?: # [^\n]+)?",
                header,
            )
            if direct:
                references.append(direct.group(1))
            references.extend(
                re.findall(
                    r"(?m)^        uses: (actions/[A-Za-z0-9._/-]+@[0-9a-f]{40})(?: # [^\n]+)?$",
                    body,
                )
            )
            self.assertEqual(len(references), 1, header)
            return references[0]

        def action_steps(step_list: list[tuple[str, str]]) -> list[tuple[str, str]]:
            return [
                step
                for step in step_list
                if step[0].startswith("uses: ")
                or re.search(r"(?m)^        uses: ", step[1])
            ]

        def permission_map(job_text: str) -> dict[str, str]:
            match = re.search(
                r"(?m)^    permissions:\n((?:      [A-Za-z-]+: [^\n]+\n)+)",
                job_text,
            )
            self.assertIsNotNone(match)
            entries = re.findall(r"(?m)^      ([A-Za-z-]+): ([^\n]+)$", match.group(1))
            self.assertEqual(len(entries), len({key for key, _ in entries}))
            return dict(entries)

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

        expected_ci_actions = [
            "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
            "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
        ]
        expected_release_actions = expected_ci_actions + [
            "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
            "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093",
        ]
        self.assertCountEqual(
            [action_reference(*step) for step in action_steps(steps(ci))],
            expected_ci_actions,
        )
        self.assertCountEqual(
            [action_reference(*step) for step in action_steps(steps(release))],
            expected_release_actions,
        )

        self.assertIn("tags:", release)
        self.assertIn("'v*'", release)
        self.assertRegex(release, r"(?m)^permissions: \{\}$")
        verify, *publish_parts = release.split("\n  publish:", 1)
        self.assertEqual(len(publish_parts), 1, "release workflow must split verify and publish")
        publish = publish_parts[0]
        self.assertIn("\n  verify:", verify)
        self.assertEqual(permission_map(verify), {"contents": "read"})
        self.assertNotIn("GH_TOKEN", verify)
        self.assertIn("needs: verify", publish)
        self.assertEqual(
            permission_map(publish),
            {"actions": "read", "contents": "write"},
        )
        self.assertEqual(release.count("contents: write"), 1)
        self.assertEqual(release.count("GH_TOKEN"), 1)

        verify_steps = steps(verify)
        publish_steps = steps(publish)
        self.assertEqual(
            [header for header, _ in publish_steps],
            ["name: Download verified release artifact", "name: Create GitHub Release"],
        )
        create_step = named_step(publish_steps, "Create GitHub Release")
        self.assertEqual(publish_steps[-1][0], "name: Create GitHub Release")
        token_steps = [header for header, body in publish_steps if "GH_TOKEN" in body]
        self.assertEqual(token_steps, ["name: Create GitHub Release"])
        self.assertRegex(
            create_step,
            r"(?m)^        env:\n          GH_TOKEN: \$\{\{ github\.token \}\}$",
        )

        upload_step = named_step(verify_steps, "Upload verified release artifact")
        self.assertIn("name: verified-release", upload_step)
        self.assertIn("path: |\n            dist/\n            RELEASE_NOTES.md", upload_step)
        self.assertIn("if-no-files-found: error", upload_step)
        self.assertIn("retention-days: 1", upload_step)
        download_step = named_step(publish_steps, "Download verified release artifact")
        self.assertIn("name: verified-release", download_step)
        self.assertIn("path: verified-release", download_step)

        self.assertIn('ARCHIVE="verified-release/dist/image-intake-router-$VERSION_FROM_TAG.tgz"', create_step)
        self.assertIn('CHECKSUM="$ARCHIVE.sha256"', create_step)
        self.assertIn('NOTES="verified-release/RELEASE_NOTES.md"', create_step)
        self.assertIn(
            "mapfile -t DIST_FILES < <(find verified-release/dist -type f -printf '%P\\n' | sort)",
            create_step,
        )
        self.assertIn(
            'EXPECTED_FILES=(\n            "image-intake-router-$VERSION_FROM_TAG.tgz"\n'
            '            "image-intake-router-$VERSION_FROM_TAG.tgz.sha256"\n          )',
            create_step,
        )
        mismatch_branch = re.search(
            r'(?ms)^          if \[ "\$\{DIST_FILES\[\*\]\}" != "\$\{EXPECTED_FILES\[\*\]\}" \]; then\n'
            r"(?P<body>.*?)^          fi$",
            create_step,
        )
        self.assertIsNotNone(mismatch_branch)
        self.assertRegex(mismatch_branch.group("body"), r"(?m)^            exit 1$")
        self.assertIn(
            'gh release create "$GITHUB_REF_NAME" \\\n            "$ARCHIVE" "$CHECKSUM" \\\n            --title "image-intake-router $VERSION_FROM_TAG" \\\n            --notes-file "$NOTES"',
            create_step,
        )
        self.assertNotIn("*.tgz", create_step)
        self.assertNotIn("*.sha256", create_step)
        self.assertIn("gh release view", create_step)
        self.assertIn("Release already exists", create_step)
        self.assertNotIn("continue-on-error: true", release)
        self.assertIn("pull_request:", ci)
        self.assertIn("permissions:\n  contents: read", ci)
        self.assertIn("persist-credentials: false", verify)

    def test_release_files_exist(self) -> None:
        required = [
            "VERSION", "LICENSE", "CHANGELOG.md", "RELEASE_NOTES.md",
            "docs/INSTALL.md", "docs/UPGRADING.md", "docs/AI-PROMPTS.md",
        ]
        self.assertEqual([name for name in required if not (ROOT / name).is_file()], [])

    def test_version_is_consistent(self) -> None:
        self.assertEqual(self.read("VERSION"), "2.1.0\n")
        for path in ["README.md", "项目说明.md", "CHANGELOG.md", "RELEASE_NOTES.md"]:
            self.assertIn("2.1.0", self.read(path), path)
        self.assertIn("version: 2.1.0", self.read("image-intake-router/SKILL.md"))

    def test_v2_1_docs_preserve_v2_0_1_rollback_and_media_safety_contract(self) -> None:
        combined = "\n".join(
            self.read(path)
            for path in [
                "README.md", "项目说明.md", "后续迭代计划.md", "约束文档.md",
                "CHANGELOG.md", "RELEASE_NOTES.md", "docs/INSTALL.md",
                "docs/UPGRADING.md", "docs/AI-PROMPTS.md",
            ]
        )
        for phrase in [
            "2.1.0", "2.0.1", "image-intake-router.v2.1",
            "https://github.com/openclaw/openclaw/blob/main/docs/nodes/media-understanding.md",
            "https://docs.openclaw.ai/tools/media-overview",
            "tools.media.image.attachments.mode: \"all\"", "maxAttachments",
            "真实视觉", "失败关闭", "一次业务确认", "不猜测", "原图",
        ]:
            self.assertIn(phrase, combined, phrase)

        for path in ["项目说明.md", "后续迭代计划.md", "约束文档.md"]:
            self.assertTrue((ROOT / path).is_file(), path)

    def test_install_docs_name_exact_assets_platforms_and_layout(self) -> None:
        readme = self.read("README.md")
        install = self.read("docs/INSTALL.md")
        for phrase in [
            "image-intake-router-2.1.0.tgz",
            "image-intake-router-2.1.0.tgz.sha256",
        ]:
            self.assertIn(phrase, readme + install)
        for phrase in [
            "Windows PowerShell",
            "Linux",
            "NAS",
            "Get-FileHash",
            "sha256sum -c",
            "image-intake-router-2.1.0/image-intake-router/",
            "<OPENCLAW_SKILLS_DIR>",
        ]:
            self.assertIn(phrase, install)
        self.assertNotIn("(RELEASE_NOTES.md)", readme)

    def test_docs_cover_required_operations(self) -> None:
        expected = {
            "README.md": ["Data boundary", "rollback", "MIT"],
            "docs/INSTALL.md": ["SHA-256", "OpenClaw", "业务级 UAT", "food-image-intake"],
            "docs/UPGRADING.md": ["更新", "2.1.0", "回滚", "数据库"],
            "docs/AI-PROMPTS.md": ["全新安装提示词", "安全更新提示词", "UAT 提示词"],
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
        self._assert_release_workflow_contract(ci, release)

    def test_release_contract_rejects_action_sha_comment_decoys(self) -> None:
        ci = self.read(".github/workflows/ci.yml")
        release = self.read(".github/workflows/release.yml")
        expected_pins = {
            "upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
            "download-artifact": "d3f86a106a0bac45b974a628896c90dbdf5c8093",
        }
        for action, expected_pin in expected_pins.items():
            with self.subTest(action=action):
                mutated = release.replace(
                    f"uses: actions/{action}@{expected_pin} # v4",
                    f"uses: actions/{action}@{'0' * 40} # actions/{action}@{expected_pin} # v4",
                )
                with self.assertRaises(AssertionError):
                    self._assert_release_workflow_contract(ci, mutated)

    def test_release_contract_rejects_token_in_unnamed_step_after_create(self) -> None:
        ci = self.read(".github/workflows/ci.yml")
        release = self.read(".github/workflows/release.yml")
        token = "        env:\n          GH_TOKEN: ${{ github.token }}\n"
        mutated = release.replace(token, "", 1).replace(
            '            --notes-file "$NOTES"\n',
            '            --notes-file "$NOTES"\n      - run: echo "unexpected token step"\n'
            "        env:\n          GH_TOKEN: ${{ github.token }}\n",
            1,
        )
        with self.assertRaises(AssertionError):
            self._assert_release_workflow_contract(ci, mutated)

    def test_release_contract_rejects_permission_expansion(self) -> None:
        ci = self.read(".github/workflows/ci.yml")
        release = self.read(".github/workflows/release.yml")
        mutations = {
            "verify": (
                "      contents: read\n    runs-on:",
                "      contents: read\n      issues: write\n    runs-on:",
            ),
            "publish": (
                "      contents: write\n    runs-on:",
                "      contents: write\n      issues: write\n    runs-on:",
            ),
        }
        for job, (original, replacement) in mutations.items():
            with self.subTest(job=job):
                mutated = release.replace(original, replacement, 1)
                with self.assertRaises(AssertionError):
                    self._assert_release_workflow_contract(ci, mutated)

    def test_release_contract_rejects_dist_mismatch_without_exit(self) -> None:
        ci = self.read(".github/workflows/ci.yml")
        release = self.read(".github/workflows/release.yml")
        mismatch_branch = (
            '          if [ "${DIST_FILES[*]}" != "${EXPECTED_FILES[*]}" ]; then\n'
            '            echo "Verified release artifact has unexpected dist files" >&2\n'
            "            exit 1\n"
            "          fi\n"
        )
        mutated = release.replace(
            mismatch_branch,
            mismatch_branch.replace("            exit 1\n", ""),
            1,
        )
        with self.assertRaises(AssertionError):
            self._assert_release_workflow_contract(ci, mutated)
