import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = SKILL_ROOT / "templates" / "image-intake-router.schema.json"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class RouterV31FixtureSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema, format_checker=FormatChecker())

    def fixture(self, name: str) -> dict:
        path = FIXTURES / name
        self.assertTrue(path.is_file(), f"missing v3.1 fixture: {name}")
        return json.loads(path.read_text(encoding="utf-8"))

    def validation_messages(
        self,
        instance: object,
        validator: Draft202012Validator | None = None,
    ) -> list[str]:
        def messages(error) -> list[str]:
            path = "/" + "/".join(str(part) for part in error.absolute_path)
            if error.context:
                current = []
            else:
                current = [f"{path}: {error.message}"]
            for child in error.context:
                current.extend(messages(child))
            return current

        rendered = []
        active_validator = validator or self.validator
        for error in sorted(
            active_validator.iter_errors(instance),
            key=lambda item: [str(part) for part in item.absolute_path],
        ):
            rendered.extend(messages(error))
        return rendered

    def assert_schema_valid(self, instance: object) -> None:
        messages = self.validation_messages(instance)
        self.assertEqual(messages, [], "\n".join(messages))

    def assert_schema_invalid(self, instance: object) -> None:
        self.assertNotEqual(self.validation_messages(instance), [])

    def definition_validator(self, name: str) -> Draft202012Validator:
        return Draft202012Validator(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$ref": f"#/$defs/{name}",
                "$defs": self.schema["$defs"],
            },
            format_checker=FormatChecker(),
        )

    def assert_definition_valid(self, name: str, instance: object) -> None:
        messages = self.validation_messages(instance, self.definition_validator(name))
        self.assertEqual(messages, [], "\n".join(messages))

    def assert_definition_invalid(self, name: str, instance: object) -> None:
        self.assertNotEqual(
            self.validation_messages(instance, self.definition_validator(name)),
            [],
        )

    def assert_runtime_attachment_invariants(self, record: dict) -> None:
        run = record["recognition_run"]
        attachments = run["attachments"]
        self.assertEqual(record["source"]["image_count"], run["attachment_count"])
        self.assertEqual(run["attachment_count"], len(attachments))
        self.assertEqual(
            [row["attachment_index"] for row in attachments],
            list(range(len(attachments))),
        )
        self.assertEqual(
            run["processed_attachment_count"],
            sum(row["status"] != "not_executed" for row in attachments),
        )

    def assert_runtime_handoff_invariants(self, record: dict) -> None:
        handoff = record["handoff"]
        if handoff is not None:
            self.assertEqual(record["preview_id"], handoff["preview_id"])
            for scope in handoff["selected_scopes"]:
                content = record[f"{scope}_content"]
                self.assertIsNotNone(content)
                self.assertTrue(content["executable"])
                if scope == "inventory":
                    self.assertGreater(len(content["items"]), 0)

    def fact_measurement(self, fact: dict) -> dict | None:
        if fact["value"] is None:
            return None
        return {"value": fact["value"], "unit": fact["unit"]}

    def assert_runtime_content_invariants(self, record: dict) -> None:
        products = record["facts"]["products"]
        for scope in ["accounting", "inventory"]:
            content = record[f"{scope}_content"]
            if content is None:
                continue
            indexes = [item["product_index"] for item in content["items"]]
            self.assertEqual(len(indexes), len(set(indexes)))
            for item in content["items"]:
                product = products[item["product_index"]]
                self.assertEqual(
                    product["line_status"]["value"],
                    "purchased_and_received",
                    f"{scope} contains an ineligible product status",
                )
                self.assertEqual(
                    product["visibility_status"]["value"],
                    "visible",
                    f"{scope} contains a non-visible product row",
                )
                if scope == "accounting":
                    self.assertIn(
                        product["item_type"]["value"],
                        {"food", "non_food"},
                        "accounting contains a fee, discount, advertisement, or unknown row",
                    )
                    self.assertIn("display_name", item)
                    self.assertIn("display_name", product)
                    self.assertEqual(
                        item["display_name"], product["display_name"]["value"]
                    )
                    self.assertEqual(item["specification"], product["specification"]["value"])
                    self.assertEqual(item["quantity"], product["purchase_quantity"]["value"])
                    self.assertEqual(item["quantity_unit"], product["quantity_unit"]["value"])
                    self.assertEqual(
                        item["nominal_weight_or_volume"],
                        self.fact_measurement(product["nominal_weight_or_volume"]),
                    )
                    self.assertEqual(
                        item["actual_weight_or_volume"],
                        self.fact_measurement(product["actual_weight_or_volume"]),
                    )
                    self.assertEqual(
                        item["line_paid_amount"], product["line_paid_amount"]["value"]
                    )
                else:
                    self.assertEqual(
                        product["item_type"]["value"],
                        "food",
                        "inventory contains a non-food row",
                    )
                    self.assertIn("display_name", item)
                    self.assertIn("display_name", product)
                    self.assertEqual(
                        item["display_name"], product["display_name"]["value"]
                    )
                    self.assertEqual(item["specification"], product["specification"]["value"])
                    self.assertEqual(item["quantity"], product["purchase_quantity"]["value"])
                    self.assertEqual(item["quantity_unit"], product["quantity_unit"]["value"])
                    inventory_weight = product["actual_weight_or_volume"]
                    if inventory_weight["value"] is None:
                        inventory_weight = product["nominal_weight_or_volume"]
                    self.assertEqual(
                        item["weight_or_volume"], self.fact_measurement(inventory_weight)
                    )
                    self.assertEqual(
                        item["production_date"], product["production_date"]["value"]
                    )

    def test_v31_schema_excludes_nonbusiness_fields_from_persisted_records(self) -> None:
        self.assertEqual(
            self.schema["properties"]["schema_version"]["const"],
            "image-intake-router.v3.1",
        )
        forbidden = {
            "refund_total",
            "refund_amount",
            "original_amount",
            "unit_price",
            "activity_discount",
            "coupon_discount",
            "packaging_fee",
            "delivery_fee",
            "weight_variance",
        }
        defs = self.schema["$defs"]
        for definition in ["orderFacts", "productFacts", "accountingItem", "inventoryItem"]:
            with self.subTest(definition=definition):
                self.assertTrue(
                    forbidden.isdisjoint(defs[definition]["properties"]),
                    forbidden.intersection(defs[definition]["properties"]),
                )

    def test_every_shipped_v31_fixture_is_a_complete_draft_2020_12_instance(self) -> None:
        fixtures = sorted(FIXTURES.glob("*.v3.1.json"))
        self.assertGreater(len(fixtures), 0)
        for path in fixtures:
            with self.subTest(fixture=path.name):
                self.assert_schema_valid(json.loads(path.read_text(encoding="utf-8")))

    def test_v31_fixtures_preserve_exact_attachment_coverage_and_count(self) -> None:
        for name in [
            "durian-order.v3.1.json",
            "partial-nine-item-order.v3.1.json",
            "partial-refined-nine-item-order.v3.1.json",
            "failed-recognition.v3.1.json",
        ]:
            with self.subTest(fixture=name):
                self.assert_runtime_attachment_invariants(self.fixture(name))

    def test_attachment_coverage_helper_rejects_count_and_index_mismatches(self) -> None:
        baseline = self.fixture("partial-nine-item-order.v3.1.json")
        mutations = {
            "source image count": lambda record: record["source"].__setitem__("image_count", 2),
            "attachment count": lambda record: record["recognition_run"].__setitem__(
                "attachment_count", 2
            ),
            "processed count": lambda record: record["recognition_run"].__setitem__(
                "processed_attachment_count", 2
            ),
            "contiguous attachment index": lambda record: record["recognition_run"][
                "attachments"
            ][0].__setitem__("attachment_index", 1),
        }
        for name, mutate in mutations.items():
            with self.subTest(mismatch=name):
                record = copy.deepcopy(baseline)
                mutate(record)
                with self.assertRaises(AssertionError):
                    self.assert_runtime_attachment_invariants(record)

    def test_durian_refinement_preserves_visible_detail(self) -> None:
        record = self.fixture("durian-order.v3.1.json")
        self.assertEqual(record["recognition_run"]["pass_count"], 2)
        self.assertEqual(record["recognition_run"]["refinement"]["status"], "succeeded")
        item = record["accounting_content"]["items"][0]
        self.assertEqual(item["display_name"], "榴莲")
        self.assertEqual(item["nominal_weight_or_volume"], {"value": 2.1, "unit": "kg"})
        self.assertEqual(item["quantity"], 1)
        self.assertEqual(item["line_paid_amount"], 119.00)
        self.assertNotIn("refund_amount", item)
        self.assertNotIn("退款", record["cleaned_text"])
        self.assertNotIn("短重", record["cleaned_text"])

    def test_compact_nine_item_preview_uses_concise_names_dates_and_actual_amounts(self) -> None:
        record = self.fixture("compact-nine-item-order.v3.1.json")
        self.assert_schema_valid(record)
        self.assertEqual(record["accounting_content"]["final_paid_amount"], 65.48)
        items = record["accounting_content"]["items"]
        self.assertEqual(
            [item["display_name"] for item in items],
            [
                "甜玉米",
                "鲜牛奶",
                "黄瓜",
                "西兰花",
                "豆浆",
                "生菜",
                "香蕉",
                "鲜牛奶",
                "果蔬汁",
            ],
        )
        self.assertEqual(
            [item["line_paid_amount"] for item in items],
            [11.78, 10.90, 4.99, 3.95, 13.00, 4.96, 11.90, 3.00, 0.00],
        )
        self.assertNotEqual(items[1]["product_index"], items[7]["product_index"])
        self.assertEqual(items[1]["specification"], "1.5L")
        self.assertEqual(items[7]["specification"], "260ml×3瓶")
        inventory = record["inventory_content"]["items"]
        self.assertEqual(len(inventory), 9)
        self.assertEqual(inventory[1]["production_date"], "2026-08-03")
        self.assertEqual(inventory[7]["production_date"], "2026-08-02")
        self.assertEqual(inventory[8]["production_date"], "2026-08-01")
        self.assertEqual(record["warnings"], ["交易时间未显示"])

        forbidden_keys = {
            "refund_total",
            "refund_amount",
            "original_amount",
            "unit_price",
            "activity_discount",
            "coupon_discount",
            "packaging_fee",
            "delivery_fee",
            "weight_variance",
        }

        def walk(value: object) -> None:
            if isinstance(value, dict):
                self.assertTrue(forbidden_keys.isdisjoint(value), forbidden_keys.intersection(value))
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(record["facts"])
        walk(record["accounting_content"])
        walk(record["inventory_content"])
        rendered = json.dumps(record, ensure_ascii=False)
        for forbidden_text in ["赠品", "免费", "会员", "原价", "优惠", "退款", "短重"]:
            self.assertNotIn(forbidden_text, rendered)

    def test_executable_accounting_accepts_real_zero_final_payment(self) -> None:
        record = self.fixture("compact-nine-item-order.v3.1.json")
        record["facts"]["order"]["final_paid_amount"]["value"] = 0.00
        record["facts"]["order"]["final_paid_amount"]["evidence"][0]["value"] = (
            "实付 ¥0.00"
        )
        record["accounting_content"]["final_paid_amount"] = 0.00
        self.assert_schema_valid(record)

    def test_runtime_content_rejects_ineligible_product_rows(self) -> None:
        baseline = self.fixture("compact-nine-item-order.v3.1.json")
        mutations = {
            "fully refunded": ("line_status", "fully_refunded"),
            "cancelled": ("line_status", "cancelled"),
            "unavailable": ("line_status", "unavailable"),
            "not received": ("line_status", "not_received"),
            "fee row": ("item_type", "fee_or_service"),
            "hidden row": ("visibility_status", "hidden"),
        }
        for name, (field, value) in mutations.items():
            with self.subTest(status=name):
                record = copy.deepcopy(baseline)
                record["facts"]["products"][0][field]["value"] = value
                with self.assertRaises(AssertionError):
                    self.assert_runtime_content_invariants(record)

        non_food = copy.deepcopy(baseline)
        non_food["facts"]["products"][0]["item_type"]["value"] = "non_food"
        with self.assertRaises(AssertionError):
            self.assert_runtime_content_invariants(non_food)

    def test_received_product_remains_eligible_after_partial_refund_classification(self) -> None:
        record = self.fixture("durian-order.v3.1.json")
        self.assertEqual(
            record["facts"]["products"][0]["line_status"]["value"],
            "purchased_and_received",
        )
        self.assert_runtime_content_invariants(record)

    def test_production_date_requires_visible_uncalculated_provenance(self) -> None:
        baseline = self.fixture("compact-nine-item-order.v3.1.json")
        product_index = 1

        calculated = copy.deepcopy(baseline)
        calculated["facts"]["products"][product_index]["production_date"][
            "calculated"
        ] = True
        self.assert_schema_invalid(calculated)

        for source in ["calculated", "reference_database", "visual_estimate", "user_text"]:
            with self.subTest(source=source):
                record = copy.deepcopy(baseline)
                record["facts"]["products"][product_index]["production_date"][
                    "evidence"
                ][0]["source"] = source
                self.assert_schema_invalid(record)

    def test_hidden_items_warn_without_triggering_refinement(self) -> None:
        record = self.fixture("partial-nine-item-order.v3.1.json")
        self.assertEqual(record["recognition_run"]["pass_count"], 1)
        self.assertEqual(record["recognition_run"]["refinement"]["status"], "not_needed")
        self.assertEqual(len(record["accounting_content"]["items"]), 7)
        self.assertEqual(len(record["inventory_content"]["items"]), 7)
        self.assertIn("另有 2 种商品未展开", record["warnings"])

    def test_failed_recognition_has_no_actionable_content_or_handoff(self) -> None:
        record = self.fixture("failed-recognition.v3.1.json")
        self.assertEqual(record["preview_state"], "failed")
        self.assertEqual(record["recognition_run"]["pass_count"], 0)
        self.assertIsNone(record["cleaned_text"])
        self.assertIsNone(record["accounting_content"])
        self.assertIsNone(record["inventory_content"])
        self.assertIsNone(record["handoff"])

    def test_failed_and_not_executed_recognition_fail_closed(self) -> None:
        baseline = self.fixture("failed-recognition.v3.1.json")
        for status, pass_count in [("failed", 0), ("not_executed", 0)]:
            with self.subTest(status=status):
                record = copy.deepcopy(baseline)
                record["preview_state"] = "failed"
                run = record["recognition_run"]
                run["status"] = status
                run["pass_count"] = pass_count
                if status == "not_executed":
                    run["processed_attachment_count"] = 0
                    for attachment in run["attachments"]:
                        attachment["status"] = "not_executed"
                        attachment["completeness"] = "unavailable"
                refinement = run["refinement"]
                refinement["status"] = "not_applicable"
                self.assert_schema_valid(record)
                self.assertEqual(refinement["reasons"], [])
                self.assertEqual(refinement["targeted_fields"], [])
                self.assertEqual(refinement["attachment_indexes"], [])
                self.assertEqual(refinement["issues"], [])
                self.assertIsNone(record["cleaned_text"])
                self.assertIsNone(record["accounting_content"])
                self.assertIsNone(record["inventory_content"])
                self.assertIsNone(record["handoff"])

                actionable = self.fixture("durian-order.v3.1.json")
                handed_off = self.fixture("handed-off.v3.1.json")
                unsafe_values = {
                    "cleaned_text": actionable["cleaned_text"],
                    "accounting_content": actionable["accounting_content"],
                    "inventory_content": actionable["inventory_content"],
                    "handoff": handed_off["handoff"],
                }
                for field, value in unsafe_values.items():
                    with self.subTest(status=status, field=field):
                        unsafe = copy.deepcopy(record)
                        unsafe[field] = value
                        self.assert_schema_invalid(unsafe)

    def test_refinement_statuses_enforce_valid_pass_count_combinations(self) -> None:
        failed_initial = self.fixture("failed-recognition.v3.1.json")
        for pass_count in [0, 1]:
            with self.subTest(initial_failure_pass_count=pass_count):
                record = copy.deepcopy(failed_initial)
                run = record["recognition_run"]
                run["status"] = "failed"
                run["pass_count"] = pass_count
                refinement = run["refinement"]
                refinement["status"] = "not_applicable"
                self.assert_schema_valid(record)
                self.assertEqual(refinement["reasons"], [])
                self.assertEqual(refinement["targeted_fields"], [])
                self.assertEqual(refinement["attachment_indexes"], [])
                self.assertEqual(refinement["issues"], [])

                for refinement_status in ["not_needed", "succeeded", "partial", "failed"]:
                    invalid = copy.deepcopy(record)
                    invalid["recognition_run"]["refinement"]["status"] = refinement_status
                    self.assert_schema_invalid(invalid)

        invalid = copy.deepcopy(failed_initial)
        invalid["recognition_run"]["status"] = "failed"
        invalid["recognition_run"]["pass_count"] = 2
        invalid["recognition_run"]["refinement"]["status"] = "not_applicable"
        self.assert_schema_invalid(invalid)

        not_executed = copy.deepcopy(failed_initial)
        not_executed_run = not_executed["recognition_run"]
        not_executed_run["status"] = "not_executed"
        not_executed_run["pass_count"] = 0
        not_executed_run["processed_attachment_count"] = 0
        not_executed_run["refinement"]["status"] = "not_applicable"
        for attachment in not_executed_run["attachments"]:
            attachment["status"] = "not_executed"
            attachment["completeness"] = "unavailable"
        self.assert_schema_valid(not_executed)
        for pass_count in [1, 2]:
            invalid = copy.deepcopy(not_executed)
            invalid["recognition_run"]["pass_count"] = pass_count
            self.assert_schema_invalid(invalid)
        for refinement_status, pass_count, detail in [
            ("not_needed", 1, {"reasons": [], "targeted_fields": [], "attachment_indexes": [], "issues": []}),
            (
                "succeeded",
                2,
                {
                    "reasons": ["visible-field omission"],
                    "targeted_fields": ["nominal_weight_or_volume"],
                    "attachment_indexes": [0],
                    "issues": ["refinement completed"],
                },
            ),
            (
                "partial",
                2,
                {
                    "reasons": ["visible-field omission"],
                    "targeted_fields": ["nominal_weight_or_volume"],
                    "attachment_indexes": [0],
                    "issues": ["refinement incomplete"],
                },
            ),
            (
                "failed",
                2,
                {
                    "reasons": ["visible-field omission"],
                    "targeted_fields": ["nominal_weight_or_volume"],
                    "attachment_indexes": [0],
                    "issues": ["refinement failed"],
                },
            ),
        ]:
            with self.subTest(not_executed_refinement=refinement_status):
                invalid = copy.deepcopy(not_executed)
                invalid["recognition_run"]["pass_count"] = pass_count
                invalid["recognition_run"]["refinement"].update(detail)
                invalid["recognition_run"]["refinement"]["status"] = refinement_status
                self.assert_schema_invalid(invalid)

        not_needed = self.fixture("partial-nine-item-order.v3.1.json")
        run = not_needed["recognition_run"]
        self.assertEqual(run["pass_count"], 1)
        self.assertEqual(run["refinement"]["status"], "not_needed")
        self.assertEqual(run["refinement"]["reasons"], [])
        self.assertEqual(run["refinement"]["targeted_fields"], [])
        self.assertEqual(run["refinement"]["attachment_indexes"], [])
        self.assertEqual(run["refinement"]["issues"], [])
        self.assert_schema_valid(not_needed)
        for field, value in [
            ("reasons", ["visible-field omission"]),
            ("targeted_fields", ["nominal_weight_or_volume"]),
            ("attachment_indexes", [0]),
            ("issues", ["unexpected refinement issue"]),
        ]:
            with self.subTest(not_needed_nonempty=field):
                invalid = copy.deepcopy(not_needed)
                invalid["recognition_run"]["refinement"][field] = value
                self.assert_schema_invalid(invalid)
        for pass_count in [0, 2]:
            with self.subTest(not_needed_pass_count=pass_count):
                invalid = copy.deepcopy(not_needed)
                invalid["recognition_run"]["pass_count"] = pass_count
                self.assert_schema_invalid(invalid)

        succeeded = self.fixture("durian-order.v3.1.json")
        for refinement_status, aggregate_status in [
            ("succeeded", "succeeded"),
            ("partial", "partial"),
            ("failed", "partial"),
        ]:
            with self.subTest(refinement_status=refinement_status):
                record = copy.deepcopy(succeeded)
                run = record["recognition_run"]
                run["status"] = aggregate_status
                run["pass_count"] = 2
                refinement = run["refinement"]
                refinement["status"] = refinement_status
                self.assertGreater(len(refinement["reasons"]), 0)
                self.assertGreater(len(refinement["targeted_fields"]), 0)
                self.assertGreater(len(refinement["attachment_indexes"]), 0)
                self.assert_schema_valid(record)

                for pass_count in [0, 1]:
                    with self.subTest(refinement_status=refinement_status, pass_count=pass_count):
                        invalid = copy.deepcopy(record)
                        invalid["recognition_run"]["pass_count"] = pass_count
                        self.assert_schema_invalid(invalid)
                for field in ["reasons", "targeted_fields", "attachment_indexes"]:
                    with self.subTest(refinement_status=refinement_status, empty=field):
                        invalid = copy.deepcopy(record)
                        invalid["recognition_run"]["refinement"][field] = []
                        self.assert_schema_invalid(invalid)

        aggregate_failed = copy.deepcopy(succeeded)
        aggregate_failed["recognition_run"]["status"] = "failed"
        aggregate_failed["recognition_run"]["pass_count"] = 2
        aggregate_failed["recognition_run"]["refinement"]["status"] = "failed"
        self.assert_schema_invalid(aggregate_failed)

    def test_partial_without_refinement_requires_a_partial_attachment(self) -> None:
        record = self.fixture("partial-nine-item-order.v3.1.json")
        run = record["recognition_run"]
        self.assertEqual(run["status"], "partial")
        self.assertEqual(run["refinement"]["status"], "not_needed")
        for attachment in run["attachments"]:
            attachment["status"] = "succeeded"
            attachment["completeness"] = "complete"
            attachment["limitations"] = []
        self.assert_schema_invalid(record)

    def test_refinement_succeeded_allows_empty_issues(self) -> None:
        record = self.fixture("durian-order.v3.1.json")
        refinement = record["recognition_run"]["refinement"]
        self.assertEqual(refinement["status"], "succeeded")
        refinement["issues"] = []
        self.assert_schema_valid(record)

    def test_handoff_selected_scopes_require_executable_content(self) -> None:
        handed_off = self.fixture("handed-off.v3.1.json")

        accounting_only = copy.deepcopy(handed_off)
        accounting_only["handoff"]["selected_scopes"] = ["accounting"]
        accounting_only["inventory_content"] = None
        self.assert_schema_valid(accounting_only)
        self.assert_runtime_handoff_invariants(accounting_only)

        inventory_only = copy.deepcopy(handed_off)
        inventory_only["handoff"]["selected_scopes"] = ["inventory"]
        inventory_only["accounting_content"] = None
        self.assert_schema_valid(inventory_only)
        self.assert_runtime_handoff_invariants(inventory_only)

        invalid_records = {}

        accounting_null = copy.deepcopy(handed_off)
        accounting_null["handoff"]["selected_scopes"] = ["accounting"]
        accounting_null["accounting_content"] = None
        invalid_records["selected accounting is null"] = accounting_null

        accounting_disabled = copy.deepcopy(handed_off)
        accounting_disabled["handoff"]["selected_scopes"] = ["accounting"]
        accounting_disabled["accounting_content"]["executable"] = False
        invalid_records["selected accounting is non-executable"] = accounting_disabled

        inventory_null = copy.deepcopy(handed_off)
        inventory_null["handoff"]["selected_scopes"] = ["inventory"]
        inventory_null["inventory_content"] = None
        invalid_records["selected inventory is null"] = inventory_null

        inventory_disabled = copy.deepcopy(handed_off)
        inventory_disabled["handoff"]["selected_scopes"] = ["inventory"]
        inventory_disabled["inventory_content"]["executable"] = False
        invalid_records["selected inventory is non-executable"] = inventory_disabled

        both_null = copy.deepcopy(handed_off)
        both_null["accounting_content"] = None
        both_null["inventory_content"] = None
        invalid_records["both selected sections are null"] = both_null

        empty_inventory = copy.deepcopy(handed_off)
        empty_inventory["handoff"]["selected_scopes"] = ["inventory"]
        empty_inventory["inventory_content"]["items"] = []
        invalid_records["selected executable inventory is empty"] = empty_inventory

        for name, record in invalid_records.items():
            with self.subTest(mutation=name):
                self.assert_schema_invalid(record)
                with self.assertRaises(AssertionError):
                    self.assert_runtime_handoff_invariants(record)

    def test_successful_targeted_refinement_can_remain_aggregate_partial(self) -> None:
        record = self.fixture("partial-refined-nine-item-order.v3.1.json")
        run = record["recognition_run"]
        self.assertEqual(run["status"], "partial")
        self.assertEqual(run["pass_count"], 2)
        self.assertEqual(run["refinement"]["status"], "succeeded")
        self.assertIn("line_paid_amount", run["refinement"]["targeted_fields"])
        self.assertGreater(len(run["refinement"]["reasons"]), 0)
        self.assertGreater(len(run["refinement"]["targeted_fields"]), 0)
        self.assertEqual(record["facts"]["order"]["hidden_item_kind_count"]["value"], 2)
        self.assertFalse(record["facts"]["order"]["content_complete"]["value"])
        self.assertIn("另有 2 种商品未展开", record["warnings"])
        self.assertEqual(record["preview_state"], "awaiting_confirmation")
        self.assertIsNone(record["handoff"])
        partial_attachments = [
            attachment
            for attachment in run["attachments"]
            if attachment["status"] == "partial"
        ]
        self.assertGreater(len(partial_attachments), 0)
        for attachment in partial_attachments:
            self.assertEqual(attachment["completeness"], "partial")
            self.assertGreater(len(attachment["limitations"]), 0)
        self.assert_schema_valid(record)
        self.assert_runtime_attachment_invariants(record)
        self.assert_runtime_content_invariants(record)

        missing_partial_witness = copy.deepcopy(record)
        for attachment in missing_partial_witness["recognition_run"]["attachments"]:
            attachment["status"] = "succeeded"
            attachment["completeness"] = "complete"
            attachment["limitations"] = []
        self.assert_schema_invalid(missing_partial_witness)

    def test_inventory_view_preserves_count_and_nominal_measurement_separately(self) -> None:
        record = self.fixture("partial-nine-item-order.v3.1.json")
        inventory = {
            item["product_index"]: item for item in record["inventory_content"]["items"]
        }
        self.assertEqual(
            (inventory[0]["quantity"], inventory[0]["quantity_unit"], inventory[0]["weight_or_volume"]),
            (2, None, {"value": 850, "unit": "g"}),
        )
        self.assertEqual(
            (inventory[1]["quantity"], inventory[1]["quantity_unit"], inventory[1]["weight_or_volume"]),
            (1, None, {"value": 1.5, "unit": "L"}),
        )
        self.assertEqual(
            (inventory[4]["quantity"], inventory[4]["quantity_unit"], inventory[4]["weight_or_volume"]),
            (2, None, {"value": 1, "unit": "L"}),
        )
        self.assert_runtime_content_invariants(record)

        for product_index, multiplied_total, invented_unit in [
            (0, 1700, "g"),
            (1, 1500, "ml"),
            (4, 2000, "ml"),
        ]:
            with self.subTest(product_index=product_index):
                invalid_view = copy.deepcopy(record)
                item = invalid_view["inventory_content"]["items"][product_index]
                item["quantity"] = multiplied_total
                item["quantity_unit"] = invented_unit
                item["weight_or_volume"] = None
                self.assert_schema_valid(invalid_view)
                with self.assertRaises(AssertionError):
                    self.assert_runtime_content_invariants(invalid_view)

    def test_every_fixture_content_view_maps_to_its_canonical_product(self) -> None:
        for path in sorted(FIXTURES.glob("*.v3.1.json")):
            with self.subTest(fixture=path.name):
                record = json.loads(path.read_text(encoding="utf-8"))
                self.assert_runtime_content_invariants(record)

    def test_unknown_fact_wrappers_fail_closed_and_known_values_keep_evidence(self) -> None:
        unknown = {
            "textFact": {
                "value": None,
                "confidence": 0,
                "calculated": False,
                "evidence": [],
            },
            "amountFact": {
                "value": None,
                "currency": None,
                "confidence": 0,
                "calculated": False,
                "evidence": [],
            },
            "quantityFact": {
                "value": None,
                "unit": None,
                "confidence": 0,
                "calculated": False,
                "evidence": [],
            },
            "dateFact": {
                "value": None,
                "confidence": 0,
                "calculated": False,
                "evidence": [],
            },
            "booleanFact": {
                "value": None,
                "confidence": 0,
                "calculated": False,
                "evidence": [],
            },
            "countFact": {
                "value": None,
                "confidence": 0,
                "calculated": False,
                "evidence": [],
            },
        }
        known = {
            "textFact": {"value": "known", "confidence": 1, "calculated": False},
            "amountFact": {
                "value": 1,
                "currency": "CNY",
                "confidence": 1,
                "calculated": False,
            },
            "quantityFact": {
                "value": 1,
                "unit": "kg",
                "confidence": 1,
                "calculated": False,
            },
            "dateFact": {"value": "2026-08-06", "confidence": 1, "calculated": False},
            "booleanFact": {"value": True, "confidence": 1, "calculated": False},
            "countFact": {"value": 1, "confidence": 1, "calculated": False},
        }
        evidence = [{"source": "visible_label", "value": "known"}]

        for name, fact in unknown.items():
            with self.subTest(wrapper=name, state="valid unknown"):
                self.assert_definition_valid(name, fact)
            for field, value in [
                ("confidence", 0.5),
                ("calculated", True),
                ("evidence", evidence),
            ]:
                with self.subTest(wrapper=name, invalid_unknown=field):
                    invalid = copy.deepcopy(fact)
                    invalid[field] = value
                    self.assert_definition_invalid(name, invalid)

            with self.subTest(wrapper=name, state="known with evidence"):
                valid_known = {**known[name], "evidence": evidence}
                self.assert_definition_valid(name, valid_known)
                invalid_known = copy.deepcopy(valid_known)
                invalid_known["evidence"] = []
                self.assert_definition_invalid(name, invalid_known)

        invalid_amount = copy.deepcopy(unknown["amountFact"])
        invalid_amount["currency"] = "CNY"
        self.assert_definition_invalid("amountFact", invalid_amount)

        invalid_quantity = copy.deepcopy(unknown["quantityFact"])
        invalid_quantity["unit"] = "kg"
        self.assert_definition_invalid("quantityFact", invalid_quantity)

        item_fact = {
            "item_name": {**known["textFact"], "evidence": evidence},
            "quantity": {**known["quantityFact"], "evidence": evidence},
            "specification": copy.deepcopy(unknown["textFact"]),
            "line_status": {**known["textFact"], "evidence": evidence},
            "item_type": "food",
            "evidence": evidence,
        }
        self.assert_definition_valid("itemFact", item_fact)
        invalid_item_fact = copy.deepcopy(item_fact)
        invalid_item_fact["specification"]["confidence"] = 0.5
        self.assert_definition_invalid("itemFact", invalid_item_fact)
        invalid_item_evidence = copy.deepcopy(item_fact)
        invalid_item_evidence["evidence"] = []
        self.assert_definition_invalid("itemFact", invalid_item_evidence)

    def test_initial_preview_has_no_handoff_and_handed_off_is_singular(self) -> None:
        for name, recognition_status in [
            ("durian-order.v3.1.json", "succeeded"),
            ("partial-nine-item-order.v3.1.json", "partial"),
        ]:
            with self.subTest(fixture=name):
                record = self.fixture(name)
                self.assertEqual(record["recognition_run"]["status"], recognition_status)
                self.assertEqual(record["preview_state"], "awaiting_confirmation")
                self.assertIsNone(record["handoff"])

        initial_preview = self.fixture("durian-order.v3.1.json")
        handed_off = self.fixture("handed-off.v3.1.json")
        self.assertEqual(handed_off["preview_state"], "handed_off")
        self.assertIsNotNone(handed_off["handoff"])
        self.assertEqual(handed_off["preview_id"], initial_preview["preview_id"])
        self.assertEqual(handed_off["handoff"]["preview_id"], initial_preview["preview_id"])
        self.assert_schema_valid(handed_off)
        self.assert_runtime_handoff_invariants(handed_off)

        mismatched_handoff = copy.deepcopy(handed_off)
        handoff_preview_id = mismatched_handoff["handoff"]["preview_id"]
        replacement = "0" if handoff_preview_id[-1] != "0" else "1"
        mismatched_handoff["handoff"]["preview_id"] = handoff_preview_id[:-1] + replacement
        self.assert_schema_valid(mismatched_handoff)
        with self.assertRaises(AssertionError):
            self.assert_runtime_handoff_invariants(mismatched_handoff)

        missing_handoff = copy.deepcopy(handed_off)
        missing_handoff["handoff"] = None
        self.assert_schema_invalid(missing_handoff)

        corrected_preview = self.fixture("corrected-preview.v3.1.json")
        self.assertEqual(corrected_preview["preview_state"], "awaiting_confirmation")
        self.assertNotEqual(corrected_preview["preview_id"], initial_preview["preview_id"])
        self.assertIsNone(corrected_preview["handoff"])
        initial_fact = initial_preview["facts"]["products"][0]["actual_weight_or_volume"]
        corrected_fact = corrected_preview["facts"]["products"][0][
            "actual_weight_or_volume"
        ]
        self.assertNotEqual(corrected_fact, initial_fact)
        self.assertEqual(corrected_fact["evidence"][0]["source"], "user_text")
        self.assertEqual(
            corrected_preview["accounting_content"]["items"][0][
                "actual_weight_or_volume"
            ],
            {"value": corrected_fact["value"], "unit": corrected_fact["unit"]},
        )
        self.assertNotEqual(
            corrected_preview["accounting_content"], initial_preview["accounting_content"]
        )
        self.assertEqual(
            corrected_preview["inventory_content"]["items"][0]["weight_or_volume"],
            {"value": corrected_fact["value"], "unit": corrected_fact["unit"]},
        )
        self.assertNotEqual(
            corrected_preview["inventory_content"], initial_preview["inventory_content"]
        )
        self.assert_schema_valid(corrected_preview)
        self.assert_runtime_content_invariants(corrected_preview)

        duplicate_confirmation = self.fixture("duplicate-confirmation.v3.1.json")
        self.assertEqual(duplicate_confirmation["preview_state"], "handed_off")
        self.assertEqual(duplicate_confirmation["preview_id"], handed_off["preview_id"])
        self.assertEqual(duplicate_confirmation["handoff"], handed_off["handoff"])
        self.assertEqual(
            duplicate_confirmation["handoff"]["selected_scopes"],
            handed_off["handoff"]["selected_scopes"],
        )
        self.assert_schema_valid(duplicate_confirmation)
        self.assert_runtime_handoff_invariants(duplicate_confirmation)


if __name__ == "__main__":
    unittest.main()
