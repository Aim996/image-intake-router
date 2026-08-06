import json
import re
import unittest
from pathlib import Path


VERSION_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = VERSION_ROOT / "image-intake-router"
SKILL = SKILL_ROOT / "SKILL.md"
REFERENCES = SKILL_ROOT / "references"
SCHEMA = SKILL_ROOT / "templates" / "image-intake-router.schema.json"

EXPECTED_REFERENCES = {
    "references/calculation-rules.md",
    "references/confirmation-and-execution.md",
    "references/openclaw-handoff.md",
    "references/output-contract.md",
    "references/recognition-rules.md",
    "references/vision-runtime.md",
}


class ProductContractTests(unittest.TestCase):
    def read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8").replace("\r\n", "\n")

    def test_required_product_files_exist(self) -> None:
        required = [
            VERSION_ROOT / "项目说明.md",
            VERSION_ROOT / "后续迭代计划.md",
            VERSION_ROOT / "约束文档.md",
            SKILL,
            *(SKILL_ROOT / path for path in EXPECTED_REFERENCES),
            SCHEMA,
        ]
        self.assertEqual([str(path) for path in required if not path.is_file()], [])
        for removed in ["projection-contracts.md", "failure-recovery.md"]:
            self.assertFalse((REFERENCES / removed).exists(), removed)

    def test_skill_is_a_recognition_preview_and_openclaw_handoff(self) -> None:
        skill = self.read(SKILL)
        for phrase in [
            "one initial visual pass",
            "at most one targeted refinement pass",
            "three-section preview",
            "zero handoffs on the image turn",
            "hand confirmed content back to OpenClaw",
            "never inspect or modify a downstream repository",
        ]:
            self.assertIn(phrase, skill)

    def test_output_contract_lists_detailed_business_sections(self) -> None:
        content = self.read(REFERENCES / "output-contract.md")
        for phrase in [
            "【入账内容】",
            "【入库内容】",
            "【需要注意】",
            "list every visible recognized product",
            "name, quantity, specification or weight, and line paid amount",
            "请核实以上内容，回复“确认”后执行。",
        ]:
            self.assertIn(phrase, content)
        self.assertNotIn("one or two business sentences", content)
        self.assertNotIn("full details only on request", content)

    def test_confirmation_hands_off_once_and_never_executes_downstream_itself(self) -> None:
        content = self.read(REFERENCES / "confirmation-and-execution.md")
        for phrase in [
            "initial image message",
            "zero business handoffs",
            "later affirmative reply",
            "确认", "可以", "没问题", "执行", "就这样",
            "只记账", "只入库",
            "invalidate the prior preview",
            "zero new handoffs",
        ]:
            self.assertIn(phrase, content)
        self.assertIn("OpenClaw owns downstream Skill invocation", content)

    def test_runtime_allows_only_one_targeted_refinement(self) -> None:
        runtime = self.read(REFERENCES / "vision-runtime.md")
        rules = self.read(REFERENCES / "recognition-rules.md")
        for phrase in [
            "pass_count",
            "0, 1, or 2",
            "never exceeds 2",
            "targeted refinement",
            "visible-field omission",
        ]:
            self.assertIn(phrase, runtime)
        for phrase in [
            "约 2.1kg",
            "重量误差 228g",
            "自动退款 ¥12.92",
            "does not trigger refinement",
        ]:
            self.assertIn(phrase, rules)

    def test_recognition_rules_never_treat_attachment_metadata_as_facts(self) -> None:
        runtime = self.read(REFERENCES / "vision-runtime.md")
        for phrase in [
            "Attachment filenames",
            "description text",
            "cannot establish image business facts",
        ]:
            self.assertIn(phrase, runtime)

    def test_skill_references_only_existing_local_files(self) -> None:
        content = self.read(SKILL)
        targets = set(re.findall(r"\]\((references/[^)]+\.md)\)", content))
        self.assertEqual(targets, EXPECTED_REFERENCES)
        for removed in ["projection-contracts.md", "failure-recovery.md"]:
            self.assertNotIn(f"references/{removed}", targets)
            self.assertFalse((REFERENCES / removed).exists(), removed)


class RouterV3ProtocolContractTests(unittest.TestCase):
    def read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8").replace("\r\n", "\n")

    def test_schema_exposes_only_recognition_preview_and_handoff(self) -> None:
        schema = json.loads(self.read(SCHEMA))
        self.assertEqual(schema["properties"]["schema_version"]["const"], "image-intake-router.v3")
        self.assertEqual(
            set(schema["required"]),
            {
                "schema_version", "preview_id", "preview_state", "source",
                "recognition_run", "cleaned_text", "facts", "accounting_content",
                "inventory_content", "warnings", "handoff",
            },
        )
        self.assertNotIn("expense_projection", schema["properties"])
        self.assertNotIn("diet_projection", schema["properties"])
        self.assertNotIn("handoffs", schema["properties"])
        self.assertIn("accountingContent", schema["$defs"])
        self.assertIn("inventoryContent", schema["$defs"])
        self.assertIn("handoff", schema["$defs"])

    def test_recognition_run_caps_targeted_refinement_at_two_passes(self) -> None:
        defs = json.loads(self.read(SCHEMA))["$defs"]
        self.assertIn("recognitionRun", defs)
        self.assertIn("refinementRun", defs)
        run = defs["recognitionRun"]
        self.assertIn("pass_count", run["properties"])
        self.assertIn("refinement", run["properties"])
        self.assertTrue({"pass_count", "refinement"}.issubset(run["required"]))
        self.assertEqual(run["properties"]["pass_count"]["minimum"], 0)
        self.assertEqual(run["properties"]["pass_count"]["maximum"], 2)
        refinement = defs["refinementRun"]
        self.assertTrue(
            {"status", "reason", "targeted_fields", "attachment_indexes"}.issubset(
                refinement["required"]
            )
        )
        self.assertEqual(
            refinement["properties"]["status"]["enum"],
            ["not_applicable", "not_needed", "succeeded", "partial", "failed"],
        )
        self.assertEqual(refinement["properties"]["attachment_indexes"]["uniqueItems"], True)

    def test_schema_keeps_recognition_and_fact_records_strict_and_evidenced(self) -> None:
        schema = json.loads(self.read(SCHEMA))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        defs = schema["$defs"]
        for name in ["facts", "textFact", "amountFact", "quantityFact", "itemFact"]:
            self.assertIn(name, defs)
            self.assertFalse(defs[name]["additionalProperties"])
        for name in ["textFact", "amountFact", "quantityFact", "itemFact"]:
            fact = defs[name]
            self.assertIn("evidence", fact["properties"])
            self.assertTrue(
                fact["properties"]["evidence"].get("minItems") == 1
                or any(
                    guard.get("then", {}).get("properties", {}).get("evidence", {}).get(
                        "minItems"
                    )
                    == 1
                    for guard in fact.get("allOf", [])
                ),
                f"{name} must require evidence for a known value",
            )

    def test_schema_preserves_exact_attachment_coverage_constraints(self) -> None:
        recognition = json.loads(self.read(SCHEMA))["$defs"]["recognitionRun"]
        self.assertTrue(
            {"attachment_count", "processed_attachment_count", "attachments"}.issubset(
                recognition["required"]
            )
        )
        attachment = json.loads(self.read(SCHEMA))["$defs"]["recognitionAttachment"]
        self.assertTrue({"attachment_index", "status"}.issubset(attachment["required"]))
        self.assertEqual(attachment["properties"]["attachment_index"]["minimum"], 0)


if __name__ == "__main__":
    unittest.main()
