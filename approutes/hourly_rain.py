"""Route for fetching hourly rain rate data from InfluxDB."""

import os

from flask import jsonify, request

from Read import read


def hourly_rain_route(app):
    @app.route('/hourly_rain', methods=['GET'])
    def get_hourly_rain():
        # InfluxDB connection details and measurement specifics
        INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'default-influxdb-url')
        INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'default-influxdb-token')
        org = "HA"
        bucket = "home_assistant"
        entity_id_temperature = "gw1100a_v2_1_3_hourly_rain_rate"
        field = "value"

        # Retrieve start and stop time arguments from the request URL parameters
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

        # Check if start_time and end_time are provided in the request, otherwise return error message
        if not start_time or not end_time:
            return jsonify({'error': 'Please provide start_time and end_time parameters in the URL'})

        # Fetch data for temperature within the specified time range
        time_values, measurement_values = read(INFLUXDB_URL, INFLUXDB_TOKEN, org, bucket, entity_id_temperature, field, start_time,
                                               end_time)

        # Convert datetime objects to ISO 8601 format
        time_values_iso = [time.isoformat() for time in time_values]

        return jsonify({'time_values': time_values_iso, 'measurement_values': measurement_values})

def latest_hourly_rain_route(app):
    @app.route('/latest_hourly_rain', methods=['GET'])
    def get_latest_hourly_rain():
        # InfluxDB connection details and measurement specifics
        INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'default-influxdb-url')
        INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'default-influxdb-token')
        org = "HA"
        bucket = "home_assistant"
        entity_id_temperature = "gw1100a_v2_1_3_hourly_rain_rate"
        field = "value"

        # Fetch data for temperature within the specified time range
        time_values, measurement_values = read(INFLUXDB_URL, INFLUXDB_TOKEN, org, bucket, entity_id_temperature, field, "-1h")

        # Convert datetime objects to ISO 8601 format
        time_values_iso = [time.isoformat() for time in time_values]
        return jsonify({'time_values': time_values_iso, 'measurement_values': measurement_values})