import json
import re
import unittest
from pathlib import Path


VERSION_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = VERSION_ROOT / "image-intake-router"
SKILL = SKILL_ROOT / "SKILL.md"
REFERENCES = SKILL_ROOT / "references"
SCHEMA = SKILL_ROOT / "templates" / "image-intake-router.schema.json"


class ProductContractTests(unittest.TestCase):
    def read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8").replace("\r\n", "\n")

    def test_required_product_files_exist(self) -> None:
        required = [
            VERSION_ROOT / "项目说明.md",
            VERSION_ROOT / "后续迭代计划.md",
            VERSION_ROOT / "约束文档.md",
            SKILL,
            REFERENCES / "recognition-rules.md",
            REFERENCES / "calculation-rules.md",
            REFERENCES / "projection-contracts.md",
            REFERENCES / "confirmation-and-execution.md",
            REFERENCES / "output-contract.md",
            REFERENCES / "failure-recovery.md",
            SCHEMA,
        ]
        self.assertEqual([str(path) for path in required if not path.is_file()], [])

    def test_skill_declares_single_pass_dual_preview_and_confirmation(self) -> None:
        content = self.read(SKILL)
        self.assertRegex(content, r"^---\nname: image-intake-router\n")
        for phrase in ["只识别一次", "默认.*两份", "确认", "只记账", "只入库", "consumed"]:
            self.assertRegex(content, phrase)
        self.assertNotIn("food-image-intake.v1.1", content)

    def test_confirmation_contract_consumes_only_latest_preview_once(self) -> None:
        content = self.read(REFERENCES / "confirmation-and-execution.md")
        for phrase in [
            "draft",
            "awaiting_confirmation",
            "executing",
            "consumed",
            "只记账",
            "只入库",
            "最近一次",
            "修改",
            "不得再次",
        ]:
            self.assertIn(phrase, content)

    def test_output_contract_uses_exact_dual_preview_titles_and_empty_domain_rules(self) -> None:
        content = self.read(REFERENCES / "output-contract.md")
        for phrase in [
            "💰 即将记入随手账：",
            "🥗 即将交给食序管家入库：",
            "仅展示存在的投影字段",
            "无可执行投影",
            "不执行",
            "不调用该域写工具",
        ]:
            self.assertIn(phrase, content)

    def test_schema_is_strict_and_namespaces_projections(self) -> None:
        schema = json.loads(self.read(SCHEMA))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["schema_version"]["const"], "image-intake-router.v2")
        self.assertFalse(schema["additionalProperties"])
        self.assertIn("expense_projection", schema["properties"])
        self.assertIn("diet_projection", schema["properties"])

    def test_schema_defines_strict_expense_and_diet_projections(self) -> None:
        schema = json.loads(self.read(SCHEMA))
        self.assertIn("$defs", schema)
        expense = schema["$defs"]["expenseProjection"]
        diet = schema["$defs"]["dietProjection"]
        self.assertFalse(expense["additionalProperties"])
        self.assertFalse(diet["additionalProperties"])
        self.assertEqual(
            expense["required"],
            [
                "executable",
                "amount",
                "category_id",
                "occurred_at",
                "source_kind",
                "merchant",
                "note",
                "issues",
            ],
        )
        self.assertIn("items", diet["required"])
        self.assertIn("excluded_items", diet["required"])
        self.assertIn("uncertain_items", diet["required"])

    def test_schema_mirrors_downstream_boundaries_and_retains_item_audit(self) -> None:
        schema = json.loads(self.read(SCHEMA))
        defs = schema["$defs"]
        expense = defs["expenseProjection"]
        pantry_item = defs["pantryAddItem"]
        diet = defs["dietProjection"]

        self.assertIn("maximum", expense["properties"]["amount"])
        self.assertEqual(expense["properties"]["amount"]["maximum"], 9_999_999_999.99)
        self.assertEqual(expense["properties"]["occurred_at"]["minLength"], 20)
        self.assertEqual(expense["properties"]["occurred_at"]["maxLength"], 40)
        executable_constraints = expense["allOf"][1]["then"]["properties"]
        self.assertEqual(executable_constraints["amount"]["maximum"], 9_999_999_999.99)
        self.assertEqual(executable_constraints["occurred_at"]["minLength"], 20)
        self.assertEqual(executable_constraints["occurred_at"]["maxLength"], 40)

        self.assertEqual(pantry_item["properties"]["expiry_date"]["format"], "date")
        self.assertIn("null", pantry_item["properties"]["expires_at"]["type"])
        self.assertEqual(pantry_item["properties"]["expires_at"]["maxLength"], 16 * 1024)
        self.assertEqual(
            pantry_item["oneOf"],
            [
                {"required": ["expiry_date"], "not": {"required": ["expires_at"]}},
                {"required": ["expires_at"], "not": {"required": ["expiry_date"]}},
            ],
        )

        self.assertIn("item_audit", diet["required"])
        audit = defs["itemAudit"]
        self.assertFalse(audit["additionalProperties"])
        self.assertEqual(audit["required"], ["item_index", "order_status", "evidence"])
        self.assertEqual(audit["properties"]["item_index"]["minimum"], 0)
        self.assertEqual(audit["properties"]["order_status"]["enum"], ["purchased_and_received"])
        self.assertEqual(audit["properties"]["evidence"]["minItems"], 1)
        self.assertEqual(audit["properties"]["evidence"]["items"]["$ref"], "#/$defs/evidenceRecord")
        self.assertEqual(pantry_item["properties"]["source_text"]["maxLength"], 240)
        self.assertEqual(pantry_item["properties"]["source_text"]["pattern"], "^[^\\r\\n]+$")

    def test_schema_requires_evidence_for_known_facts_and_complete_quality(self) -> None:
        schema = json.loads(self.read(SCHEMA))
        defs = schema["$defs"]
        for fact_name in ["textFact", "amountFact", "quantityFact"]:
            self.assertIn("allOf", defs[fact_name])
            constraint = defs[fact_name]["allOf"][0]
            self.assertEqual(constraint["then"]["properties"]["evidence"]["minItems"], 1)
        self.assertEqual(defs["itemFact"]["properties"]["evidence"]["minItems"], 1)
        complete_constraint = schema["allOf"][0]
        self.assertEqual(
            complete_constraint["if"]["properties"]["quality"]["properties"]["fact_set_status"]["const"],
            "complete",
        )
        self.assertEqual(
            complete_constraint["then"]["properties"]["facts"]["properties"]["unresolved_issues"]["maxItems"],
            0,
        )

    def test_item_audit_requires_purchased_and_received_status(self) -> None:
        schema = json.loads(self.read(SCHEMA))
        audit_status = schema["$defs"]["itemAudit"]["properties"]["order_status"]
        self.assertEqual(audit_status["enum"], ["purchased_and_received"])
        contract = self.read(REFERENCES / "projection-contracts.md")
        for phrase in [
            "purchased_and_received",
            "线下已完成购买",
            "已完成配送",
            "未送达",
            "仅下单",
            "仅付款",
            "uncertain_items",
        ]:
            self.assertIn(phrase, contract)

    def test_skill_references_only_existing_local_files(self) -> None:
        content = self.read(SKILL)
        targets = re.findall(r"\]\((references/[^)]+\.md)\)", content)
        self.assertGreaterEqual(len(targets), 6)
        self.assertEqual(
            [target for target in targets if not (SKILL_ROOT / target).is_file()],
            [],
        )

    def test_recognition_rules_cover_order_facts_and_overlap_dedup(self) -> None:
        content = self.read(REFERENCES / "recognition-rules.md")
        for phrase in [
            "实付",
            "商家",
            "订单状态",
            "商品名称",
            "规格",
            "重叠",
            "不得擅自合并",
            "visible_label",
            "user_text",
            "calculated",
            "reference_database",
            "visual_estimate",
        ]:
            self.assertIn(phrase, content)

    def test_recognition_rules_preserve_lower_ranked_evidence_source_semantics(self) -> None:
        content = self.read(REFERENCES / "recognition-rules.md")
        self.assertRegex(
            content,
            r"(?s)经用户允许使用的通用参考数据的 `reference_database`.*?"
            r"`reference_database` 只用于通用参考而非包装标签事实，"
            r"必须显式标注所用参考数据及其可追溯标识；"
            r"不得冒充 `visible_label`、`user_text` 或 `calculated`，也不得覆盖它们。",
        )
        self.assertRegex(
            content,
            r"`visual_estimate` 只可用于本规则允许的无标签生鲜或自制菜、外卖和成品餐的区间估算，"
            r"必须保留可见线索、假设、低值/中心值/高值范围和主要不确定性；"
            r"不得冒充或覆盖 `visible_label`、`user_text` 或 `calculated`。",
        )


if __name__ == "__main__":
    unittest.main()
