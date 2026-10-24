import unittest
from pathlib import Path
from screener.config import Config
from screener.storage import Storage
from screener.notifier import Notifier
from screener.tracker import ScreenTimeTracker, TrackerState
from screener.instance import SingleInstance
from screener.startup import is_startup_enabled, enable_startup, disable_startup

class TestScreener(unittest.TestCase):
    def setUp(self):
        self.config = Config(
            work_duration_minutes=1,
            break_duration_minutes=1,
            idle_threshold_seconds=2,
            sound_enabled=False,
            notification_enabled=False,
            auto_complete_break=True
        )
        test_storage_path = Path("test_stats.json")
        if test_storage_path.exists():
            test_storage_path.unlink()
        self.storage = Storage(file_path=test_storage_path)
        self.notifier = Notifier(sound_enabled=False, notification_enabled=False)
        self.tracker = ScreenTimeTracker(self.config, self.storage, self.notifier)

    def tearDown(self):
        test_storage_path = Path("test_stats.json")
        if test_storage_path.exists():
            test_storage_path.unlink()

    def test_initial_state(self):
        self.assertEqual(self.tracker.state, TrackerState.ACTIVE)
        self.assertEqual(self.tracker.session_active_seconds, 0.0)

    def test_postpone_break(self):
        self.tracker.session_active_seconds = 59.0
        self.tracker.postpone_break(minutes=2)
        self.assertEqual(self.tracker.session_active_seconds, 0.0)
        self.assertEqual(self.tracker.postpone_count, 1)

    def test_skip_break(self):
        self.tracker.session_active_seconds = 60.0
        self.tracker.skip_break()
        self.assertEqual(self.tracker.session_active_seconds, 0.0)
        today = self.storage.get_today_stats()
        self.assertEqual(today["breaks_skipped"], 1)

    def test_start_and_finish_break(self):
        self.tracker.start_break()
        self.assertEqual(self.tracker.state, TrackerState.ON_BREAK)
        self.assertEqual(self.tracker.break_remaining_seconds, 60.0)

        self.tracker.finish_break(auto_detected=False)
        self.assertEqual(self.tracker.state, TrackerState.ACTIVE)
        self.assertEqual(self.tracker.session_active_seconds, 0.0)
        today = self.storage.get_today_stats()
        self.assertEqual(today["breaks_completed"], 1)

    def test_storage_accumulation(self):
        self.storage.add_active_time(15.5)
        self.storage.add_idle_time(30.0)
        today = self.storage.get_today_stats()
        self.assertEqual(today["active_seconds"], 15.5)
        self.assertEqual(today["idle_seconds"], 30.0)

    def test_single_instance(self):
        inst1 = SingleInstance(port=49299)
        self.assertTrue(inst1.check_or_register())

        inst2 = SingleInstance(port=49299)
        self.assertFalse(inst2.check_or_register())

        inst1.close()

    def test_daily_limit_alert(self):
        self.config.daily_limit_hours = 1.0  # 1 hour
        self.storage.add_active_time(3600.0) # 1 hour
        self.tracker.update()
        self.assertTrue(self.tracker.daily_limit_warned)

if __name__ == "__main__":
    unittest.main()
