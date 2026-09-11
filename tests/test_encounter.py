import unittest

from evia_journal.core import analyze as journal
from evia_journal.core import verify_records
from test_contract import sample

from encounter_kit.core import analyze


class EncounterTests(unittest.TestCase):
    def events(self, *actions):
        data = sample()
        data["events"] = [
            {"atMs": i * 1000, "action": action, "choice": 0} for i, action in enumerate(actions)
        ]
        data["nowMs"] = len(actions) * 1000
        return data

    def test_no_event_does_not_start_automatically(self):
        data = sample()
        data["nowMs"] = 90000
        self.assertEqual(analyze(data)["state"]["status"], "ready")

    def test_end_before_start_is_valid_and_has_no_active_time(self):
        report = analyze(sample("declined"))
        self.assertEqual(report["state"]["status"], "ended")
        self.assertEqual(report["state"]["activeMs"], 0)

    def test_pause_time_is_excluded_from_active_duration(self):
        report = analyze(sample("paused"))
        state = report["state"]
        self.assertEqual(state["activeMs"], 60000)
        self.assertEqual(state["pausedMs"], 30000)
        self.assertEqual(state["skipped"], ["notice"])
        self.assertEqual(state["completed"], ["arrive", "close"])

    def test_ongoing_pause_does_not_advance(self):
        data = self.events("start", "pause")
        data["nowMs"] = 100000
        state = analyze(data)["state"]
        self.assertEqual(state["status"], "paused")
        self.assertEqual(state["cardIndex"], 0)
        self.assertEqual(state["activeMs"], 1000)
        self.assertEqual(state["pausedMs"], 99000)

    def test_next_requires_an_explicit_choice(self):
        with self.assertRaises(ValueError):
            analyze(self.events("start", "next"))

    def test_choice_is_cleared_at_next_card(self):
        report = analyze(self.events("start", "choose", "next"))
        self.assertIsNone(report["state"]["choice"])
        self.assertNotIn("next", report["state"]["legalActions"])

    def test_skip_does_not_require_a_choice(self):
        report = analyze(self.events("start", "skip"))
        self.assertEqual(report["state"]["skipped"], ["arrive"])

    def test_pause_blocks_choices_and_card_changes(self):
        for action in ("next", "choose", "skip", "pause"):
            with self.subTest(action=action), self.assertRaises(ValueError):
                analyze(self.events("start", "pause", action))

    def test_end_is_terminal(self):
        for action in ("start", "resume", "choose", "end"):
            with self.subTest(action=action), self.assertRaises(ValueError):
                analyze(self.events("end", action))

    def test_unknown_choice_rejected(self):
        data = self.events("start", "choose")
        data["events"][1]["choice"] = 5
        with self.assertRaises(ValueError):
            analyze(data)

    def test_future_and_reverse_time_rejected(self):
        data = self.events("start", "pause")
        data["events"][0]["atMs"] = 10000
        with self.assertRaises(ValueError):
            analyze(data)
        data = self.events("start", "pause")
        data["events"][0]["atMs"] = 1500
        with self.assertRaises(ValueError):
            analyze(data)

    def test_pause_then_end_closes_duration(self):
        data = self.events("start", "pause", "end")
        data["nowMs"] = 100000
        state = analyze(data)["state"]
        self.assertEqual(state["activeMs"], 1000)
        self.assertEqual(state["pausedMs"], 1000)

    def test_declined_session_never_receives_completion_score(self):
        report = analyze(sample("declined"))
        self.assertEqual(report["state"]["completed"], [])
        self.assertNotIn("score", report)

    def test_real_public_journal_contract_and_chain(self):
        report = analyze(sample("paused"))
        self.assertEqual(journal(report["journalInput"]), report["journal"])
        self.assertTrue(
            verify_records(report["journal"]["records"], report["journal"]["rootHash"])["valid"]
        )
        for event in report["journalInput"]["events"]:
            self.assertEqual(set(event), {"id", "atMs", "sessionId", "kind", "outcome"})

    def test_retention_affects_exported_journal_only(self):
        data = sample("paused")
        data["retentionMs"] = 10000
        report = analyze(data)
        self.assertTrue(all(row["atMs"] >= 80000 for row in report["journal"]["records"]))
        self.assertGreater(report["journal"]["excluded"], 0)
        self.assertEqual(len(report["timeline"]), 8)

    def test_same_timestamp_events_keep_input_order(self):
        data = self.events("start", "choose", "pause")
        for event in data["events"]:
            event["atMs"] = 0
        self.assertEqual(analyze(data)["state"]["status"], "paused")


if __name__ == "__main__":
    unittest.main()
