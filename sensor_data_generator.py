import time
import random
import os
import math
from datetime import datetime
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

# Device locations - for multiple sensor simulation
LOCATIONS = ["living_room", "bedroom", "kitchen", "bathroom", "garage"]

# Function to simulate environmental sensor data with more realistic patterns
def simulate_environmental_data(location, timestamp):
    # Base values
    base_temp = {"living_room": 22.0, "bedroom": 21.0, "kitchen": 23.0, "bathroom": 24.0, "garage": 18.0}
    base_humidity = {"living_room": 45.0, "bedroom": 50.0, "kitchen": 55.0, "bathroom": 65.0, "garage": 40.0}
    
    # Day/night cycle simulation (24-hour sinusoidal pattern)
    hour_of_day = datetime.fromtimestamp(timestamp).hour
    day_cycle = math.sin(hour_of_day / 24.0 * 2 * math.pi)
    
    # Add daily cycle variation (±2°C based on time of day)
    temperature = round(base_temp[location] + day_cycle * 2.0 + random.uniform(-0.5, 0.5), 2)
    
    # Humidity often has inverse relationship with temperature
    humidity = round(base_humidity[location] - day_cycle * 5.0 + random.uniform(-2.0, 2.0), 2)
    
    # CO2 levels (ppm) - higher during occupied hours
    co2 = round(400 + random.uniform(0, 50) + (100 if 8 <= hour_of_day <= 22 else 0), 1)
    
    # Light level (lux) - follows day/night pattern with randomness
    light_level = float(round(max(0, 500 * (day_cycle + 1) + random.uniform(-50, 50)), 1))
    if 22 <= hour_of_day or hour_of_day <= 6:  # night time
        light_level = float(round(random.uniform(0, 10), 1))  # minimal light at night
    
    return temperature, humidity, co2, light_level

# Function to simulate power consumption data
def simulate_power_data():
    # Base load (always on)
    base_load = 100  # watts
    
    # Appliance simulations
    refrigerator = 150 * (0.8 + 0.4 * random.random())  # cycling between 80-120% of avg
    
    # Time-based loads
    hour = datetime.now().hour
    
    # Higher usage during morning and evening hours
    time_factor = 1.0
    if 6 <= hour <= 9:  # morning peak
        time_factor = 2.5
    elif 17 <= hour <= 21:  # evening peak
        time_factor = 3.0
    elif 22 <= hour or hour <= 5:  # night (low usage)
        time_factor = 0.6
    
    # Random usage spikes
    random_usage = random.uniform(0, 500) if random.random() < 0.1 else 0
    
    total_power = base_load + refrigerator + (random.uniform(200, 800) * time_factor) + random_usage
    voltage = 120 + random.uniform(-2, 2)  # small voltage fluctuations
    current = round(total_power / voltage, 2)
    
    return round(total_power, 2), round(voltage, 2), current

# Function to simulate water usage data (liters)
def simulate_water_data():
    hour = datetime.now().hour
    
    # Base minimal flow (leaks, etc.)
    base_flow = random.uniform(0, 0.05)
    
    # Morning shower/bathroom usage
    if 6 <= hour <= 9:
        if random.random() < 0.3:  # 30% chance during morning hours
            return round(random.uniform(5, 15), 2)  # shower or toilet
    
    # Evening usage (dishes, etc)
    if 18 <= hour <= 22:
        if random.random() < 0.25:  # 25% chance during evening hours
            return round(random.uniform(1, 8), 2)
    
    # Random usage during the day
    if random.random() < 0.05:  # 5% chance of water usage any time
        return round(random.uniform(0.5, 5), 2)
        
    return round(base_flow, 3)

# Function to send multi-sensor data to InfluxDB
def send_data_to_influxdb():
    current_time = time.time()
    
    # Environmental data for each location
    for location in LOCATIONS:
        temp, humidity, co2, light = simulate_environmental_data(location, current_time)
        
        point = Point("environment") \
            .tag("location", location) \
            .field("temperature", temp) \
            .field("humidity", humidity) \
            .field("co2", co2) \
            .field("light", light)
            
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        
    # Power consumption data
    power, voltage, current = simulate_power_data()
    point = Point("power") \
        .field("consumption", power) \
        .field("voltage", voltage) \
        .field("current", current)
    
    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
    
    # Water usage data
    water_usage = simulate_water_data()
    point = Point("water") \
        .field("usage", water_usage)
    
    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
    
    return {
        "environmental": {loc: {"temp": simulate_environmental_data(loc, current_time)[0], 
                              "humidity": simulate_environmental_data(loc, current_time)[1]} 
                        for loc in LOCATIONS},
        "power": {"consumption": power, "voltage": voltage, "current": current},
        "water": {"usage": water_usage}
    }

# Main loop to simulate and send data
if __name__ == '__main__':
    try:
        print("Starting IoT data simulation. Press CTRL+C to stop.")
        while True:
            data = send_data_to_influxdb()
            print(f"Sent data to InfluxDB at {datetime.now().strftime('%H:%M:%S')}:")
            print(f"  Environmental: {len(LOCATIONS)} locations monitored")
            print(f"  Power: {data['power']['consumption']:.2f}W, {data['power']['voltage']:.2f}V")
            print(f"  Water: {data['water']['usage']:.3f} liters")
            time.sleep(5)
    except KeyboardInterrupt:
        print("Stopping sensor simulation...")
    finally:
        client.close()
