"""
PulseTrack Test Suite
Comprehensive unit tests for the Screen Time Monitor
"""

import unittest
from datetime import datetime, timedelta
from tracker import ScreenTimeTracker
from database import Database
from config import STATE_ACTIVE, STATE_IDLE, STATE_LOCKED, STATE_SLEEP


class TestDatabase(unittest.TestCase):
    """Test database operations"""

    def setUp(self):
        """Set up test database"""
        self.db = Database()
        self.db._db_path = ":memory:"  # Use in-memory database
        self.db.initialize()

    def tearDown(self):
        """Clean up"""
        self.db.close()

    def test_record_state_session(self):
        """Test recording state sessions"""
        now = datetime.now()
        start = now - timedelta(hours=1)
        end = now
        duration = 3600

        self.db.record_state_session(STATE_ACTIVE, start, end, duration)
        self.assertTrue(True)  # If no exception, test passed

    def test_record_app_session(self):
        """Test recording app sessions"""
        now = datetime.now()
        start = now - timedelta(minutes=30)
        end = now
        duration = 1800

        self.db.record_app_session("code.exe", "main.py - VS Code", start, end, duration)
        self.assertTrue(True)

    def test_record_system_event(self):
        """Test recording system events"""
        self.db.record_system_event("BOOT", "System started")
        self.assertTrue(True)

    def test_get_daily_summary(self):
        """Test getting daily summary"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        summary = self.db.get_daily_summary(date_str)

        self.assertIsNotNone(summary)
        self.assertIn("state_totals", summary)
        self.assertIn("app_totals", summary)

    def test_format_seconds(self):
        """Test seconds formatting"""
        result = self.db._format_seconds(3661)
        self.assertEqual(result, "1h 1m 1s")

        result = self.db._format_seconds(60)
        self.assertEqual(result, "0h 1m 0s")

        result = self.db._format_seconds(1)
        self.assertEqual(result, "0h 0m 1s")


class TestTracker(unittest.TestCase):
    """Test tracker functionality"""

    def test_tracker_singleton(self):
        """Test that ScreenTimeTracker is a singleton"""
        tracker1 = ScreenTimeTracker()
        tracker2 = ScreenTimeTracker()
        self.assertIs(tracker1, tracker2)

    def test_state_determination(self):
        """Test state determination logic"""
        tracker = ScreenTimeTracker()

        # Test SLEEP state
        result = tracker._determine_state(0, False, True)
        self.assertEqual(result, STATE_SLEEP)

        # Test LOCKED state
        result = tracker._determine_state(0, True, False)
        self.assertEqual(result, STATE_LOCKED)

        # Test IDLE state
        result = tracker._determine_state(65, False, False)
        self.assertEqual(result, STATE_IDLE)

        # Test ACTIVE state
        result = tracker._determine_state(30, False, False)
        self.assertEqual(result, STATE_ACTIVE)


class TestConfiguration(unittest.TestCase):
    """Test configuration values"""

    def test_state_colors_defined(self):
        """Test that state colors are defined"""
        from config import STATE_COLORS

        self.assertIn(STATE_ACTIVE, STATE_COLORS)
        self.assertIn(STATE_IDLE, STATE_COLORS)
        self.assertIn(STATE_LOCKED, STATE_COLORS)
        self.assertIn(STATE_SLEEP, STATE_COLORS)

    def test_state_emojis_defined(self):
        """Test that state emojis are defined"""
        from config import STATE_EMOJIS

        self.assertIn(STATE_ACTIVE, STATE_EMOJIS)
        self.assertIn(STATE_IDLE, STATE_EMOJIS)
        self.assertIn(STATE_LOCKED, STATE_EMOJIS)
        self.assertIn(STATE_SLEEP, STATE_EMOJIS)

    def test_polling_intervals(self):
        """Test that polling intervals are reasonable"""
        from config import POLL_INTERVAL_SECONDS, IDLE_THRESHOLD_SECONDS

        self.assertGreater(POLL_INTERVAL_SECONDS, 0)
        self.assertGreater(IDLE_THRESHOLD_SECONDS, POLL_INTERVAL_SECONDS)


class TestPlatformAdapter(unittest.TestCase):
    """Test platform adapter selection"""

    def test_platform_adapter_creation(self):
        """Test that platform adapter can be created"""
        from platforms import get_platform_adapter

        try:
            adapter = get_platform_adapter()
            self.assertIsNotNone(adapter)
        except RuntimeError as e:
            # Acceptable for unsupported platforms
            self.assertIn("Unsupported platform", str(e))


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()
