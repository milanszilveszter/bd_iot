import time
import random
import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB v2 connection settings
INFLUXDB_URL = os.getenv('INFLUXDB_URL', '')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', '')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', '')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', '')

# Create InfluxDB client
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Function to simulate sensor data
def simulate_sensor_data():
    temperature = round(random.uniform(20.0, 30.0), 2)
    humidity = round(random.uniform(30.0, 60.0), 2)
    return temperature, humidity

# Function to send data to InfluxDB
def send_data_to_influxdb(temperature, humidity):
    point = Point("environment") \
        .field("temperature", temperature) \
        .field("humidity", humidity)
    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

# Main loop to simulate and send data every 5 seconds
if __name__ == '__main__':
    try:
        while True:
            temp, hum = simulate_sensor_data()
            send_data_to_influxdb(temp, hum)
            print(f"Sent data to InfluxDB: Temperature={temp}, Humidity={hum}")
            time.sleep(5)
    except KeyboardInterrupt:
        print("Stopping sensor simulation...")
    finally:
        client.close()
