import json
import time
from sds011 import *
import aqi
from datetime import datetime
import paho.mqtt.client as mqtt

sensor = SDS011("/dev/ttyUSB0", use_query_mode=True)
THINGSBOARD_HOST = '10.0.0.61'
ACCESS_TOKEN = 'x=zR]:fTZR'

# Data capture and upload interval in seconds. Less interval will eventually hang the DHT22.
INTERVAL = 30

sensor_data = {'pmt_2_5': 0, 'aqi_2_5': 0, 'pmt_10': 0, 'aqi_10': 0}


def get_data(n=3):
    sensor.sleep(sleep=False)
    pmt_2_5 = 0
    pmt_10 = 0
    time.sleep(30)
    for i in range(n):
        x = sensor.query()
        pmt_2_5 = pmt_2_5 + x[0]
        pmt_10 = pmt_10 + x[1]
        time.sleep(10)
    pmt_2_5 = round(pmt_2_5 / n, 1)
    pmt_10 = round(pmt_10 / n, 1)
    sensor.sleep(sleep=True)
    time.sleep(10)
    return pmt_2_5, pmt_10


def conv_aqi(pmt_2_5, pmt_10):
    aqi_2_5 = aqi.to_iaqi(aqi.POLLUTANT_PM25, str(pmt_2_5))
    aqi_10 = aqi.to_iaqi(aqi.POLLUTANT_PM10, str(pmt_10))
    return aqi_2_5, aqi_10


def save_log():
    with open("air_quality.csv", "a") as log:
        dt = datetime.now()
        log.write("{},{},{},{},{}\n".format(dt, pmt_2_5, aqi_2_5, pmt_10, aqi_10))
    log.close()


next_reading = time.time()

client = mqtt.Client()

# Set access token
client.username_pw_set(ACCESS_TOKEN)

# Connect to ThingsBoard using default MQTT port and 60 seconds keep alive interval
client.connect(THINGSBOARD_HOST, 1883, 60)

client.loop_start()

try:
    while True:
        pmt_2_5, pmt_10 = get_data()
        aqi_2_5, aqi_10 = conv_aqi(pmt_2_5, pmt_10)
        sensor_data['pmt_2_5'] = pmt_2_5
        sensor_data['pmt_10'] = pmt_10
        sensor_data['aqi_2_5'] = aqi_2_5
        sensor_data['aqi_10'] = aqi_10

        # save log as csv
        try:
            save_log()
        except:
            print("[INFO] Failure in logging data")
        time.sleep(5)

        # Sending humidity and temperature data to ThingsBoard
        client.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)

        next_reading += INTERVAL
        sleep_time = next_reading - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
except KeyboardInterrupt:
    pass

client.loop_stop()
client.disconnect()
