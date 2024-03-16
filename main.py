#Importing the libraries
from flask import Flask, jsonify
from flask_cors import CORS

# Importing the routes
from approutes.all_weather import all_weather_route
from approutes.absolute_pressure import absolute_pressure_route, latest_absolute_pressure_route
from approutes.daily_rain import daily_rain_route, latest_daily_rain_route
from approutes.dewpoint import dewpoint_route, latest_dewpoint_route
from approutes.hourly_rain import hourly_rain_route, latest_hourly_rain_route
from approutes.humidity import humidity_route, latest_humidity_route
from approutes.outdoor_temperature import outdoor_temperature_route, latest_outdoor_temperature_route
from approutes.relative_pressure import relative_pressure_route, latest_relative_pressure_route
from approutes.wind_gust import wind_gust_route, latest_wind_gust_route
from approutes.wind_speed import wind_speed_route, latest_wind_speed_route
from approutes.yearly_rain import yearly_rain_route, latest_yearly_rain_route

app = Flask(__name__)
CORS(app)

# Data routes
all_weather_route(app)

outdoor_temperature_route(app)
latest_outdoor_temperature_route(app)

dewpoint_route(app)
latest_dewpoint_route(app)

wind_speed_route(app)
latest_wind_speed_route(app)

wind_gust_route(app)
latest_wind_gust_route(app)

absolute_pressure_route(app)
latest_absolute_pressure_route(app)

relative_pressure_route(app)
latest_relative_pressure_route(app)

hourly_rain_route(app)
latest_hourly_rain_route(app)

daily_rain_route(app)
latest_daily_rain_route(app)

yearly_rain_route(app)
latest_yearly_rain_route(app)

humidity_route(app)
latest_humidity_route(app)


#Error handling
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '404 Not found', 'message': 'This route is not available. Please check your URL.'}), 404

# Entry point
if __name__ == '__main__':
    app.run(debug=False)
