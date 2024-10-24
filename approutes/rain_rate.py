"""Route for retrieving outdoor temperature data from InfluxDB"""

import os
from threading import Thread
from flask import jsonify, request
from flask_socketio import SocketIO
import eventlet
from Read import read, read_latest
from datetime import datetime


def rain_rate_route(app):

    @app.route('/weather/rain_rate', methods=['GET'])
    def get_rain_rate():
        # InfluxDB connection details and measurement specifics
        INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'default-influxdb-url')
        INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'default-influxdb-token')
        org = "HA"
        bucket = "home_assistant"
        entity_id_temperature = "gw1100a_v2_2_3_rain_rate"
        field = "value"

        # Retrieve start and stop time arguments from the request URL parameters
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Received request for rain rate data between {start_time} and {end_time}')
        # Check if start_time and end_time are provided in the request, otherwise return error message
        if not start_time or not end_time:
            return jsonify({'error': 'Please provide start_time and end_time parameters in the URL'})

        # Fetch data for temperature within the specified time range
        time_values, measurement_values = read(INFLUXDB_URL, INFLUXDB_TOKEN, org, bucket, entity_id_temperature, field, start_time, end_time)

        # Convert datetime objects to ISO 8601 format
        time_values_iso = [time.isoformat() for time in time_values]

        return jsonify({'time_values': time_values_iso, 'measurement_values': measurement_values})

def latest_rain_rate_route(app):
        @app.route('/weather/rain_rate/latest', methods=['GET'])
        def get_latest_rain_rate():
            print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Received request for latest rain rate data')
            # InfluxDB connection details and measurement specifics
            INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'default-influxdb-url')
            INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'default-influxdb-token')
            org = "HA"
            bucket = "home_assistant"
            entity_id_temperature = "gw1100a_v2_2_3_rain_rate"
            field = "value"

            # Fetch data for temperature within the specified time range
            time_values, measurement_values = read_latest(INFLUXDB_URL, INFLUXDB_TOKEN, org, bucket, entity_id_temperature, field, "-30d")

            # Convert datetime objects to ISO 8601 format
            time_values_iso = [time.isoformat() for time in time_values]

            return jsonify({'time_values': time_values_iso, 'measurement_values': measurement_values})