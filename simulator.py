import requests
import random
import time
import csv
import os

# ==========================================
# CONFIGURATION & API KEYS
# ==========================================
# Replace with your actual ThingSpeak Write API Key
API_KEY = 'YOUR_WRITE_API_KEY_HERE'
URL = 'https://api.thingspeak.com/update'
LOG_FILE = "factory_sensor_logs.csv"

# ==========================================
# INITIAL MACHINE STATE (Digital Twin)
# ==========================================
current_temp = 45.0
current_humidity = 50.0
machine_status = 1  # 1: Running, 2: Idle, 3: Fault

# Create the local log file with headers if it doesn't exist
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Status", "Temperature_C", "Humidity_Pct"])

print("--- Smart Factory IoT Simulator ---")
print(f"Logging data locally to: {LOG_FILE}")
print("Sending data to ThingSpeak Cloud...")
print("Press Ctrl+C to stop.\n")

# ==========================================
# MAIN SIMULATION LOOP
# ==========================================
try:
    while True:
        # 1. SIMULATE PHYSICAL BEHAVIOR (Digital Twin Logic)
        if machine_status == 1:  # RUNNING
            current_temp += random.uniform(1.5, 4.0)
            current_humidity += random.uniform(-2.0, 2.0)
            # High temp increases chance of a Fault
            if current_temp > 82:
                if random.random() < 0.25: # 25% chance to trigger fault
                    machine_status = 3

        elif machine_status == 2:  # IDLE (Cooling down)
            current_temp -= random.uniform(2.0, 5.0)
            if current_temp < 42: machine_status = 1 # Restart once cooled

        elif machine_status == 3:  # FAULT (Overheated)
            current_temp += random.uniform(-1.0, 3.0)
            # Simulate a technician "resetting" the machine after it stays in fault
            if random.random() < 0.15:
                print(">> Alert: Technician reset machine. Moving to Idle.")
                machine_status = 2

        # Ensure values stay within realistic physical bounds
        current_temp = max(40.0, min(current_temp, 98.0))
        current_humidity = max(30.0, min(current_humidity, 65.0))

        # 2. LOCAL EDGE LOGGING (Safety Backup)
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, machine_status, round(current_temp, 2), round(current_humidity, 2)])

        # 3. PREPARE CLOUD PAYLOAD
        payload = {
            'api_key': API_KEY,
            'field1': machine_status,
            'field2': round(current_temp, 2),
            'field3': round(current_temp - 5, 2), # Simulated ambient warehouse temp
            'field4': round(current_humidity, 2)
        }

        # 4. TRANSMIT TO CLOUD
        try:
            response = requests.get(URL, params=payload, timeout=10)
            if response.status_code == 200:
                print(f"[{timestamp}] Cloud Sync Success | Status: {machine_status} | Temp: {current_temp:.2f}°C")
            else:
                print(f"[{timestamp}] Cloud Error: Status Code {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[{timestamp}] Connection Failed: {e}")

        # ThingSpeak Free Tier requires a delay (usually 15-20 seconds)
        time.sleep(16)

except KeyboardInterrupt:
    print("\nSimulation terminated by user. Data saved to CSV.")
