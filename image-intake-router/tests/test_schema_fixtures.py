import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = SKILL_ROOT / "templates" / "image-intake-router.schema.json"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class RouterV21FixtureSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(
            cls.schema,
            format_checker=FormatChecker(),
        )

    def fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def validation_messages(self, instance: object) -> list[str]:
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
        for error in sorted(
            self.validator.iter_errors(instance),
            key=lambda item: [str(part) for part in item.absolute_path],
        ):
            rendered.extend(messages(error))
        return rendered

    def assert_schema_valid(self, instance: object) -> None:
        messages = self.validation_messages(instance)
        self.assertEqual(messages, [], "\n".join(messages))

    def assert_schema_invalid(self, instance: object) -> None:
        self.assertNotEqual(self.validation_messages(instance), [])

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
        if run["status"] in {"succeeded", "partial"}:
            self.assertEqual(run["processed_attachment_count"], run["attachment_count"])

    def assert_diet_arrays_are_parallel(self, record: dict) -> None:
        diet = record["diet_projection"]
        products = diet["business_products"]
        items = diet["items"]
        adapter_payload = diet["adapter_payload"]
        audit = diet["item_audit"]
        self.assertEqual(len(items), len(products))
        self.assertEqual(len(items), len(adapter_payload))
        self.assertEqual(len(items), len(audit))
        for index, (item, product, adapter, audit_row) in enumerate(
            zip(items, products, adapter_payload, audit)
        ):
            self.assertEqual(adapter["source_product_index"], index)
            self.assertEqual(item["food_name"], product["full_name"]["value"])
            self.assertEqual(item["normalized_name"], product["normalized_name"]["value"])
            self.assertEqual((item["quantity"], item["unit"]), (adapter["quantity"], adapter["unit"]))
            self.assertIn(product["specification"]["value"], item["source_text"])
            self.assertIsNone(item["expires_at"])
            self.assertEqual(audit_row["item_index"], index)
            self.assertEqual(audit_row["order_status"], "purchased_and_received")
            self.assertGreaterEqual(len(audit_row["evidence"]), 1)

    def test_every_shipped_v21_fixture_is_a_complete_draft_2020_12_instance(self) -> None:
        fixtures = sorted(FIXTURES.glob("*.v2.1.json"))
        self.assertGreater(len(fixtures), 0)
        for path in fixtures:
            with self.subTest(fixture=path.name):
                record = json.loads(path.read_text(encoding="utf-8"))
                self.assert_schema_valid(record)
                self.assert_runtime_attachment_invariants(record)

    def test_partial_order_routes_only_seven_visible_products_and_discloses_two_hidden(self) -> None:
        record = self.fixture("partial-nine-item-order.v2.1.json")
        run = record["recognition_run"]
        self.assertEqual(run["status"], "partial")
        self.assertEqual(run["attachment_count"], 1)
        self.assertEqual(run["processed_attachment_count"], 1)
        self.assertEqual(len(run["attachments"]), 1)
        self.assertTrue(all(row["status"] != "not_executed" for row in run["attachments"]))
        self.assertEqual(run["attachments"][0]["status"], "partial")
        self.assertEqual(run["attachments"][0]["completeness"], "partial")
        self.assertGreaterEqual(len(run["attachments"][0]["limitations"]), 1)

        order = record["facts"]["order"]
        self.assertEqual(order["declared_item_kind_count"]["value"], 9)
        self.assertEqual(order["recognized_item_kind_count"]["value"], 7)
        self.assertEqual(order["hidden_item_kind_count"]["value"], 2)
        self.assertTrue(order["has_unexpanded_items"]["value"])
        self.assertFalse(order["content_complete"]["value"])

        diet = record["diet_projection"]
        self.assert_diet_arrays_are_parallel(record)
        expected_names = ["甜玉米", "鲜牛奶", "黄瓜", "西兰花", "豆浆", "云南生菜", "香蕉"]
        self.assertEqual([row["food_name"] for row in diet.get("items", [])], expected_names)
        self.assertEqual(len(diet["business_products"]), 7)
        self.assertEqual(len(diet["adapter_payload"]), 7)
        self.assertEqual([row["item_index"] for row in diet.get("item_audit", [])], list(range(7)))
        self.assertTrue(all(row["order_status"] == "purchased_and_received" for row in diet.get("item_audit", [])))
        self.assertEqual(diet.get("excluded_items"), [])
        self.assertEqual(
            [(row["item_name"], row["status"]) for row in diet.get("uncertain_items", [])],
            [("未展开商品（2种）", "unexpanded")],
        )
        self.assertEqual(
            diet["uncertain_items"][0]["evidence"],
            [{"source": "visible_label", "value": "还有2种商品"}],
        )
        self.assertEqual(record["expense_projection"]["omitted_item_count"], 2)

    def test_durian_order_remains_succeeded_complete_with_a_parallel_diet_audit(self) -> None:
        record = self.fixture("durian-order.v2.1.json")
        run = record["recognition_run"]
        self.assertEqual(run["status"], "succeeded")
        self.assertEqual(run["processed_attachment_count"], run["attachment_count"])
        self.assertEqual(
            [(row["status"], row["completeness"], row["limitations"]) for row in run["attachments"]],
            [("succeeded", "complete", [])],
        )

        diet = record["diet_projection"]
        self.assert_diet_arrays_are_parallel(record)
        self.assertEqual([row["food_name"] for row in diet.get("items", [])], ["金枕榴莲"])
        self.assertEqual([row["item_index"] for row in diet.get("item_audit", [])], [0])
        self.assertEqual(
            [row["order_status"] for row in diet.get("item_audit", [])],
            ["purchased_and_received"],
        )
        self.assertEqual(diet.get("excluded_items"), [])
        self.assertEqual(diet.get("uncertain_items"), [])
        self.assertEqual(
            {
                field: diet["items"][0][field]
                for field in ["display_quantity", "display_unit", "base_quantity_per_display_unit"]
            },
            {
                "display_quantity": 1,
                "display_unit": "粒",
                "base_quantity_per_display_unit": 2100,
            },
        )

    def test_succeeded_status_cannot_spoof_useful_partial_recognition(self) -> None:
        record = self.fixture("partial-nine-item-order.v2.1.json")
        record["recognition_run"]["status"] = "succeeded"
        self.assert_schema_invalid(record)

    def test_each_required_diet_projection_array_is_schema_enforced(self) -> None:
        record = self.fixture("durian-order.v2.1.json")
        self.assert_schema_valid(record)
        for field in ["items", "item_audit", "excluded_items", "uncertain_items"]:
            with self.subTest(field=field):
                mutated = copy.deepcopy(record)
                mutated["diet_projection"].pop(field)
                self.assert_schema_invalid(mutated)

    def test_failed_and_not_executed_full_records_remain_schema_valid_and_fail_closed(self) -> None:
        baseline = self.fixture("durian-order.v2.1.json")
        for status in ["failed", "not_executed"]:
            with self.subTest(status=status):
                record = copy.deepcopy(baseline)
                record["preview_state"] = "draft"
                record["expense_projection"] = None
                record["diet_projection"] = None
                record["quality"]["fact_set_status"] = "unavailable"
                record["quality"]["issues"] = ["vision unavailable"]
                run = record["recognition_run"]
                run["status"] = status
                run["issues"] = ["vision unavailable"]
                attachment = run["attachments"][0]
                attachment["status"] = status
                attachment["completeness"] = "unavailable"
                attachment["limitations"] = ["vision unavailable"]
                if status == "not_executed":
                    run["processed_attachment_count"] = 0
                    record["quality"]["visual_capability"] = "unavailable"
                self.assert_schema_valid(record)
                self.assertEqual(record["preview_state"], "draft")
                self.assertIsNone(record["expense_projection"])
                self.assertIsNone(record["diet_projection"])
                self.assertEqual(record["quality"]["fact_set_status"], "unavailable")

    def test_runtime_validation_rejects_cross_field_count_and_index_mismatches(self) -> None:
        baseline = self.fixture("partial-nine-item-order.v2.1.json")
        mutations = {
            "source image count": lambda record: record["source"].__setitem__("image_count", 2),
            "attachment count": lambda record: record["recognition_run"].__setitem__("attachment_count", 2),
            "derived processed count": lambda record: record["recognition_run"].__setitem__("processed_attachment_count", 2),
            "contiguous attachment index": lambda record: record["recognition_run"]["attachments"][0].__setitem__("attachment_index", 1),
        }
        for mismatch, mutate in mutations.items():
            with self.subTest(mismatch=mismatch):
                record = copy.deepcopy(baseline)
                mutate(record)
                self.assert_schema_valid(record)
                with self.assertRaises(AssertionError):
                    self.assert_runtime_attachment_invariants(record)


if __name__ == "__main__":
    unittest.main()
