import unittest
import tempfile
import os
import json
import threading
from datetime import datetime, timezone, timedelta
import sys

# Ensure bridge module is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from bridge.capacity import CapacityStore, is_valid_label, validate_percent, validate_timestamp

class TestCapacityStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = self.temp_dir.name
        self.store = CapacityStore(self.project_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_record_show_roundtrip(self):
        now = datetime.now(timezone.utc).isoformat()
        self.store.record("test-group", "5m", 5, 50.0, now)

        res = self.store.show("test-group")
        self.assertIn("test-group", res)
        self.assertIn("5m", res["test-group"])
        w = res["test-group"]["5m"]
        self.assertEqual(w["status"], "fresh")
        self.assertEqual(w["usable_remaining_percent"], 50.0)
        self.assertEqual(w["source"], "manual")
        self.assertEqual(w["window_minutes"], 5)

    def test_multiple_windows_groups(self):
        now = datetime.now(timezone.utc).isoformat()
        self.store.record("group1", "w1", 10, 20.0, now)

        # Simulate time passing by using past times
        earlier = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        self.store.record("group1", "w2", 20, 30.0, earlier)

        even_earlier = (datetime.now(timezone.utc) - timedelta(seconds=2)).isoformat()
        self.store.record("group2", "w1", 15, 40.0, even_earlier)

        res = self.store.show()
        self.assertIn("group1", res)
        self.assertIn("group2", res)
        self.assertEqual(res["group1"]["w1"]["usable_remaining_percent"], 20.0)
        self.assertEqual(res["group1"]["w2"]["usable_remaining_percent"], 30.0)
        self.assertEqual(res["group2"]["w1"]["usable_remaining_percent"], 40.0)

    def test_bounds_nan_bool(self):
        now = datetime.now(timezone.utc).isoformat()

        with self.assertRaises(ValueError):
            self.store.record("g", "w", 5, -1, now)
        with self.assertRaises(ValueError):
            self.store.record("g", "w", 5, 101, now)
        with self.assertRaises(ValueError):
            self.store.record("g", "w", 5, float('nan'), now)
        with self.assertRaises(ValueError):
            self.store.record("g", "w", 5, float('inf'), now)
        with self.assertRaises(ValueError):
            self.store.record("g", "w", 5, True, now)

        with self.assertRaises(ValueError):
            self.store.record("g", "w", -5, 50, now)
        with self.assertRaises(ValueError):
            self.store.record("g", "w", 5.5, 50, now) # float window_minutes
        with self.assertRaises(ValueError):
            self.store.record("g", "w", True, 50, now)

    def test_future_inputs(self):
        future_ts = (datetime.now(timezone.utc) + timedelta(days=366)).isoformat()
        with self.assertRaises(ValueError):
            self.store.record("g", "w", 5, 50, future_ts)

    def test_invalid_labels(self):
        now = datetime.now(timezone.utc).isoformat()
        with self.assertRaises(ValueError):
            self.store.record("invalid label!", "w", 5, 50, now)
        with self.assertRaises(ValueError):
            self.store.record("g", "invalid/window", 5, 50, now)

    def test_stale_expired_missing(self):
        now = datetime.now(timezone.utc)
        stale_ts = (now - timedelta(seconds=1000)).isoformat()
        reset_ts = (now - timedelta(seconds=10)).isoformat()
        future_obs = (now + timedelta(seconds=10)).isoformat()

        self.store.record("g", "stale_win", 5, 50, stale_ts)
        self.store.record("g", "expired_win", 5, 50, now.isoformat(), reset_at=reset_ts)
        self.store.record("g", "future_obs_win", 5, 50, future_obs)

        res = self.store.show("g")

        self.assertEqual(res["g"]["stale_win"]["status"], "stale")
        self.assertNotIn("usable_remaining_percent", res["g"]["stale_win"])
        self.assertEqual(res["g"]["stale_win"]["last_remaining_percent"], 50)

        self.assertEqual(res["g"]["expired_win"]["status"], "expired")
        self.assertNotIn("usable_remaining_percent", res["g"]["expired_win"])

        self.assertEqual(res["g"]["future_obs_win"]["status"], "invalid")
        self.assertNotIn("usable_remaining_percent", res["g"]["future_obs_win"])

    def test_corrupt_state(self):
        now = datetime.now(timezone.utc).isoformat()
        self.store.record("g", "w", 5, 50, now)

        with open(self.store.readings_path, 'w') as f:
            f.write("invalid json")

        res = self.store.show("g")
        self.assertEqual(res, {"g": {"status": "Unknown"}})

        # Record should overwrite invalid JSON safely
        self.store.record("g", "w", 5, 60, now)
        res2 = self.store.show("g")
        self.assertEqual(res2["g"]["w"]["usable_remaining_percent"], 60)

    def test_concurrent_writers(self):
        def write_worker(idx):
            # Give each thread a unique, valid timestamp for its loop
            base_time = datetime.now(timezone.utc)
            for i in range(10):
                obs = (base_time - timedelta(seconds=i*0.1 + idx)).isoformat()
                self.store.record(f"g{idx}", f"w{i}", 5, idx * 10, obs)

        threads = [threading.Thread(target=write_worker, args=(i,)) for i in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()

        res = self.store.show()
        for i in range(5):
            self.assertIn(f"g{i}", res)
            for j in range(10):
                self.assertEqual(res[f"g{i}"][f"w{j}"]["usable_remaining_percent"], i * 10)

    def test_preservation_on_refusal(self):
        now = datetime.now(timezone.utc).isoformat()
        self.store.record("g", "w", 5, 50, now)

        # Test exact duplicate observation time
        with self.assertRaises(ValueError):
            self.store.record("g", "w", 5, 60, now)

        res = self.store.show("g")
        self.assertEqual(res["g"]["w"]["usable_remaining_percent"], 50)

if __name__ == '__main__':
    unittest.main()
