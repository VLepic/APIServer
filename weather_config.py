"""Centralized configuration for weather metrics and InfluxDB."""

import os


WEATHER_METRICS = {
    "outdoor_temperature": {
        "entity_id": "gw1100a_v2_2_3_outdoor_temperature",
        "latest_window": "-1h",
    },
    "humidity": {
        "entity_id": "gw1100a_v2_2_3_humidity",
        "latest_window": "-1h",
    },
    "dewpoint": {
        "entity_id": "gw1100a_v2_2_3_dewpoint",
        "latest_window": "-1h",
    },
    "absolute_pressure": {
        "entity_id": "gw1100a_v2_1_3_absolute_pressure",
        "latest_window": "-1h",
    },
    "relative_pressure": {
        "entity_id": "gw1100a_v2_1_3_relative_pressure",
        "latest_window": "-1h",
    },
    "wind_gust": {
        "entity_id": "gw1100a_v2_2_3_wind_gust",
        "latest_window": "-1h",
    },
    "wind_speed": {
        "entity_id": "gw1100a_v2_2_3_wind_speed",
        "latest_window": "-1h",
    },
    "hourly_rain": {
        "entity_id": "gw1100a_v2_2_3_hourly_rain_rate",
        "latest_window": "-620h",
    },
    "daily_rain": {
        "entity_id": "gw1100a_v2_2_3_daily_rain_rate",
        "latest_window": "-620h",
    },
    "yearly_rain": {
        "entity_id": "gw1100a_v2_2_3_yearly_rain_rate",
        "latest_window": "-620h",
    },
}


def get_influx_settings():
    """Return validated InfluxDB settings."""
    influx_url = os.environ.get("INFLUXDB_URL")
    influx_token = os.environ.get("INFLUXDB_TOKEN")
    org = os.environ.get("INFLUXDB_ORG", "HA")
    bucket = os.environ.get("INFLUXDB_BUCKET", "home_assistant")

    if not influx_url or not influx_token:
        raise RuntimeError("Missing required INFLUXDB_URL or INFLUXDB_TOKEN environment variable.")

    return influx_url, influx_token, org, bucket


def get_socket_entity_ids():
    """Map websocket channels directly to metric entity IDs."""
    return {
        metric: config["entity_id"]
        for metric, config in WEATHER_METRICS.items()
    }
