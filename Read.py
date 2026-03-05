"""Read data from InfluxDB."""

import os

import pytz
from influxdb_client import InfluxDBClient


def create_influx_client(url: str, token: str, org: str):
    return InfluxDBClient(url=url, token=token, org=org)


def _convert_to_local_timezone(time_values):
    timezone_name = os.environ.get("TIMEZONE", "UTC")
    try:
        local_timezone = pytz.timezone(timezone_name)
    except pytz.UnknownTimeZoneError:
        local_timezone = pytz.UTC

    return [time_value.astimezone(local_timezone) for time_value in time_values]


def read(url, token, org, bucket, entity_id, field_name, start_time, end_time):
    client = create_influx_client(url=url, token=token, org=org)

    query = (
        f'from(bucket:"{bucket}") '
        f'|> range(start: {start_time}, stop: {end_time}) '
        f'|> filter(fn: (r) => r.entity_id == "{entity_id}" and r._field == "{field_name}")'
    )

    tables = client.query_api().query(query)

    time_values = []
    measurement_values = []

    for table in tables:
        for record in table.records:
            time_values.append(record.get_time())
            measurement_values.append(record.get_value())

    client.close()

    return _convert_to_local_timezone(time_values), measurement_values


def read_latest(
    url: str,
    token: str,
    org: str,
    bucket: str,
    entity_id: str,
    field_name: str,
    sampling_period: str,
    client=None,
):
    own_client = client is None
    influx_client = client or create_influx_client(url=url, token=token, org=org)
    query = (
        f'from(bucket:"{bucket}") '
        f'|> range(start: {sampling_period}) '
        f'|> filter(fn: (r) => r["entity_id"] == "{entity_id}") '
        f'|> filter(fn: (r) => r["_field"] == "{field_name}") '
        f'|> last()'
    )

    try:
        tables = influx_client.query_api().query(query=query)
    except Exception as error:
        print(f"Error querying data: {error}")
        if own_client:
            influx_client.close()
        return [], []

    time_values = []
    measurement_values = []

    for table in tables:
        for record in table.records:
            time_values.append(record.get_time())
            measurement_values.append(record.get_value())

    if own_client:
        influx_client.close()

    return _convert_to_local_timezone(time_values), measurement_values


def read_latest_many(
    url: str,
    token: str,
    org: str,
    bucket: str,
    entity_ids: list,
    field_name: str,
    sampling_period: str,
    client=None,
    raise_on_error=False,
):
    if not entity_ids:
        return {}

    own_client = client is None
    influx_client = client or create_influx_client(url=url, token=token, org=org)

    entity_filter = " or ".join(f'r["entity_id"] == "{entity_id}"' for entity_id in entity_ids)
    query = (
        f'from(bucket:"{bucket}") '
        f'|> range(start: {sampling_period}) '
        f'|> filter(fn: (r) => ({entity_filter})) '
        f'|> filter(fn: (r) => r["_field"] == "{field_name}") '
        f'|> group(columns: ["entity_id"]) '
        f'|> last()'
    )

    try:
        tables = influx_client.query_api().query(query=query)
    except Exception as error:
        print(f"Error querying batch data: {error}")
        if own_client:
            influx_client.close()
        if raise_on_error:
            raise
        return {}

    latest_by_entity = {}
    for table in tables:
        for record in table.records:
            entity_id = record.values.get("entity_id")
            if not entity_id:
                continue
            latest_by_entity[entity_id] = (record.get_time(), record.get_value())

    if own_client:
        influx_client.close()

    converted = {}
    for entity_id, (time_value, measurement_value) in latest_by_entity.items():
        converted_time = _convert_to_local_timezone([time_value])[0]
        converted[entity_id] = {
            "time_values": [converted_time],
            "measurement_values": [measurement_value],
        }

    return converted
