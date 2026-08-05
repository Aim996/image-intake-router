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
LEDGER_PUBLIC_LINE_ITEM_KEYS = {
    "full_name", "normalized_name", "specification", "quantity", "quantity_unit",
    "nominal_weight_or_volume", "actual_weight_or_volume", "billing_weight", "weight_variance",
    "original_amount", "unit_price", "paid_amount", "refund_amount", "production_date",
    "line_status", "field_metadata",
}
LEDGER_PUBLIC_LINE_ITEM_REQUIRED = {"full_name", "quantity", "field_metadata"}
LEDGER_PUBLIC_LINE_ITEM_WRAPPER_ONLY = {
    "purchase_quantity", "line_paid_amount", "item_type", "visibility_status", "currency",
    "confidence", "calculated", "evidence",
}
LEDGER_PUBLIC_MEASUREMENT_FIELDS = {
    "nominal_weight_or_volume", "actual_weight_or_volume", "billing_weight", "weight_variance",
}


def matches_schema_fragment(instance: object, fragment: dict) -> bool:
    """Evaluate the small JSON Schema subset used by recognition status guards."""
    if "required" in fragment and (
        not isinstance(instance, dict) or any(key not in instance for key in fragment["required"])
    ):
        return False
    if "const" in fragment and instance != fragment["const"]:
        return False
    if "enum" in fragment and instance not in fragment["enum"]:
        return False
    if fragment.get("type") == "null" and instance is not None:
        return False
    if "minimum" in fragment and (
        not isinstance(instance, (int, float)) or instance < fragment["minimum"]
    ):
        return False
    if "properties" in fragment:
        if not isinstance(instance, dict):
            return False
        for key, constraint in fragment["properties"].items():
            if key in instance and not matches_schema_fragment(instance[key], constraint):
                return False
    if "items" in fragment:
        if not isinstance(instance, list):
            return False
        if any(not matches_schema_fragment(item, fragment["items"]) for item in instance):
            return False
    if "contains" in fragment:
        if not isinstance(instance, list):
            return False
        matches = sum(matches_schema_fragment(item, fragment["contains"]) for item in instance)
        if matches < fragment.get("minContains", 1):
            return False
    return all(matches_schema_fragment(instance, rule) for rule in fragment.get("allOf", []))


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

    def test_output_contract_uses_concise_business_output_and_no_verbose_skeleton(self) -> None:
        content = self.read(REFERENCES / "output-contract.md")
        for phrase in [
            "one or two business sentences",
            "full details only on request",
            "no business preview or confirmation prompt",
            "will not run and why",
            "line_items",
            "refund",
        ]:
            self.assertIn(phrase, content.lower())
        self.assertNotIn("exact user-visible tokens byte-for-byte", content)
        self.assertNotIn("Use this literal reply skeleton", content)

    def test_output_contract_gives_approved_chinese_examples_and_scope_mappings(self) -> None:
        content = self.read(REFERENCES / "output-contract.md")
        self.assertIn(
            "识别到本单实付 ¥65.48，共至少 9 种商品；图片完整展示了 7 种，另外 2 种未展开。"
            "准备记账 ¥65.48，并将 7 种可见食品交给食序管家，是否确认？",
            content,
        )
        self.assertIn(
            "已记账 ¥65.48，完整保存了 7 种可见商品的名称、重量、数量和价格；"
            "食序管家成功入库 6 种，1 种因数量不明确未提交。",
            content,
        )
        for mapping in [
            "`确认`/`可以`/`就这样` => all executable scopes",
            "`只记账` => expense only",
            "`只入库` => diet only",
        ]:
            self.assertIn(mapping, content)
        self.assertIn("A question is not confirmation", content)
        self.assertIn("A changed digest produces a new concise preview", content)

    def test_projection_contract_preserves_order_detail_and_dual_projection_boundary(self) -> None:
        content = self.read(REFERENCES / "projection-contracts.md")
        for phrase in [
            "one expense, never one expense per product",
            "`line_items` contains every ledger-forwardable visible purchased product",
            "`note` is generated independently",
            "note truncation never removes or truncates structured `line_items`",
            "fail that domain closed",
            "`business_products` preserves source business facts",
            "`adapter_payload` contains deterministic technical normalization",
            "Only clearly food + purchased + received rows enter `items`",
            "hidden rows never do",
            "Unknown expiry adapts to the installed public schema",
        ]:
            self.assertIn(phrase, content)
        self.assertIn("`约 2.1 kg × 1粒`", content)
        self.assertNotIn("`约 2.1 kg × 1袋`", content)
        self.assertIn("`2100 g` or `piece`", content)
        self.assertIn("`facts.products` is the canonical provenance-rich fact set", content)
        self.assertIn("The finalized ledger-public projection is forwarded intact", content)
        self.assertIn("Adapter-only repairs do not change the business digest or require another user confirmation", content)
        self.assertNotIn("raw/wrapper `line_items` are forwarded intact", content)
        self.assertIn("完成适配的账本公开 `line_items` 投影必须原样转发", content)
        self.assertNotIn("`line_items` 必须原样转发", content)

    def test_confirmation_uses_a_business_digest_and_one_later_confirmation(self) -> None:
        content = self.read(REFERENCES / "confirmation-and-execution.md")
        for phrase in [
            "business_digest",
            "canonical representation",
            "final paid amount and category business meaning",
            "expense/diet selected scopes",
            "initial image turn",
            "zero business writes",
            "later valid confirmation",
            "Business-field or selected-scope changes require a new preview and confirmation",
            "Adapter-only changes do not change the digest and do not reconfirm",
            "kg/g/L/ml conversion",
            "expiry null/omission/version adaptation",
            "stable call IDs",
        ]:
            self.assertIn(phrase, content)

    def test_recovery_has_exactly_four_states_and_one_correction_path(self) -> None:
        content = self.read(REFERENCES / "failure-recovery.md")
        self.assertRegex(
            content,
            r"Execution statuses are exactly: `not_executed`, `written`, "
            r"`failed_before_write`, `indeterminate`\.",
        )
        self.assertIn("There is no generic terminal `failed` state", content)
        self.assertNotRegex(content, r"\|.*`failed`.*\|")
        for phrase in [
            "at most one deterministic adapter-only correction",
            "business digest is unchanged",
            "does not replay the expense or any written pantry item",
            "queries the documented downstream status/idempotency state first",
            "Never resubmit blindly",
            "One pantry item failure does not replay written siblings",
            "Do not directly edit SQLite",
        ]:
            self.assertIn(phrase, content)

    def test_default_output_hides_internal_data_and_partial_order_detail_survives(self) -> None:
        output = self.read(REFERENCES / "output-contract.md")
        projection = self.read(REFERENCES / "projection-contracts.md")
        for token in [
            "visible_label",
            "user_text",
            "attachment_context",
            "shopping",
            "ISO timestamp",
            "expires_at",
            "technical `piece`",
            "preview revision",
            "operation/call IDs",
            "adapter versions",
            "internal execution-state names",
        ]:
            self.assertIn(token, output)
        for phrase in [
            "seven visible + two hidden yields at least 9/visible 7/hidden 2",
            "only seven product rows downstream",
            "refund facts remain but create no refund write",
        ]:
            self.assertIn(phrase, projection.lower())

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

    def test_schema_adapts_expense_lines_to_strict_ledger_public_scalars(self) -> None:
        defs = json.loads(self.read(SCHEMA))["$defs"]
        line = defs["expenseLineItem"]
        metadata = defs["fieldMetadata"]
        measurement = defs["expenseMeasurement"]

        self.assertFalse(line["additionalProperties"])
        self.assertEqual(set(line["properties"]), LEDGER_PUBLIC_LINE_ITEM_KEYS)
        self.assertEqual(set(line["required"]), LEDGER_PUBLIC_LINE_ITEM_REQUIRED)
        self.assertEqual(line["properties"]["full_name"]["minLength"], 1)
        self.assertEqual(line["properties"]["full_name"]["maxLength"], 240)
        self.assertEqual(line["properties"]["full_name"]["pattern"], "\\S")
        self.assertEqual(line["properties"]["quantity"]["exclusiveMinimum"], 0)
        self.assertEqual(line["properties"]["quantity"]["maximum"], 1_000_000_000)
        self.assertEqual(line["properties"]["field_metadata"]["minItems"], 1)
        self.assertEqual(line["properties"]["field_metadata"]["maxItems"], 100)
        for amount_field in ["original_amount", "unit_price", "paid_amount", "refund_amount"]:
            amount = line["properties"][amount_field]
            self.assertEqual(amount["minimum"], 0)
            self.assertEqual(amount["maximum"], 9_999_999_999.99)
            self.assertEqual(amount["multipleOf"], 0.01)
        self.assertFalse(metadata["additionalProperties"])
        self.assertEqual(set(metadata["required"]), {"field", "source", "confidence", "calculated"})
        self.assertEqual(set(metadata["properties"]), {"field", "source", "confidence", "calculated", "location"})
        self.assertEqual(set(metadata["properties"]["field"]["enum"]), LEDGER_PUBLIC_LINE_ITEM_KEYS - {"field_metadata"})
        self.assertEqual(
            metadata["properties"]["source"]["enum"],
            ["visible_label", "user_text", "calculated", "reference_database", "visual_estimate"],
        )
        self.assertEqual(metadata["properties"]["confidence"]["minimum"], 0)
        self.assertEqual(metadata["properties"]["confidence"]["maximum"], 1)
        self.assertEqual(metadata["properties"]["location"]["maxLength"], 240)
        self.assertFalse(measurement["additionalProperties"])
        self.assertEqual(set(measurement["required"]), {"value", "unit"})
        self.assertEqual(measurement["properties"]["value"]["exclusiveMinimum"], 0)
        self.assertEqual(measurement["properties"]["value"]["maximum"], 1_000_000_000)
        self.assertEqual(measurement["properties"]["unit"]["maxLength"], 40)

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
        expected = {
            "references/recognition-rules.md",
            "references/calculation-rules.md",
            "references/projection-contracts.md",
            "references/confirmation-and-execution.md",
            "references/output-contract.md",
            "references/failure-recovery.md",
            "references/vision-runtime.md",
        }
        self.assertEqual(set(targets), expected)
        self.assertTrue(all("\\" not in target for target in targets))
        self.assertLess(len(content.splitlines()), 500)
        self.assertGreaterEqual(len(targets), 6)
        self.assertEqual(
            [target for target in targets if not (SKILL_ROOT / target).is_file()],
            [],
        )

    def test_skill_removes_described_image_exception_and_verbose_skeleton(self) -> None:
        content = self.read(SKILL)
        self.assertNotIn("For a described image with no pixels", content)
        self.assertNotIn("Use this literal reply skeleton", content)
        for phrase in [
            "recognition_run",
            "one unified fact set",
            "one concise business preview",
            "zero business writes",
            "later confirmation",
        ]:
            self.assertIn(phrase, content)

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

    def recognition_status_rule(self, status: str) -> dict:
        rules = self.schema()["$defs"]["recognitionRun"]["allOf"]
        matches = [
            rule["then"]
            for rule in rules
            if rule.get("if", {}).get("properties", {}).get("status", {}).get("const") == status
        ]
        self.assertEqual(len(matches), 1, f"recognition status {status} must have one conditional rule")
        return matches[0]

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

    def test_recognition_status_conditions_fail_closed_per_attachment(self) -> None:
        def run(status: str, attachment_statuses: list[str], processed: int, issues: list[str]) -> dict:
            completeness = {
                "succeeded": "complete",
                "partial": "partial",
                "failed": "unavailable",
                "not_executed": "unavailable",
            }
            return {
                "status": status,
                "processed_attachment_count": processed,
                "attachments": [
                    {
                        "attachment_index": index,
                        "status": attachment_status,
                        "completeness": completeness[attachment_status],
                        "limitations": [] if attachment_status == "succeeded" else ["controlled limitation"],
                    }
                    for index, attachment_status in enumerate(attachment_statuses)
                ],
                "issues": issues,
            }

        partial_rule = self.recognition_status_rule("partial")
        self.assertFalse(matches_schema_fragment(run("partial", ["succeeded", "failed"], 2, ["failed image"]), partial_rule))
        self.assertFalse(matches_schema_fragment(run("partial", ["succeeded", "not_executed"], 1, ["image skipped"]), partial_rule))
        self.assertTrue(matches_schema_fragment(run("partial", ["succeeded", "partial"], 2, []), partial_rule))
        self.assertTrue(matches_schema_fragment(run("partial", ["partial", "partial"], 2, []), partial_rule))

        failed_rule = self.recognition_status_rule("failed")
        self.assertTrue(matches_schema_fragment(run("failed", ["succeeded", "failed"], 2, ["failed image"]), failed_rule))
        self.assertTrue(matches_schema_fragment(run("failed", ["succeeded", "not_executed"], 1, ["image skipped"]), failed_rule))
        self.assertFalse(matches_schema_fragment(run("failed", ["succeeded", "succeeded"], 2, ["wrong status"]), failed_rule))
        self.assertFalse(matches_schema_fragment(run("failed", ["not_executed", "not_executed"], 0, ["no vision"]), failed_rule))

        succeeded_rule = self.recognition_status_rule("succeeded")
        self.assertTrue(matches_schema_fragment(run("succeeded", ["succeeded", "succeeded"], 2, []), succeeded_rule))
        self.assertFalse(matches_schema_fragment(run("succeeded", ["succeeded", "partial"], 2, []), succeeded_rule))

        not_executed_rule = self.recognition_status_rule("not_executed")
        self.assertTrue(matches_schema_fragment(run("not_executed", ["not_executed", "not_executed"], 0, []), not_executed_rule))
        self.assertFalse(matches_schema_fragment(run("not_executed", ["succeeded", "not_executed"], 1, []), not_executed_rule))

    def test_runtime_invariants_require_exact_attachment_coverage_and_processed_count(self) -> None:
        description = self.schema()["$defs"]["recognitionRun"]["description"]
        for invariant in [
            "attachment_count equals source.image_count and attachments.length",
            "unique contiguous attachment_index",
            "processed_attachment_count equals the number of attachments whose status is not not_executed",
            "A succeeded run requires processed_attachment_count to equal attachment_count",
        ]:
            self.assertIn(invariant, description)

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
        self.assertEqual(guarded.get("preview_state"), {"const": "draft"})
        for projection in ["expense_projection", "diet_projection"]:
            constraint = guarded[projection]
            self.assertTrue(
                constraint.get("type") == "null" or constraint.get("const", object()) is None,
                f"{projection} must be null when recognition did not succeed",
            )

        failed_record = {
            "preview_state": "draft",
            "expense_projection": None,
            "diet_projection": None,
            "quality": {"fact_set_status": "unavailable"},
        }
        self.assertTrue(matches_schema_fragment(failed_record, guard["then"]))
        for unsafe_mutation in [
            {**failed_record, "preview_state": "awaiting_confirmation"},
            {**failed_record, "expense_projection": {"executable": True}},
            {**failed_record, "diet_projection": {"items": []}},
            {**failed_record, "quality": {"fact_set_status": "partial"}},
        ]:
            self.assertFalse(matches_schema_fragment(unsafe_mutation, guard["then"]))

        root_properties = self.schema()["properties"]
        self.assertNotIn("confirmation_token", root_properties)
        self.assertNotIn("adapter_execution", root_properties)
        self.assertNotIn("business_writes", root_properties)

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
        self.assertEqual(
            {
                field: durian["expense_projection"][field]
                for field in ["executable", "amount", "category_id", "occurred_at", "source_kind", "merchant", "note", "issues"]
            },
            {
                "executable": True,
                "amount": 119.00,
                "category_id": "shopping",
                "occurred_at": "2026-08-05T00:00:00+08:00",
                "source_kind": "image",
                "merchant": None,
                "note": None,
                "issues": [],
            },
        )
        self.assertEqual(
            set(durian_expense_line),
            {
                "full_name", "normalized_name", "specification", "quantity", "quantity_unit",
                "nominal_weight_or_volume", "weight_variance", "paid_amount", "refund_amount",
                "line_status", "field_metadata",
            },
        )
        self.assertEqual(durian_expense_line["full_name"], "金枕榴莲")
        self.assertEqual(durian_expense_line["normalized_name"], "榴莲")
        self.assertEqual(durian_expense_line["specification"], "约2.1kg × 1粒")
        self.assertEqual(durian_expense_line["quantity"], 1)
        self.assertEqual(durian_expense_line["quantity_unit"], "粒")
        self.assertEqual(durian_expense_line["nominal_weight_or_volume"], {"value": 2.1, "unit": "kg"})
        self.assertEqual(durian_expense_line["weight_variance"], {"value": 228, "unit": "g"})
        self.assertEqual(durian_expense_line["paid_amount"], 119.00)
        self.assertEqual(durian_expense_line["refund_amount"], 12.92)
        self.assertEqual(durian_expense_line["line_status"], "purchased_and_received")
        for field in ["actual_weight_or_volume", "billing_weight", "original_amount", "unit_price", "production_date"]:
            self.assertNotIn(field, durian_expense_line)
        self.assertTrue(
            all(
                not isinstance(value, dict)
                for field, value in durian_expense_line.items()
                if field not in {"field_metadata", *LEDGER_PUBLIC_MEASUREMENT_FIELDS}
            )
        )
        self.assertFalse(LEDGER_PUBLIC_LINE_ITEM_WRAPPER_ONLY.intersection(durian_expense_line))
        self.assertEqual(
            {entry["field"] for entry in durian_expense_line["field_metadata"]},
            set(durian_expense_line) - {"field_metadata"},
        )
        self.assertTrue(all(entry["source"] != "attachment_context" for entry in durian_expense_line["field_metadata"]))
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
        self.assertEqual(
            {
                field: partial["expense_projection"][field]
                for field in ["executable", "amount", "category_id", "occurred_at", "source_kind", "merchant", "note", "issues"]
            },
            {
                "executable": True,
                "amount": 65.48,
                "category_id": "shopping",
                "occurred_at": "2026-08-05T00:00:00+08:00",
                "source_kind": "image",
                "merchant": None,
                "note": None,
                "issues": [],
            },
        )
        self.assertEqual(set(partial["facts"]["order"]), ORDER_FACT_KEYS)
        expected_expense_rows = [
            ("甜玉米", "约850 g × 2", 2, {"value": 850, "unit": "g"}, 11.78),
            ("鲜牛奶", "1.5 L × 1", 1, {"value": 1.5, "unit": "L"}, 10.90),
            ("黄瓜", "约700 g × 1", 1, {"value": 700, "unit": "g"}, 4.99),
            ("西兰花", "约600 g × 1", 1, {"value": 600, "unit": "g"}, 3.95),
            ("豆浆", "1 L × 2", 2, {"value": 1, "unit": "L"}, 13.00),
            ("云南生菜", "约500 g × 1", 1, {"value": 500, "unit": "g"}, 4.96),
            ("香蕉", "约800 g × 1", 1, {"value": 800, "unit": "g"}, 11.90),
        ]
        for product_row, expense_line, expected_expense in zip(partial["facts"]["products"], partial["expense_projection"]["line_items"], expected_expense_rows):
            self.assertEqual(set(product_row), PRODUCT_FACT_KEYS)
            self.assertTrue(set(expense_line).issubset(LEDGER_PUBLIC_LINE_ITEM_KEYS))
            self.assertTrue(LEDGER_PUBLIC_LINE_ITEM_REQUIRED.issubset(expense_line))
            self.assertEqual(
                (expense_line["full_name"], expense_line["specification"], expense_line["quantity"], expense_line["nominal_weight_or_volume"], expense_line["paid_amount"]),
                expected_expense,
            )
            self.assertTrue(
                all(
                    not isinstance(value, dict)
                    for field, value in expense_line.items()
                    if field not in {"field_metadata", *LEDGER_PUBLIC_MEASUREMENT_FIELDS}
                )
            )
            self.assertFalse(LEDGER_PUBLIC_LINE_ITEM_WRAPPER_ONLY.intersection(expense_line))
            self.assertEqual({entry["field"] for entry in expense_line["field_metadata"]}, set(expense_line) - {"field_metadata"})
            self.assertTrue(all(entry["source"] != "attachment_context" for entry in expense_line["field_metadata"]))
            self.assertIsNone(product_row["quantity_unit"]["value"])
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
        self.assertEqual(durian["diet_projection"]["business_products"], durian["facts"]["products"])
        self.assertEqual(partial["diet_projection"]["business_products"], partial["facts"]["products"])
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
