"""Route for retrieving outdoor temperature data from InfluxDB"""

import os
from threading import Thread
from flask import jsonify, request
from flask_socketio import SocketIO
import eventlet
from Read import read, read_latest
from datetime import datetime
import logging

def outdoor_temperature_route(app):

    @app.route('/weather/outdoor_temperature', methods=['GET'])
    def get_outdoor_temperature():
        # InfluxDB connection details and measurement specifics
        INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'default-influxdb-url')
        INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'default-influxdb-token')
        org = "HA"
        bucket = "home_assistant"
        entity_id_temperature = "gw1100a_v2_2_3_outdoor_temperature"
        field = "value"

        # Retrieve start and stop time arguments from the request URL parameters
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        logging.info(f'Received request for outdoor temperature data between {start_time} and {end_time}')

        # Check if start_time and end_time are provided in the request, otherwise return error message
        if not start_time or not end_time:
            return jsonify({'error': 'Please provide start_time and end_time parameters in the URL'}), 400

        # Fetch data for temperature within the specified time range
        try:
            time_values, measurement_values = read(INFLUXDB_URL, INFLUXDB_TOKEN, org, bucket, entity_id_temperature, field, start_time, end_time)
        except Exception as InfluxDBReadError:
            logging.critical(f"Error fetching data for outdoor temperature: {InfluxDBReadError}")
            return jsonify({'500 Server error': 'An error occurred while fetching data from InfluxDB'}), 500
        # Convert datetime objects to ISO 8601 format
        time_values_iso = [time.isoformat() for time in time_values]

        return jsonify({'time_values': time_values_iso, 'measurement_values': measurement_values}), 200

def latest_outdoor_temperature_route(app):
        @app.route('/weather/outdoor_temperature/latest', methods=['GET'])
        def get_latest_outdoor_temperature():
            logging.info('Received request for latest outdoor temperature data')
            # InfluxDB connection details and measurement specifics
            INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'default-influxdb-url')
            INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'default-influxdb-token')
            org = "HA"
            bucket = "home_assistant"
            entity_id_temperature = "gw1100a_v2_2_3_outdoor_temperature"
            field = "value"

            # Fetch data for temperature within the specified time range
            try:
                time_values, measurement_values = read_latest(INFLUXDB_URL, INFLUXDB_TOKEN, org, bucket, entity_id_temperature, field, "-1h")
            except Exception as InfluxDBReadError:
                logging.critical(f"Error fetching data for latest outdoor temperature: {InfluxDBReadError}")
                return jsonify({'500 Server error': 'An error occurred while fetching data from InfluxDB'}), 500
            # Convert datetime objects to ISO 8601 format
            time_values_iso = [time.isoformat() for time in time_values]

            return jsonify({'time_values': time_values_iso, 'measurement_values': measurement_values}), 200