from flask import Flask, render_template, jsonify, request
import paho.mqtt.client as mqtt
import json
import threading
import requests
from datetime import datetime

app = Flask(__name__)


# =====================================================
# MQTT CONFIGURATION
# =====================================================

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

MQTT_TOPIC = "vedant/smartiot/environment"


# =====================================================
# LATEST IoT DATA
# =====================================================

latest_iot_data = {
    "temperature": 0,
    "humidity": 0,
    "wind": 0,
    "aqi": 0,
    "source": "Wokwi ESP32",
    "last_update": None
}


# =====================================================
# ONLINE LOCATION
# =====================================================

location = {
    "latitude": None,
    "longitude": None
}


# =====================================================
# MQTT MESSAGE RECEIVED
# =====================================================

def on_message(client, userdata, message):

    global latest_iot_data

    try:

        payload = message.payload.decode("utf-8")

        print()
        print("========================================")
        print("MQTT DATA RECEIVED")
        print("========================================")
        print("Topic:", message.topic)
        print("Payload:", payload)

        data = json.loads(payload)

        latest_iot_data["temperature"] = data.get(
            "temperature", 0
        )

        latest_iot_data["humidity"] = data.get(
            "humidity", 0
        )

        latest_iot_data["wind"] = data.get(
            "wind", 0
        )

        latest_iot_data["aqi"] = data.get(
            "aqi", 0
        )

        latest_iot_data["source"] = "Wokwi ESP32"

        latest_iot_data["last_update"] = (
            datetime.now().strftime("%H:%M:%S")
        )

        print("✓ IoT data updated")

    except Exception as e:

        print(
            "MQTT processing error:",
            e
        )


# =====================================================
# MQTT CONNECTION
# =====================================================

def start_mqtt():

    print()
    print("========================================")
    print("STARTING MQTT CLIENT")
    print("========================================")

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION1,
        client_id="flask-dashboard-client"
    )

    client.on_message = on_message

    print(
        "Connecting to MQTT broker..."
    )

    client.connect(
        MQTT_BROKER,
        MQTT_PORT,
        60
    )

    print(
        "✓ Connected to HiveMQ"
    )

    client.subscribe(
        MQTT_TOPIC
    )

    print(
        "✓ Subscribed to:"
    )

    print(
        MQTT_TOPIC
    )

    print()
    print(
        "Waiting for Wokwi ESP32 data..."
    )

    client.loop_forever()


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/")
def dashboard():

    return render_template(
        "index.html"
    )


# =====================================================
# LOCATION
# =====================================================

@app.route(
    "/location",
    methods=["POST"]
)
def receive_location():

    global location

    data = request.json

    location["latitude"] = data.get(
        "latitude"
    )

    location["longitude"] = data.get(
        "longitude"
    )

    print()
    print(
        "Location received:"
    )

    print(
        location
    )

    return jsonify({
        "status": "location received"
    })


# =====================================================
# ONLINE ENVIRONMENTAL DATA
# =====================================================

@app.route("/live-data")
def live_data():

    # -------------------------------------------------
    # If location is not available
    # -------------------------------------------------

    if (
        location["latitude"] is None
        or
        location["longitude"] is None
    ):

        return jsonify(
            latest_iot_data
        )


    latitude = location["latitude"]

    longitude = location["longitude"]


    try:

        # -------------------------------------------------
        # WEATHER API
        # -------------------------------------------------

        weather_url = (

            "https://api.open-meteo.com/v1/forecast"

            f"?latitude={latitude}"

            f"&longitude={longitude}"

            "&current="

            "temperature_2m,"

            "relative_humidity_2m,"

            "wind_speed_10m"

        )


        weather_response = requests.get(
            weather_url,
            timeout=10
        )


        weather = (
            weather_response
            .json()
            ["current"]
        )


        # -------------------------------------------------
        # AIR QUALITY API
        # -------------------------------------------------

        air_url = (

            "https://air-quality-api.open-meteo.com/v1/air-quality"

            f"?latitude={latitude}"

            f"&longitude={longitude}"

            "&current="

            "us_aqi,"

            "pm2_5,"

            "pm10"

        )


        air_response = requests.get(
            air_url,
            timeout=10
        )


        air = (
            air_response
            .json()
            ["current"]
        )


        # -------------------------------------------------
        # RETURN IoT DATA
        # -------------------------------------------------

        response = {

            "temperature":
                latest_iot_data[
                    "temperature"
                ],

            "humidity":
                latest_iot_data[
                    "humidity"
                ],

            "wind":
                latest_iot_data[
                    "wind"
                ],

            "aqi":
                latest_iot_data[
                    "aqi"
                ],

            "online_temperature":
                weather[
                    "temperature_2m"
                ],

            "online_humidity":
                weather[
                    "relative_humidity_2m"
                ],

            "online_wind":
                weather[
                    "wind_speed_10m"
                ],

            "online_aqi":
                air[
                    "us_aqi"
                ],

            "pm25":
                air[
                    "pm2_5"
                ],

            "pm10":
                air[
                    "pm10"
                ],

            "source":
                latest_iot_data[
                    "source"
                ],

            "last_update":
                latest_iot_data[
                    "last_update"
                ]

        }


        return jsonify(
            response
        )


    except Exception as e:

        print(
            "Online API error:",
            e
        )

        return jsonify(
            latest_iot_data
        )


# =====================================================
# IoT DATA ONLY
# =====================================================

@app.route("/iot-data")
def iot_data():

    return jsonify(
        latest_iot_data
    )


# =====================================================
# START APPLICATION
# =====================================================

if __name__ == "__main__":

    # Start MQTT in background
    mqtt_thread = threading.Thread(
        target=start_mqtt,
        daemon=True
    )

    mqtt_thread.start()


    # Start Flask

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )