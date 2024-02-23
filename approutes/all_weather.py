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

        entity_ids = ["gw1100a_v2_1_3_absolute_pressure", "gw1100a_v2_1_3_daily_rain_rate", "gw1100a_v2_1_3_dewpoint",
                      "gw1100a_v2_1_3_hourly_rain_rate", "gw1100a_v2_1_3_outdoor_temperature",
                      "gw1100a_v2_1_3_relative_pressure", "gw1100a_v2_1_3_wind_gust", "gw1100a_v2_1_3_wind_speed",
                      "gw1100a_v2_1_3_yearly_rain"]

        grouped_results = {}
        for entity_id in entity_ids:
            time_values, measurement_values = read(INFLUXDB_URL, INFLUXDB_TOKEN, org, bucket, entity_id, field,
                                                   start_time, end_time)
            time_values_iso = [time.isoformat() for time in time_values]
            grouped_results[entity_id] = {
                'time_values': time_values_iso,
                'measurement_values': measurement_values
            }

        return jsonify(grouped_results)
