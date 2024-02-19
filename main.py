#Importing the libraries
from flask import Flask
from flask_cors import CORS

from approutes.absolute_pressure import absolute_pressure_route
# Importing the routes
from approutes.all_weather import all_weather_route
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

# Data routes
all_weather_route(app)
outdoor_temperature_route(app)
dewpoint_route(app)
wind_speed_route(app)
wind_gust_route(app)
absolute_pressure_route(app)
relative_pressure_route(app)
hourly_rain_route(app)
daily_rain_route(app)
yearly_rain_route(app)

# Entry point
if __name__ == '__main__':
    app.run(debug=False)
