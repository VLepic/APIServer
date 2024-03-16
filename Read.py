"""Read data from InfluxDB"""

import pytz
from influxdb_client import InfluxDBClient


def read(url, token, org, bucket, entity_id, field_name, start_time, end_time):
    client = InfluxDBClient(url=url, token=token, org=org)

    query = f'from(bucket:"{bucket}") |> range(start: {start_time}, stop: {end_time}) |> filter(fn: (r) => r.entity_id == "{entity_id}" and r._field == "{field_name}")'

    # Query data
    tables = client.query_api().query(query)

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

    # Convert each UTC time to your local timezone
    time_values_local = [time.astimezone(local_timezone) for time in time_values]
    return time_values_local, measurement_values

def read_latest(url: str, token: str, org: str, bucket: str, entity_id: str, field_name: str, sampling_period: str):
    client = InfluxDBClient(url=url, token=token, org=org)
    query = f'from(bucket:"{bucket}") |> range(start: -{sampling_period}) |> filter(fn: (r) => r["entity_id"] == "{entity_id}") |> filter(fn: (r) => r["_field"] == "{field_name}") |> last()'
    # Query data
    try:
        tables = client.query_api().query(query=query)
    except Exception as e:
        print(f"Error querying data: {e}")
        client.close()
        return [], []

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

    # Convert each UTC time to your local timezone
    time_values_local = [time.replace(tzinfo=timezone.utc).astimezone(local_timezone) for time in time_values]
    return time_values_local, measurement_values