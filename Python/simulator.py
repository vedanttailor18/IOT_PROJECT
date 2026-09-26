import requests
import random
import time

URL = "http://127.0.0.1:5000/data"

print("🚀 IoT Sensor Simulator Started")
print("Sending simulated sensor data to Flask...\n")

while True:

    # Normal environmental values
    temperature = round(random.uniform(24, 34), 1)
    humidity = round(random.uniform(45, 75), 1)
    soil = round(random.uniform(30, 80), 1)

    # Mostly normal gas readings
    gas = random.randint(250, 550)

    # Occasionally create a gas spike
    if random.random() < 0.10:
        gas = random.randint(900, 1500)
        print("⚠️ GAS SPIKE SIMULATED!")

    data = {
        "gas": gas,
        "temp": temperature,
        "humidity": humidity,
        "soil": soil
    }

    try:
        response = requests.post(URL, json=data)

        print(
            f"Gas: {gas} | "
            f"Temp: {temperature}°C | "
            f"Humidity: {humidity}% | "
            f"Soil: {soil}% | "
            f"Server: {response.status_code}"
        )

    except requests.exceptions.ConnectionError:
        print("❌ Flask server is not running!")

    time.sleep(2)