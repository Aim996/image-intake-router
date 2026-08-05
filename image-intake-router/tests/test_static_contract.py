import json
import re
import unittest
from pathlib import Path


VERSION_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = VERSION_ROOT / "image-intake-router"
SKILL = SKILL_ROOT / "SKILL.md"
REFERENCES = SKILL_ROOT / "references"
SCHEMA = SKILL_ROOT / "templates" / "image-intake-router.schema.json"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PRODUCT_FACT_KEYS = {
    "full_name", "normalized_name", "specification", "purchase_quantity", "quantity_unit",
    "nominal_weight_or_volume", "actual_weight_or_volume", "billing_weight", "weight_variance",
    "original_amount", "unit_price", "line_paid_amount", "refund_amount", "production_date",
    "line_status", "item_type", "visibility_status",
}
ORDER_FACT_KEYS = {
    "merchant", "transaction_time", "order_status", "goods_subtotal", "activity_discount",
    "coupon_discount", "packaging_fee", "delivery_fee", "final_paid_amount", "refund_total",
    "declared_item_kind_count", "recognized_item_kind_count", "hidden_item_kind_count",
    "has_unexpanded_items", "content_complete",
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
        self.assertEqual(schema["properties"]["schema_version"]["const"], "image-intake-router.v2.1")
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


class RouterV21ProtocolContractTests(unittest.TestCase):
    """Contract tests for the v2.1 protocol introduced before its implementation."""

    def schema(self) -> dict:
        return json.loads(SCHEMA.read_text(encoding="utf-8"))

    def fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def test_schema_declares_v21_recognition_run(self) -> None:
        schema = self.schema()
        self.assertIn("recognition_run", schema["required"])
        self.assertIn("recognition_run", schema["properties"])

    def test_recognition_run_records_attachment_coverage_and_methods(self) -> None:
        defs = self.schema()["$defs"]
        self.assertTrue("recognitionRun" in defs, "v2.1 must define the recognition-run record")
        recognition = defs["recognitionRun"]
        self.assertEqual(
            recognition["properties"]["status"]["enum"],
            ["succeeded", "partial", "failed", "not_executed"],
        )
        self.assertEqual(
            recognition["properties"]["method"]["enum"],
            ["native_vision", "media_understanding"],
        )
        self.assertTrue({"attachment_count", "processed_attachment_count", "attachments", "issues"}.issubset(recognition["required"]))
        self.assertTrue("recognitionAttachment" in defs, "v2.1 must define per-attachment recognition details")
        attachment = defs["recognitionAttachment"]
        self.assertTrue({"status", "completeness", "limitations"}.issubset(attachment["required"]))

    def test_unsuccessful_recognition_blocks_executable_projections(self) -> None:
        rules = self.schema()["allOf"]
        guards = [
            rule for rule in rules
            if rule.get("if", {}).get("properties", {}).get("recognition_run", {}).get("properties", {}).get("status", {}).get("enum")
            == ["failed", "not_executed"]
        ]
        self.assertEqual(len(guards), 1, "v2.1 must gate failed and not-executed recognition")
        guard = guards[0]
        guarded = guard["then"]["properties"]
        self.assertEqual(guarded["quality"]["properties"]["fact_set_status"]["const"], "unavailable")
        for projection in ["expense_projection", "diet_projection"]:
            constraint = guarded[projection]
            self.assertTrue(
                constraint.get("type") == "null" or constraint.get("const", object()) is None,
                f"{projection} must be null when recognition did not succeed",
            )

    def test_fact_wrappers_and_evidence_are_v21_ready(self) -> None:
        defs = self.schema()["$defs"]
        self.assertEqual(
            defs["evidenceRecord"]["properties"]["source"]["enum"],
            ["visible_label", "user_text", "calculated", "reference_database", "visual_estimate"],
        )
        for wrapper in ["textFact", "amountFact", "quantityFact", "dateFact", "booleanFact"]:
            properties = defs[wrapper]["properties"]
            self.assertTrue({"confidence", "calculated", "evidence"}.issubset(properties))
            self.assertEqual(properties["confidence"]["minimum"], 0)
            self.assertEqual(properties["confidence"]["maximum"], 1)

    def test_schema_exposes_unified_product_order_and_projection_shapes(self) -> None:
        defs = self.schema()["$defs"]
        self.assertTrue("productFacts" in defs, "v2.1 must define unified product facts")
        self.assertTrue("dietProjection" in defs, "v2.1 must retain the public diet projection")
        product = defs["productFacts"]["properties"]
        self.assertTrue({"full_name", "normalized_name", "specification", "purchase_quantity", "quantity_unit", "nominal_weight_or_volume", "actual_weight_or_volume", "billing_weight", "weight_variance", "original_amount", "unit_price", "line_paid_amount", "refund_amount", "production_date", "line_status", "item_type", "visibility_status"}.issubset(product))
        order = defs["orderFacts"]["properties"]
        self.assertTrue({"merchant", "transaction_time", "order_status", "goods_subtotal", "activity_discount", "coupon_discount", "packaging_fee", "delivery_fee", "final_paid_amount", "refund_total", "declared_item_kind_count", "recognized_item_kind_count", "hidden_item_kind_count", "has_unexpanded_items", "content_complete"}.issubset(order))
        expense = defs["expenseProjection"]["properties"]
        self.assertTrue({"line_items", "detail_completeness", "omitted_item_count"}.issubset(expense))
        diet = defs["dietProjection"]["properties"]
        self.assertTrue({"business_products", "adapter_payload"}.issubset(diet))

    def test_literal_v21_fixtures_preserve_visible_facts_and_order_completeness(self) -> None:
        durian = self.fixture("durian-order.v2.1.json")
        partial = self.fixture("partial-nine-item-order.v2.1.json")

        self.assertEqual(durian["schema_version"], "image-intake-router.v2.1")
        self.assertEqual(durian["recognition_run"]["status"], "succeeded")
        self.assertEqual(durian["recognition_run"]["attachment_count"], 1)
        self.assertEqual(durian["recognition_run"]["processed_attachment_count"], 1)
        self.assertEqual(set(durian["facts"]["order"]), ORDER_FACT_KEYS)
        product = durian["facts"]["products"][0]
        self.assertEqual(set(product), PRODUCT_FACT_KEYS)
        self.assertEqual(product["full_name"]["value"], "金枕榴莲")
        self.assertEqual(product["normalized_name"]["value"], "榴莲")
        self.assertEqual(product["specification"]["value"], "约2.1kg × 1粒")
        self.assertEqual(product["purchase_quantity"]["value"], 1)
        self.assertEqual(product["quantity_unit"]["value"], "粒")
        self.assertEqual(product["nominal_weight_or_volume"]["value"], 2.1)
        self.assertEqual(product["nominal_weight_or_volume"]["unit"], "kg")
        self.assertIsNone(product["actual_weight_or_volume"]["value"])
        self.assertEqual(product["weight_variance"]["value"], 228)
        self.assertEqual(product["weight_variance"]["unit"], "g")
        self.assertEqual(product["line_paid_amount"]["value"], 119.00)
        self.assertEqual(product["refund_amount"]["value"], 12.92)
        self.assertEqual(durian["facts"]["order"]["final_paid_amount"]["value"], 119.00)
        self.assertEqual(durian["facts"]["order"]["refund_total"]["value"], 12.92)
        self.assertEqual(product["line_status"]["value"], "purchased_and_received")
        self.assertTrue({"confidence", "calculated", "evidence"}.issubset(product["full_name"]))
        self.assertNotIn("盒", json.dumps(durian, ensure_ascii=False))
        durian_expense_line = durian["expense_projection"]["line_items"][0]
        self.assertEqual(set(durian_expense_line) - {"field_metadata"}, PRODUCT_FACT_KEYS)
        self.assertTrue({"confidence", "calculated", "evidence"}.issubset(durian_expense_line["field_metadata"]))
        self.assertEqual(durian_expense_line["line_paid_amount"]["value"], 119.00)
        business_product = durian["diet_projection"]["business_products"][0]
        self.assertEqual(set(business_product), PRODUCT_FACT_KEYS)
        self.assertEqual(business_product["nominal_weight_or_volume"]["value"], 2.1)
        self.assertEqual(business_product["purchase_quantity"]["value"], 1)
        self.assertEqual(business_product["quantity_unit"]["value"], "粒")
        self.assertEqual(
            durian["diet_projection"]["adapter_payload"],
            [{"source_product_index": 0, "quantity": 2100, "unit": "g", "display_quantity": 1, "display_unit": "粒"}],
        )
        for field in ["actual_weight_or_volume", "billing_weight", "original_amount", "unit_price", "production_date"]:
            self.assertIsNone(product[field]["value"])
            self.assertEqual(product[field]["confidence"], 0)
            self.assertFalse(product[field]["calculated"])
            self.assertEqual(product[field]["evidence"], [])

        self.assertEqual(partial["recognition_run"]["status"], "succeeded")
        self.assertEqual(partial["recognition_run"]["attachment_count"], 1)
        self.assertEqual(partial["facts"]["order"]["final_paid_amount"]["value"], 65.48)
        expected_rows = [
            ("甜玉米", "约850 g × 2", 11.78), ("鲜牛奶", "1.5 L × 1", 10.90), ("黄瓜", "约700 g × 1", 4.99),
            ("西兰花", "约600 g × 1", 3.95), ("豆浆", "1 L × 2", 13.00), ("云南生菜", "约500 g × 1", 4.96),
            ("香蕉", "约800 g × 1", 11.90),
        ]
        self.assertEqual(len(partial["facts"]["products"]), 7)
        self.assertEqual(len(partial["expense_projection"]["line_items"]), 7)
        self.assertEqual(set(partial["facts"]["order"]), ORDER_FACT_KEYS)
        for product_row, expense_line in zip(partial["facts"]["products"], partial["expense_projection"]["line_items"]):
            self.assertEqual(set(product_row), PRODUCT_FACT_KEYS)
            self.assertEqual(set(expense_line) - {"field_metadata"}, PRODUCT_FACT_KEYS)
            self.assertTrue({"confidence", "calculated", "evidence"}.issubset(expense_line["field_metadata"]))
            self.assertIsNone(product_row["quantity_unit"]["value"])
            self.assertIsNone(expense_line["quantity_unit"]["value"])
        self.assertEqual([(row["full_name"]["value"], row["specification"]["value"], row["line_paid_amount"]["value"]) for row in partial["facts"]["products"]], expected_rows)
        order = partial["facts"]["order"]
        self.assertEqual(order["declared_item_kind_count"]["value"], 9)
        self.assertEqual(order["recognized_item_kind_count"]["value"], 7)
        self.assertEqual(order["hidden_item_kind_count"]["value"], 2)
        self.assertTrue(order["has_unexpanded_items"]["value"])
        self.assertFalse(order["content_complete"]["value"])
        self.assertEqual(partial["expense_projection"]["detail_completeness"], "partial")
        self.assertEqual(partial["expense_projection"]["omitted_item_count"], 2)
        self.assertNotIn("hidden_products", partial["facts"])
        self.assertEqual(len(partial["diet_projection"]["business_products"]), 7)
        self.assertEqual(len(partial["diet_projection"]["adapter_payload"]), 7)
        self.assertEqual(
            [
                (row["full_name"]["value"], row["purchase_quantity"]["value"], row["quantity_unit"]["value"], row["nominal_weight_or_volume"]["value"], row["nominal_weight_or_volume"]["unit"])
                for row in partial["diet_projection"]["business_products"]
            ],
            [("甜玉米", 2, None, 850, "g"), ("鲜牛奶", 1, None, 1.5, "L"), ("黄瓜", 1, None, 700, "g"), ("西兰花", 1, None, 600, "g"), ("豆浆", 2, None, 1, "L"), ("云南生菜", 1, None, 500, "g"), ("香蕉", 1, None, 800, "g")],
        )
        self.assertEqual(
            partial["diet_projection"]["adapter_payload"],
            [
                {"source_product_index": 0, "quantity": 1700, "unit": "g", "display_quantity": 2, "display_unit": None},
                {"source_product_index": 1, "quantity": 1500, "unit": "ml", "display_quantity": 1, "display_unit": None},
                {"source_product_index": 2, "quantity": 700, "unit": "g", "display_quantity": 1, "display_unit": None},
                {"source_product_index": 3, "quantity": 600, "unit": "g", "display_quantity": 1, "display_unit": None},
                {"source_product_index": 4, "quantity": 2000, "unit": "ml", "display_quantity": 2, "display_unit": None},
                {"source_product_index": 5, "quantity": 500, "unit": "g", "display_quantity": 1, "display_unit": None},
                {"source_product_index": 6, "quantity": 800, "unit": "g", "display_quantity": 1, "display_unit": None},
            ],
        )
        for fixture in [durian, partial]:
            self.assertEqual(fixture["preview_state"], "awaiting_confirmation")
            self.assertEqual(fixture["source"], {"image_count": 1, "has_user_text": False})
            self.assertEqual(fixture["quality"]["visual_capability"], "available")
            self.assertNotIn("attachment_context", json.dumps(fixture, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
