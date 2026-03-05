import os
import unittest
from unittest.mock import patch

from flask import Flask

from approutes.weather import register_weather_routes


class WeatherRoutesTests(unittest.TestCase):
    def setUp(self):
        self.env_patch = patch.dict(
            os.environ,
            {
                "INFLUXDB_URL": "http://localhost:8086",
                "INFLUXDB_TOKEN": "token",
            },
            clear=False,
        )
        self.env_patch.start()

        self.app = Flask(__name__)
        register_weather_routes(self.app)
        self.client = self.app.test_client()

    def tearDown(self):
        self.env_patch.stop()

    def test_weather_list_contains_yearly_rain(self):
        response = self.client.get("/weather")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("yearly_rain", payload["metrics"])

    def test_metric_requires_start_and_end_time(self):
        response = self.client.get("/weather/yearly_rain")
        self.assertEqual(response.status_code, 400)

    @patch("approutes.weather.read")
    def test_yearly_rain_metric_maps_to_correct_entity(self, read_mock):
        read_mock.return_value = ([], [])

        response = self.client.get(
            "/weather/yearly_rain",
            query_string={
                "start_time": "2025-01-01T00:00:00+00:00",
                "end_time": "2025-01-02T00:00:00+00:00",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(read_mock.call_args.args[4], "gw1100a_v2_2_3_yearly_rain_rate")

    @patch("approutes.weather.read_latest")
    def test_daily_rain_latest_uses_default_window(self, read_latest_mock):
        read_latest_mock.return_value = ([], [])

        response = self.client.get("/weather/daily_rain/latest")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(read_latest_mock.call_args.args[6], "-620h")

    @patch("approutes.weather.read_latest")
    def test_wind_speed_latest_uses_default_window(self, read_latest_mock):
        read_latest_mock.return_value = ([], [])

        response = self.client.get("/weather/wind_speed/latest")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(read_latest_mock.call_args.args[6], "-1h")

    @patch("approutes.weather.read")
    def test_invalid_time_format_returns_400(self, read_mock):
        response = self.client.get(
            "/weather/humidity",
            query_string={
                "start_time": "not-a-time",
                "end_time": "2025-01-02T00:00:00+00:00",
            },
        )

        self.assertEqual(response.status_code, 400)
        read_mock.assert_not_called()

    @patch("approutes.weather.read")
    def test_all_weather_data_returns_grouped_payload(self, read_mock):
        read_mock.return_value = ([], [])

        response = self.client.get(
            "/weather/all_weather_data",
            query_string={
                "start_time": "2025-01-01T00:00:00+00:00",
                "end_time": "2025-01-02T00:00:00+00:00",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("humidity", payload)
        self.assertIn("wind_speed", payload)
        self.assertIn("time_values", payload["humidity"])
        self.assertIn("measurement_values", payload["humidity"])

    def test_unknown_metric_returns_404(self):
        response = self.client.get("/weather/unknown_metric/latest")
        self.assertEqual(response.status_code, 404)

    def test_invalid_sampling_period_returns_400(self):
        response = self.client.get(
            "/weather/wind_speed/latest",
            query_string={"sampling_period": "tomorrow"},
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
