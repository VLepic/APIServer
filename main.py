# Importing the libraries
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
import eventlet
from threading import Thread
import os
from joblib import Parallel, delayed
from Read import read, read_latest  # Assuming these functions are properly imported
from datetime import datetime
from approutes.all_weather import all_weather_route
from approutes.absolute_pressure import absolute_pressure_route, latest_absolute_pressure_route
from approutes.daily_rain import daily_rain_route, latest_daily_rain_route
from approutes.dewpoint import dewpoint_route, latest_dewpoint_route
from approutes.hourly_rain import hourly_rain_route, latest_hourly_rain_route
from approutes.humidity import humidity_route, latest_humidity_route
from approutes.outdoor_temperature import *
from approutes.relative_pressure import relative_pressure_route, latest_relative_pressure_route
from approutes.wind_gust import wind_gust_route, latest_wind_gust_route
from approutes.wind_speed import wind_speed_route, latest_wind_speed_route
from approutes.yearly_rain import yearly_rain_route, latest_yearly_rain_route
from approutes.rain_rate import rain_rate_route, latest_rain_rate_route
import threading

# Configure logging

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
numeric_level = getattr(logging, log_level, logging.INFO)
logging.basicConfig(
    level=numeric_level,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Initialize Flask app
eventlet.monkey_patch()
app = Flask(__name__)
CORS(app)

# Initialize SocketIO for WebSocket support
socketio = SocketIO(app, ping_timeout=60, ping_interval=30, cors_allowed_origins="*")

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
rain_rate_route(app)
latest_rain_rate_route(app)

@socketio.on('connect')
def handle_connect():
    logging.info(f'Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logging.info(f'Client {request.sid} disconnected')

    # Remove client from all subscribed measurements
    with thread_lock:
        for measurement, client_set in clients.items():
            if request.sid in client_set:
                client_set.remove(request.sid)
                logging.info(f'Client {request.sid} unsubscribed from {measurement}')

clients = {
    "temperature": set(),
    "humidity": set(),
    "dewpoint": set(),
    "absolute_pressure": set(),
    "relative_pressure": set(),
    "wind_gust": set(),
    "wind_speed": set(),
    "hourly_rain": set(),
    "daily_rain": set(),
    "yearly_rain": set(),
    "rain_rate": set()
}
thread_lock = threading.Lock()

def weather_socket(socketio):
    """Function to send updates for specific measurements to subscribed clients."""
    logging.info('Running weather socket updates')
    INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'default-influxdb-url')
    INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'default-influxdb-token')
    org = "HA"
    bucket = "home_assistant"
    entity_ids = {
        "temperature": "gw1100a_v2_2_3_outdoor_temperature",
        "humidity": "gw1100a_v2_2_3_humidity",
        "dewpoint": "gw1100a_v2_2_3_dewpoint",
        "absolute_pressure": "gw1100a_v2_1_3_absolute_pressure",
        "relative_pressure": "gw1100a_v2_1_3_relative_pressure",
        "wind_gust": "gw1100a_v2_2_3_wind_gust",
        "wind_speed": "gw1100a_v2_2_3_wind_speed",
        "hourly_rain": "gw1100a_v2_2_3_hourly_rain_rate",
        "daily_rain": "gw1100a_v2_2_3_daily_rain_rate",
        "yearly_rain": "gw1100a_v2_2_3_yearly_rain_rate",
        "rain_rate": "gw1100a_v2_2_3_rain_rate"
    }
    last_times = {key: None for key in entity_ids}

    while True:
        with thread_lock:
            if all(len(clients[measurement]) == 0 for measurement in clients):
                eventlet.sleep(5)
                continue

        for measurement, entity_id in entity_ids.items():
            try:
                time_values, measurement_values = read_latest(
                    INFLUXDB_URL, INFLUXDB_TOKEN, org, bucket, entity_id, "value", "-30d"
                )
            except Exception as e:
                logging.critical(f'Error fetching latest data for {measurement}: {e}')
                socketio.emit('error', {'message': f'Error fetching latest data for {measurement}'})
                continue
            if time_values and measurement_values:
                latest_time = time_values[0]
                if last_times[measurement] is None or latest_time != last_times[measurement]:
                    data = {
                        'measurement': measurement,
                        'time_values': [latest_time.isoformat()],
                        'measurement_values': measurement_values
                    }
                    last_times[measurement] = latest_time

                    # Emit data only to clients subscribed to this measurement
                    with thread_lock:
                        for client in clients[measurement]:
                            logging.info(f'Sending {measurement} update to client {client}')
                            socketio.emit(f'{measurement}_update', data, to=client)

        eventlet.sleep(1)  # Repeat every second

# Manage client subscriptions
@socketio.on('subscribe')
def handle_subscribe(data):
    global clients
    measurement = data.get('measurement')
    if measurement in clients:
        with thread_lock:
            clients[measurement].add(request.sid)
        logging.info(f'Client {request.sid} subscribed to {measurement}')
        # Send immediate data upon subscription
        try:
            send_initial_data(measurement, request.sid)
        except KeyError as e:
            logging.error(f'Error: {e} - The session {request.sid} is disconnected')

def send_initial_data(measurement, sid):
    logging.info(f'Sending initial data to {sid}')
    """Send the initial data for a measurement after subscribing."""
    INFLUXDB_URL = os.environ.get('INFLUXDB_URL', 'default-influxdb-url')
    INFLUXDB_TOKEN = os.environ.get('INFLUXDB_TOKEN', 'default-influxdb-token')
    org = "HA"
    bucket = "home_assistant"

    entity_ids = {
        "temperature": "gw1100a_v2_2_3_outdoor_temperature",
        "humidity": "gw1100a_v2_2_3_humidity",
        "dewpoint": "gw1100a_v2_2_3_dewpoint",
        "absolute_pressure": "gw1100a_v2_1_3_absolute_pressure",
        "relative_pressure": "gw1100a_v2_1_3_relative_pressure",
        "wind_gust": "gw1100a_v2_2_3_wind_gust",
        "wind_speed": "gw1100a_v2_2_3_wind_speed",
        "hourly_rain": "gw1100a_v2_2_3_hourly_rain_rate",
        "daily_rain": "gw1100a_v2_2_3_daily_rain_rate",
        "yearly_rain": "gw1100a_v2_2_3_yearly_rain_rate",
        "rain_rate": "gw1100a_v2_2_3_rain_rate"
    }

    entity_id = entity_ids.get(measurement)
    if entity_id:
        try:
            time_values, measurement_values = read_latest(
            INFLUXDB_URL, INFLUXDB_TOKEN, org, bucket, entity_id, "value", "-30d"
        )
        except Exception as e:
            logging.critical(f'Error fetching initial data for {measurement}: {e}')
            socketio.emit('error', {'message': f'Error fetching initial data for {measurement}'})
            return
        if time_values and measurement_values:
            data = {
                'measurement': measurement,
                'time_values': [time_values[0].isoformat()],
                'measurement_values': measurement_values
            }
            socketio.emit(f'{measurement}_update', data, to=sid)

# Error handling
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '404 Not found', 'message': 'This route is not available. Please check your URL.'}), 404

logging.info('Starting weather socket thread...')
eventlet.spawn(weather_socket, socketio)
logging.info('Weather socket thread started.')

# Entry point
if __name__ == '__main__':
    logging.info('Starting Flask app with SocketIO...')
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, ping_timeout=20, ping_interval=5)
    logging.info('Flask app started')









