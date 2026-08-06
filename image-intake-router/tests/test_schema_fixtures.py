import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = SKILL_ROOT / "templates" / "image-intake-router.schema.json"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class RouterV3FixtureSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema, format_checker=FormatChecker())

    def fixture(self, name: str) -> dict:
        path = FIXTURES / name
        self.assertTrue(path.is_file(), f"missing v3 fixture: {name}")
        return json.loads(path.read_text(encoding="utf-8"))

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

    def test_every_shipped_v3_fixture_is_a_complete_draft_2020_12_instance(self) -> None:
        fixtures = sorted(FIXTURES.glob("*.v3.json"))
        self.assertGreater(len(fixtures), 0)
        for path in fixtures:
            with self.subTest(fixture=path.name):
                self.assert_schema_valid(json.loads(path.read_text(encoding="utf-8")))

    def test_durian_refinement_preserves_visible_detail(self) -> None:
        record = self.fixture("durian-order.v3.json")
        self.assertEqual(record["recognition_run"]["pass_count"], 2)
        self.assertEqual(record["recognition_run"]["refinement"]["status"], "succeeded")
        item = record["accounting_content"]["items"][0]
        self.assertEqual(item["full_name"], "金枕榴莲")
        self.assertEqual(item["nominal_weight_or_volume"], {"value": 2.1, "unit": "kg"})
        self.assertEqual(item["quantity"], 1)
        self.assertEqual(item["line_paid_amount"], 119.00)
        self.assertEqual(item["refund_amount"], 12.92)
        self.assertIn("重量误差 228g", record["cleaned_text"])

    def test_hidden_items_warn_without_triggering_refinement(self) -> None:
        record = self.fixture("partial-nine-item-order.v3.json")
        self.assertEqual(record["recognition_run"]["pass_count"], 1)
        self.assertEqual(record["recognition_run"]["refinement"]["status"], "not_needed")
        self.assertEqual(len(record["accounting_content"]["items"]), 7)
        self.assertEqual(len(record["inventory_content"]["items"]), 7)
        self.assertIn("另有 2 种商品未展开", record["warnings"])

    def test_failed_recognition_has_no_actionable_content_or_handoff(self) -> None:
        record = self.fixture("failed-recognition.v3.json")
        self.assertEqual(record["preview_state"], "failed")
        self.assertEqual(record["recognition_run"]["pass_count"], 0)
        self.assertIsNone(record["cleaned_text"])
        self.assertIsNone(record["accounting_content"])
        self.assertIsNone(record["inventory_content"])
        self.assertIsNone(record["handoff"])


if __name__ == "__main__":
    unittest.main()
