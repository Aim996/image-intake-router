import copy
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

    def assert_runtime_handoff_invariants(self, record: dict) -> None:
        handoff = record["handoff"]
        if handoff is not None:
            self.assertEqual(record["preview_id"], handoff["preview_id"])

    def test_every_shipped_v3_fixture_is_a_complete_draft_2020_12_instance(self) -> None:
        fixtures = sorted(FIXTURES.glob("*.v3.json"))
        self.assertGreater(len(fixtures), 0)
        for path in fixtures:
            with self.subTest(fixture=path.name):
                self.assert_schema_valid(json.loads(path.read_text(encoding="utf-8")))

    def test_v3_fixtures_preserve_exact_attachment_coverage_and_count(self) -> None:
        for name in [
            "durian-order.v3.json",
            "partial-nine-item-order.v3.json",
            "failed-recognition.v3.json",
        ]:
            with self.subTest(fixture=name):
                self.assert_runtime_attachment_invariants(self.fixture(name))

    def test_attachment_coverage_helper_rejects_count_and_index_mismatches(self) -> None:
        baseline = self.fixture("partial-nine-item-order.v3.json")
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

    def test_failed_and_not_executed_recognition_fail_closed(self) -> None:
        baseline = self.fixture("failed-recognition.v3.json")
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

                actionable = self.fixture("durian-order.v3.json")
                handed_off = self.fixture("handed-off.v3.json")
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
        failed_initial = self.fixture("failed-recognition.v3.json")
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

        not_needed = self.fixture("partial-nine-item-order.v3.json")
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

        succeeded = self.fixture("durian-order.v3.json")
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
                self.assertGreater(len(refinement["issues"]), 0)
                self.assert_schema_valid(record)

                for pass_count in [0, 1]:
                    with self.subTest(refinement_status=refinement_status, pass_count=pass_count):
                        invalid = copy.deepcopy(record)
                        invalid["recognition_run"]["pass_count"] = pass_count
                        self.assert_schema_invalid(invalid)
                for field in ["reasons", "targeted_fields", "attachment_indexes", "issues"]:
                    with self.subTest(refinement_status=refinement_status, empty=field):
                        invalid = copy.deepcopy(record)
                        invalid["recognition_run"]["refinement"][field] = []
                        self.assert_schema_invalid(invalid)

        aggregate_failed = copy.deepcopy(succeeded)
        aggregate_failed["recognition_run"]["status"] = "failed"
        aggregate_failed["recognition_run"]["pass_count"] = 2
        aggregate_failed["recognition_run"]["refinement"]["status"] = "failed"
        self.assert_schema_invalid(aggregate_failed)

    def test_initial_preview_has_no_handoff_and_handed_off_is_singular(self) -> None:
        for name, recognition_status in [
            ("durian-order.v3.json", "succeeded"),
            ("partial-nine-item-order.v3.json", "partial"),
        ]:
            with self.subTest(fixture=name):
                record = self.fixture(name)
                self.assertEqual(record["recognition_run"]["status"], recognition_status)
                self.assertEqual(record["preview_state"], "awaiting_confirmation")
                self.assertIsNone(record["handoff"])

        handed_off = self.fixture("handed-off.v3.json")
        self.assertEqual(handed_off["preview_state"], "handed_off")
        self.assertIsNotNone(handed_off["handoff"])
        self.assert_schema_valid(handed_off)
        self.assert_runtime_handoff_invariants(handed_off)

        missing_handoff = copy.deepcopy(handed_off)
        missing_handoff["handoff"] = None
        self.assert_schema_invalid(missing_handoff)

        corrected_preview = self.fixture("corrected-preview.v3.json")
        self.assertEqual(corrected_preview["preview_state"], "awaiting_confirmation")
        self.assertNotEqual(corrected_preview["preview_id"], handed_off["preview_id"])
        self.assertIsNone(corrected_preview["handoff"])
        self.assert_schema_valid(corrected_preview)

        duplicate_confirmation = self.fixture("duplicate-confirmation.v3.json")
        self.assertEqual(duplicate_confirmation["preview_id"], handed_off["preview_id"])
        self.assertEqual(duplicate_confirmation["handoff"], handed_off["handoff"])
        self.assert_schema_valid(duplicate_confirmation)
        self.assert_runtime_handoff_invariants(duplicate_confirmation)


if __name__ == "__main__":
    unittest.main()
