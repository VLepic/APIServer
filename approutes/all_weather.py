"""Route for all weather data"""
import os
import logging
from flask import jsonify, request
from joblib import Parallel, delayed
from Read import read


def read_weather_data(entity_id, start_time, end_time):
    INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'default-influxdb-url')
    INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'default-influxdb-token')
    org = "HA"
    bucket = "home_assistant"
    field = "value"

    if not start_time or not end_time:
        return {'error': 'Please provide start_time and end_time parameters in the URL'}, 400
    try:
        time_values, measurement_values = read(INFLUXDB_URL, INFLUXDB_TOKEN, org, bucket, entity_id, field, start_time, end_time)
    except Exception as InfluxDBReadError:
        logging.critical(f"Error fetching data for all weather: {InfluxDBReadError}")
        return jsonify({'500 Server error': 'An error occurred while fetching data from InfluxDB'}), 500

    time_values_iso = [time.isoformat() for time in time_values]
    return {
        'time_values': time_values_iso,
        'measurement_values': measurement_values
    }, 200

def all_weather_route(app):
    @app.route('/weather/all_weather_data', methods=['GET'])
    def get_all_weather_data():
        entity_ids = [
                      "gw1100a_v2_2_3_humidity",
                      "gw1100a_v2_2_3_dewpoint",
                      "gw1100a_v2_2_3_outdoor_temperature",
                      "gw1100a_v2_1_3_absolute_pressure",
                      "gw1100a_v2_1_3_relative_pressure",
                      "gw1100a_v2_2_3_wind_gust",
                      "gw1100a_v2_2_3_wind_speed",
                      "gw1100a_v2_2_3_hourly_rain_rate",
                      "gw1100a_v2_2_3_daily_rain_rate",
                      "gw1100a_v2_2_3_yearly_rain_rate"]

        num_processes = len(entity_ids)

        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        logging.info(f'Received request for all weather data between {start_time} and {end_time}')
        results = Parallel(n_jobs=num_processes)(delayed(read_weather_data)(entity_id, start_time, end_time) for entity_id in entity_ids)

        grouped_results = {}
        for entity_id, result in zip(entity_ids, results):
            grouped_results[entity_id] = result

        return jsonify(grouped_results), 200
