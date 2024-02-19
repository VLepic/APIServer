"""Route for all weather data"""
import os

from flask import jsonify, request
from influxdb_client import InfluxDBClient

from Read import read


def get_all_entity_ids(url, token, org, bucket):
    with InfluxDBClient(url=url, token=token, org=org) as client:
        query = f'''
        import "influxdata/influxdb/schema"

        schema.tagValues(
            bucket: "{bucket}",
            tag: "entity_id",
            predicate: (r) => true,
            start: -30d
        )
        '''
        result = client.query_api().query(org=org, query=query)
        entity_ids = [record.get_value() for table in result for record in table.records]
        return entity_ids

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

        # Fetch all entity IDs from InfluxDB
        entity_ids = get_all_entity_ids(INFLUXDB_URL, INFLUXDB_TOKEN, org, bucket)

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