import pytz
import logging
from influxdb_client import InfluxDBClient

def read(url, token, org, bucket, entity_id, field_name, start_time, end_time):
    client = InfluxDBClient(url=url, token=token, org=org)

    try:
        query = f'from(bucket:"{bucket}") |> range(start: {start_time}, stop: {end_time}) |> filter(fn: (r) => r.entity_id == "{entity_id}" and r._field == "{field_name}")'
        tables = client.query_api().query(query)
    except Exception as e:
        logging.critical(f"Error querying data in `read`: {e}")
        client.close()
        raise

    # Extract data
    time_values = []
    measurement_values = []

    for table in tables:
        for record in table.records:
            time_values.append(record.get_time())
            measurement_values.append(record.get_value())

    # Close the client
    client.close()

    # Convert UTC time to local timezone
    timezone = 'Europe/Paris'
    local_timezone = pytz.timezone(timezone)
    time_values_local = [time.astimezone(local_timezone) for time in time_values]

    return time_values_local, measurement_values

def read_latest(url: str, token: str, org: str, bucket: str, entity_id: str, field_name: str, sampling_period: str):
    client = InfluxDBClient(url=url, token=token, org=org)

    try:
        query = f'from(bucket:"{bucket}") |> range(start: {sampling_period}) |> filter(fn: (r) => r["entity_id"] == "{entity_id}") |> filter(fn: (r) => r["_field"] == "{field_name}") |> last()'
        tables = client.query_api().query(query=query)
    except Exception as e:
        logging.critical(f"Error querying data in `read_latest`: {e}")
        client.close()
        raise

    # Extract data
    time_values = []
    measurement_values = []

    for table in tables:
        for record in table.records:
            time_values.append(record.get_time())
            measurement_values.append(record.get_value())

    # Close the client
    client.close()

    # Convert UTC time to local timezone
    timezone = 'Europe/Paris'
    local_timezone = pytz.timezone(timezone)
    time_values_local = [time.astimezone(local_timezone) for time in time_values]

    return time_values_local, measurement_values

