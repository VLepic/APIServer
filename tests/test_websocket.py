import importlib
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch


class WebSocketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DISABLE_WEATHER_SOCKET_THREAD"] = "1"
        os.environ["DISABLE_EVENTLET_PATCH"] = "1"
        os.environ["INFLUXDB_URL"] = "http://localhost:8086"
        os.environ["INFLUXDB_TOKEN"] = "token"
        cls.main = importlib.import_module("main")

    def setUp(self):
        for measurement in self.main.clients:
            self.main.clients[measurement].clear()

    @patch("main.read_latest")
    def test_subscribe_sends_initial_update(self, read_latest_mock):
        read_latest_mock.return_value = ([datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)], [21.5])

        client = self.main.socketio.test_client(self.main.app)
        self.assertTrue(client.is_connected())

        client.emit("subscribe", {"measurement": "outdoor_temperature"})
        received = client.get_received()

        update_events = [event for event in received if event["name"] == "outdoor_temperature_update"]
        self.assertEqual(len(update_events), 1)
        payload = update_events[0]["args"][0]
        self.assertEqual(payload["measurement"], "outdoor_temperature")
        self.assertEqual(payload["measurement_values"], [21.5])
        self.assertEqual(payload["time_values"], ["2026-01-01T12:00:00+00:00"])

        client.disconnect()

    @patch("main.read_latest")
    def test_subscribe_unknown_measurement_emits_nothing(self, read_latest_mock):
        client = self.main.socketio.test_client(self.main.app)
        self.assertTrue(client.is_connected())

        client.emit("subscribe", {"measurement": "unknown_channel"})
        received = client.get_received()

        self.assertFalse(any(event["name"].endswith("_update") for event in received))
        read_latest_mock.assert_not_called()

        client.disconnect()


if __name__ == "__main__":
    unittest.main()
