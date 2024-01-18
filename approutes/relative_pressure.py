import os

from flask import jsonify, request

from Read import read


def relative_pressure_route(app):
    @app.route('/relative_pressure', methods=['GET'])
    def get_relative_pressure():
        INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'default-influxdb-url')
        INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'default-influxdb-token')
        # InfluxDB connection details and measurement specifics
        url = INFLUXDB_URL
        token = INFLUXDB_TOKEN
        org = "HA"
        bucket = "home_assistant"
        entity_id_temperature = "gw1100a_v2_1_3_relative_pressure"
        field = "value"

        # Retrieve start and stop time arguments from the request URL parameters
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

        # Check if start_time and end_time are provided in the request, otherwise return error message
        if not start_time or not end_time:
            return jsonify({'error': 'Please provide start_time and end_time parameters in the URL'})

        # Fetch data for temperature within the specified time range
        time_values, measurement_values = read(url, token, org, bucket, entity_id_temperature, field, start_time,
                                               end_time)

        # Convert datetime objects to ISO 8601 format
        time_values_iso = [time.isoformat() for time in time_values]

        return jsonify({'time_values': time_values_iso, 'measurement_values': measurement_values})