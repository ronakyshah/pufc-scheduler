import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import config
from main import assign_referees, parse_cli_arguments, read_local_schedule, read_referee_pool


class RefereeAssignmentTests(unittest.TestCase):
    def setUp(self):
        self.games = read_local_schedule()
        self.referees = read_referee_pool()
        self.assigned = assign_referees(self.games, self.referees)

    def test_assignments_are_populated(self):
        self.assertTrue(self.assigned["Referee"].notna().any())
        self.assertTrue(self.assigned["AR #1"].notna().any())

    def test_grade_3_and_4_games_use_under_20_referees_for_center(self):
        grade_3_4 = self.assigned[self.assigned["Grade"].isin([3, 4])]
        if grade_3_4.empty:
            self.skipTest("No grade 3/4 games found in local sample")

        referee_lookup = self.referees.set_index("Name")["Age"].to_dict()
        for _, row in grade_3_4.iterrows():
            self.assertLess(referee_lookup[row["Referee"]], 20)

    def test_other_official_slot_remains_unassigned(self):
        self.assertTrue(self.assigned["Other Official"].isna().all())

    def test_cli_parser_defaults_to_local_mode_and_allows_schedule_path(self):
        parsed = parse_cli_arguments(["/tmp/custom.csv"])
        self.assertEqual(parsed["mode"], "local")
        self.assertEqual(parsed["schedule_path"], "/tmp/custom.csv")

        parsed = parse_cli_arguments(["google", "--schedule-file", "/tmp/another.csv"])
        self.assertEqual(parsed["mode"], "google")
        self.assertEqual(parsed["schedule_path"], "/tmp/another.csv")

    def test_referees_have_balanced_assignment_counts(self):
        roles = ["Referee", "AR #1", "AR #2", "Other Official"]
        counts = {}
        for role in roles:
            for name in self.assigned[role].dropna():
                counts[name] = counts.get(name, 0) + 1

        self.assertTrue(counts)
        for name, count in counts.items():
            self.assertGreaterEqual(count, 1)
            self.assertLessEqual(count, 3)


if __name__ == "__main__":
    unittest.main()
