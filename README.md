# Weather API Server

Flask + Socket.IO API for reading weather metrics from InfluxDB.

## Features

- REST endpoints for time-series and latest metric values
- Aggregated endpoint for all weather metrics
- Socket.IO updates for subscribed clients only
- Optimized websocket polling:
  - polls only active subscriptions
  - uses one batch Flux query per tick
  - reuses the InfluxDB client connection
- Centralized metric/config mapping in `weather_config.py`

## Tech Stack

- Python
- Flask
- Flask-CORS
- Flask-SocketIO
- InfluxDB Client
- Eventlet

## Requirements

- Python 3.10+
- Running InfluxDB with Home Assistant weather data
- Environment variables configured

## Environment Variables

Required:

- `INFLUXDB_URL` - InfluxDB URL (for example `http://localhost:8086`)
- `INFLUXDB_TOKEN` - InfluxDB token

Optional:

- `INFLUXDB_ORG` - default: `HA`
- `INFLUXDB_BUCKET` - default: `home_assistant`
- `TIMEZONE` - default: `UTC` (for example `Europe/Prague`)

## Run Locally (Python)

```bash
pip install -r requirements.txt
python main.py
```

Server default address:

```text
http://0.0.0.0:5000
```

## Run with Docker Compose

1. Create `.env` from example:

```bash
cp .env.example .env
```

2. Fill real values in `.env` (mainly `INFLUXDB_TOKEN`).

3. Start API (build is automatic):

```bash
docker compose up --build api
```

4. Stop services:

```bash
docker compose down
```

## Run Tests in Docker

```bash
docker compose --profile test run --rm api-tests
```

This command builds the image automatically when needed and runs:

```text
python -m unittest discover -v -s tests
```

## REST API

Base URL:

```text
http://localhost:5000
```

### 1) List Available Metrics

- `GET /weather`

Response:

```json
{
  "metrics": [
    "absolute_pressure",
    "daily_rain",
    "dewpoint",
    "hourly_rain",
    "humidity",
    "outdoor_temperature",
    "relative_pressure",
    "wind_gust",
    "wind_speed",
    "yearly_rain"
  ]
}
```

### 2) Get Metric Time-Series

- `GET /weather/<metric>?start_time=<time>&end_time=<time>`

Supported `start_time` / `end_time` formats:

- ISO datetime (for example `2025-01-01T00:00:00+00:00`)
- Relative Flux time (for example `-1h`, `-7d`)

Example:

```bash
curl "http://localhost:5000/weather/outdoor_temperature?start_time=-24h&end_time=-1h"
```

Success (200):

```json
{
  "time_values": ["2026-03-05T11:00:00+00:00"],
  "measurement_values": [7.2]
}
```

Validation error (400):

```json
{
  "error": "Please provide start_time and end_time parameters in the URL."
}
```

Unknown metric (404):

```json
{
  "error": "Unknown weather metric 'xyz'."
}
```

### 3) Get Latest Metric Value

- `GET /weather/<metric>/latest`
- `GET /weather/<metric>/latest?sampling_period=-6h`

Note: `sampling_period` must be a relative duration (`-1h`, `-30m`, `-7d`).

Example:

```bash
curl "http://localhost:5000/weather/humidity/latest?sampling_period=-2h"
```

Success (200):

```json
{
  "time_values": ["2026-03-05T11:12:00+00:00"],
  "measurement_values": [63]
}
```

Validation error (400):

```json
{
  "error": "Invalid sampling_period format. Use relative duration like -1h."
}
```

### 4) Get All Metrics in One Request

- `GET /weather/all_weather_data?start_time=<time>&end_time=<time>`

Example:

```bash
curl "http://localhost:5000/weather/all_weather_data?start_time=-6h&end_time=-1h"
```

Response shape:

```json
{
  "outdoor_temperature": {
    "time_values": ["2026-03-05T11:00:00+00:00"],
    "measurement_values": [7.2]
  },
  "humidity": {
    "time_values": ["2026-03-05T11:00:00+00:00"],
    "measurement_values": [63]
  }
}
```

## WebSocket API (Socket.IO)

Socket.IO runs on the same host/port as HTTP.

### Subscribe Flow

1. Client connects.
2. Client emits `subscribe` with payload `{ "measurement": "<channel>" }`.
3. Server sends initial latest value.
4. Server sends incremental updates only when a new value arrives.

### Available Channels (`measurement`)

- `outdoor_temperature`
- `humidity`
- `dewpoint`
- `absolute_pressure`
- `relative_pressure`
- `wind_gust`
- `wind_speed`
- `hourly_rain`
- `daily_rain`
- `yearly_rain`

### Update Events

Server emits events in this format:

```text
<measurement>_update
```

Example payload (`outdoor_temperature_update`):

```json
{
  "measurement": "outdoor_temperature",
  "time_values": ["2026-03-05T11:12:00+00:00"],
  "measurement_values": [7.3]
}
```

## Error Handling

Unknown HTTP routes return:

```json
{
  "error": "404 Not found",
  "message": "This route is not available. Please check your URL."
}
```

## Tests

Basic route tests are in:

- `tests/test_weather_routes.py`

Run locally:

```bash
python -m unittest discover -v -s tests
```

Run in Docker:

```bash
docker compose --profile test run --rm api-tests
```

## Project Structure (Key Files)

- `main.py` - Flask/Socket.IO app bootstrap + websocket update loop
- `approutes/weather.py` - unified weather REST routes
- `weather_config.py` - metric mapping and Influx settings
- `Read.py` - InfluxDB query helpers
- `docker-compose.yml` - local run + test services
