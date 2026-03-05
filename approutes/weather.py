"""Weather routes."""

from datetime import datetime
import re

from flask import jsonify, request

from Read import read, read_latest
from weather_config import WEATHER_METRICS, get_influx_settings


RELATIVE_TIME_RE = re.compile(r"^-\d+[smhdw]$")


def _is_iso_datetime(value):
    if not value:
        return False
    normalized = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
        return True
    except ValueError:
        return False


def _is_valid_flux_time(value):
    return bool(value) and (RELATIVE_TIME_RE.match(value) is not None or _is_iso_datetime(value))


def _is_valid_sampling_period(value):
    return bool(value) and RELATIVE_TIME_RE.match(value) is not None


def _serialize_values(time_values, measurement_values):
    return {
        "time_values": [time_value.isoformat() for time_value in time_values],
        "measurement_values": measurement_values,
    }


def _get_metric_config(metric):
    metric_config = WEATHER_METRICS.get(metric)
    if metric_config is None:
        return None, (jsonify({"error": f"Unknown weather metric '{metric}'."}), 404)
    return metric_config, None


def _validate_time_range(start_time, end_time):
    if not start_time or not end_time:
        return jsonify({"error": "Please provide start_time and end_time parameters in the URL."}), 400
    if not _is_valid_flux_time(start_time) or not _is_valid_flux_time(end_time):
        return jsonify({"error": "Invalid start_time or end_time format. Use ISO datetime or relative time (e.g. -1h)."}), 400
    return None


def _query_range(entity_id, start_time, end_time):
    influx_url, influx_token, org, bucket = get_influx_settings()
    return read(influx_url, influx_token, org, bucket, entity_id, "value", start_time, end_time)


def _query_latest(entity_id, sampling_period):
    influx_url, influx_token, org, bucket = get_influx_settings()
    return read_latest(influx_url, influx_token, org, bucket, entity_id, "value", sampling_period)


def register_weather_routes(app):
    @app.route("/weather", methods=["GET"])
    def get_available_weather_metrics():
        return jsonify({"metrics": sorted(WEATHER_METRICS.keys())})

    @app.route("/weather/<metric>", methods=["GET"])
    def get_weather_metric(metric):
        metric_config, error_response = _get_metric_config(metric)
        if error_response:
            return error_response

        start_time = request.args.get("start_time")
        end_time = request.args.get("end_time")
        validation_error = _validate_time_range(start_time, end_time)
        if validation_error:
            return validation_error

        try:
            time_values, measurement_values = _query_range(metric_config["entity_id"], start_time, end_time)
        except RuntimeError as error:
            return jsonify({"error": str(error)}), 500

        return jsonify(_serialize_values(time_values, measurement_values))

    @app.route("/weather/<metric>/latest", methods=["GET"])
    def get_latest_weather_metric(metric):
        metric_config, error_response = _get_metric_config(metric)
        if error_response:
            return error_response

        sampling_period = request.args.get("sampling_period", metric_config["latest_window"])
        if not _is_valid_sampling_period(sampling_period):
            return jsonify({"error": "Invalid sampling_period format. Use relative duration like -1h."}), 400

        try:
            time_values, measurement_values = _query_latest(metric_config["entity_id"], sampling_period)
        except RuntimeError as error:
            return jsonify({"error": str(error)}), 500

        return jsonify(_serialize_values(time_values, measurement_values))

    @app.route("/weather/all_weather_data", methods=["GET"])
    def get_all_weather_data():
        start_time = request.args.get("start_time")
        end_time = request.args.get("end_time")
        validation_error = _validate_time_range(start_time, end_time)
        if validation_error:
            return validation_error

        try:
            payload = {}
            for metric, config in WEATHER_METRICS.items():
                time_values, measurement_values = _query_range(config["entity_id"], start_time, end_time)
                payload[metric] = _serialize_values(time_values, measurement_values)
        except RuntimeError as error:
            return jsonify({"error": str(error)}), 500

        return jsonify(payload)
