from flask import Flask
from flask_cors import CORS

from approutes.absolute_pressure import absolute_pressure_route
from approutes.daily_rain import daily_rain_route
from approutes.dewpoint import dewpoint_route
from approutes.hourly_rain import hourly_rain_route
from approutes.outdoor_temperature import outdoor_temperature_route
from approutes.relative_pressure import relative_pressure_route
from approutes.wind_gust import wind_gust_route
from approutes.wind_speed import wind_speed_route
from approutes.yearly_rain import yearly_rain_route

app = Flask(__name__)
CORS(app)

# Weather Station
outdoor_temperature_route(app)
dewpoint_route(app)
wind_speed_route(app)
wind_gust_route(app)
absolute_pressure_route(app)
relative_pressure_route(app)
hourly_rain_route(app)
daily_rain_route(app)
yearly_rain_route(app)

@app.route('/hourly_rain', methods=['GET'])
def get_hourly_rain():
    # Replace these variables with your actual InfluxDB connection details and measurement specifics
    url = INFLUXDB_URL
    token = INFLUXDB_TOKEN
    org = "HA"
    bucket = "home_assistant"
    entity_id_temperature = "gw1100a_v2_1_3_hourly_rain_rate"
    field = "value"

    # Retrieve start and stop time arguments from the request URL parameters
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    # Check if start_time and end_time are provided in the request, otherwise set defaults
    if not start_time or not end_time:
        return jsonify({'error': 'Please provide start_time and end_time parameters in the URL'})

    # Fetch data for temperature within the specified time range
    time_values, measurement_values = read(url, token, org, bucket, entity_id_temperature, field, start_time, end_time)

    # Convert datetime objects to ISO 8601 format
    time_values_iso = [time.isoformat() for time in time_values]

    return jsonify({'time_values': time_values_iso, 'measurement_values': measurement_values})

if __name__ == '__main__':
    app.run(debug=False)
