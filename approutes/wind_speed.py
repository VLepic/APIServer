"""Route for fetching wind speed data from InfluxDB"""

import os
import logging
from flask import jsonify, request
from datetime import datetime
from Read import read, read_latest


def wind_speed_route(app):

    @app.route('/weather/wind_speed', methods=['GET'])
    def get_wind_speed():
        # InfluxDB connection details and measurement specifics
        INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'default-influxdb-url')
        INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'default-influxdb-token')
        org = "HA"
        bucket = "home_assistant"
        entity_id_temperature = "gw1100a_v2_2_3_wind_speed"
        field = "value"

        # Retrieve start and stop time arguments from the request URL parameters
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        logging.info(f'Received request for wind speed data between {start_time} and {end_time}')
        # Check if start_time and end_time are provided in the request, otherwise return error message
        if not start_time or not end_time:
            return jsonify({'error': 'Please provide start_time and end_time parameters in the URL'}), 400

        # Fetch data for temperature within the specified time range
        try:
            time_values, measurement_values = read(INFLUXDB_URL, INFLUXDB_TOKEN, org, bucket, entity_id_temperature, field, start_time,
                                               end_time)
        except Exception as InfluxDBReadError:
            logging.critical(f"Error fetching data for wind speed: {InfluxDBReadError}")
            return jsonify({'500 Server error': 'An error occurred while fetching data from InfluxDB'}), 500
        # Convert datetime objects to ISO 8601 format
        time_values_iso = [time.isoformat() for time in time_values]

        return jsonify({'time_values': time_values_iso, 'measurement_values': measurement_values}), 200

def latest_wind_speed_route(app):
        @app.route('/weather/wind_speed/latest', methods=['GET'])
        def get_latest_wind_speed():
            # InfluxDB connection details and measurement specifics
            INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'default-influxdb-url')
            INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'default-influxdb-token')
            org = "HA"
            bucket = "home_assistant"
            entity_id_temperature = "gw1100a_v2_2_3_wind_speed"
            field = "value"
            logging.info('Received request for latest wind speed data')
            # Fetch data for temperature within the specified time range
            try:
                time_values, measurement_values = read_latest(INFLUXDB_URL, INFLUXDB_TOKEN, org, bucket, entity_id_temperature, field, "-1h")
            except Exception as InfluxDBReadError:
                logging.critical(f"Error fetching data for latest wind speed: {InfluxDBReadError}")
                return jsonify({'500 Server error': 'An error occurred while fetching data from InfluxDB'}), 500
            # Convert datetime objects to ISO 8601 format
            time_values_iso = [time.isoformat() for time in time_values]

            return jsonify({'time_values': time_values_iso, 'measurement_values': measurement_values}), 200
