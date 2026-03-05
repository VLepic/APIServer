import os
import threading

import eventlet

if os.environ.get("DISABLE_EVENTLET_PATCH") != "1":
    eventlet.monkey_patch()

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO

from Read import create_influx_client, read_latest, read_latest_many
from approutes.weather import register_weather_routes
from weather_config import get_influx_settings, get_socket_entity_ids


app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, ping_timeout=60, ping_interval=30, cors_allowed_origins="*")

register_weather_routes(app)

SOCKET_ENTITY_IDS = get_socket_entity_ids()
clients = {measurement: set() for measurement in SOCKET_ENTITY_IDS}
thread_lock = threading.Lock()


@socketio.on("connect")
def handle_connect():
    print("Client connected")


@socketio.on("disconnect")
def handle_disconnect():
    print(f"Client {request.sid} disconnected")
    with thread_lock:
        for measurement, client_set in clients.items():
            if request.sid in client_set:
                client_set.remove(request.sid)
                print(f"Client {request.sid} unsubscribed from {measurement}")


def _get_active_measurements():
    with thread_lock:
        return [measurement for measurement, subscribers in clients.items() if subscribers]


def weather_socket(socketio_instance):
    """Poll only active subscriptions and broadcast updates to their subscribers."""
    print("Running weather socket updates")
    last_times = {measurement: None for measurement in SOCKET_ENTITY_IDS}
    influx_client = None

    while True:
        active_measurements = _get_active_measurements()
        if not active_measurements:
            eventlet.sleep(5)
            continue

        try:
            influx_url, influx_token, org, bucket = get_influx_settings()
        except RuntimeError as error:
            print(f"Websocket update paused: {error}")
            eventlet.sleep(5)
            continue

        if influx_client is None:
            influx_client = create_influx_client(influx_url, influx_token, org)

        active_entity_ids = [SOCKET_ENTITY_IDS[measurement] for measurement in active_measurements]

        try:
            latest_by_entity = read_latest_many(
                influx_url,
                influx_token,
                org,
                bucket,
                active_entity_ids,
                "value",
                "-1h",
                client=influx_client,
                raise_on_error=True,
            )
        except Exception as error:
            print(f"Batch poll failed, reconnecting Influx client: {error}")
            try:
                influx_client.close()
            except Exception:
                pass
            influx_client = None
            eventlet.sleep(2)
            continue

        for measurement in active_measurements:
            entity_id = SOCKET_ENTITY_IDS[measurement]
            latest_payload = latest_by_entity.get(entity_id)
            if not latest_payload:
                continue

            latest_time = latest_payload["time_values"][0]
            if last_times[measurement] == latest_time:
                continue

            data = {
                "measurement": measurement,
                "time_values": [latest_time.isoformat()],
                "measurement_values": latest_payload["measurement_values"],
            }
            last_times[measurement] = latest_time

            with thread_lock:
                subscribers = list(clients[measurement])

            for client in subscribers:
                socketio_instance.emit(f"{measurement}_update", data, to=client)

        eventlet.sleep(1)


@socketio.on("subscribe")
def handle_subscribe(data):
    measurement = data.get("measurement")
    if measurement in clients:
        with thread_lock:
            clients[measurement].add(request.sid)
        print(f"Client {request.sid} subscribed to {measurement}")
        send_initial_data(measurement, request.sid)


def send_initial_data(measurement, sid):
    """Send initial point for a measurement immediately after subscribe."""
    entity_id = SOCKET_ENTITY_IDS.get(measurement)
    if not entity_id:
        return

    try:
        influx_url, influx_token, org, bucket = get_influx_settings()
    except RuntimeError as error:
        print(f"Cannot send initial data: {error}")
        return

    time_values, measurement_values = read_latest(
        influx_url,
        influx_token,
        org,
        bucket,
        entity_id,
        "value",
        "-1h",
    )

    if not time_values or not measurement_values:
        return

    data = {
        "measurement": measurement,
        "time_values": [time_values[0].isoformat()],
        "measurement_values": measurement_values,
    }
    socketio.emit(f"{measurement}_update", data, to=sid)


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "404 Not found", "message": "This route is not available. Please check your URL."}), 404


if os.environ.get("DISABLE_WEATHER_SOCKET_THREAD") != "1":
    print("Starting weather socket thread...")
    eventlet.spawn(weather_socket, socketio)
    print("Weather socket thread started.")


if __name__ == "__main__":
    print("Starting Flask app with SocketIO...")
    socketio.run(app, debug=False, host="0.0.0.0", port=5000)
