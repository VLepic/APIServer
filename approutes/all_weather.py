"""Route for all weather data"""
import os

from flask import jsonify, request

from Read import read


def all_weather_route(app):
    @app.route('/all_weather_data', methods=['GET'])
    def get_all_weather_data():
        INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'default-influxdb-url')
        INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'default-influxdb-token')
        org = "HA"
        bucket = "home_assistant"
        field = "value"

        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

        if not start_time or not end_time:
            return jsonify({'error': 'Please provide start_time and end_time parameters in the URL'})

        # Read entity IDs from the text file
        try:
            with open('entities.txt', 'r') as file:
                entity_ids = [line.strip() for line in file.readlines() if line.strip()]
        except FileNotFoundError:
            return jsonify({'error': 'Entity ID file not found.'})

        results = []
        for entity_id in entity_ids:
            time_values, measurement_values = read(INFLUXDB_URL, INFLUXDB_TOKEN, org, bucket, entity_id, field, start_time, end_time)
            time_values_iso = [time.isoformat() for time in time_values]
            results.append({
                'entity_id': entity_id,
                'time_values': time_values_iso,
                'measurement_values': measurement_values
            })

        return jsonify(results)
