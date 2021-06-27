\
import time
from datetime import datetime
import paho.mqtt.client as mqtt
import psutil
from sds011 import *
import aqi

sensor = SDS011("/dev/ttyUSB0", use_query_mode=True)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully")
    else:
        print("Connect returned result code: " + str(rc))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print("Received message: " + msg.topic + " -> " + msg.payload.decode("utf-8"))


def get_data(n=3):
        sensor.sleep(sleep=False)
        pmt_2_5 = 0
        pmt_10 = 0
        time.sleep(30)
        for i in range (n):
            x = sensor.query()
            pmt_2_5 = pmt_2_5 + x[0]
            pmt_10 = pmt_10 + x[1]
            time.sleep(10)
        pmt_2_5 = round(pmt_2_5/n, 1)
        pmt_10 = round(pmt_10/n, 1)
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

# create the client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# enable TLS
client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)

# set username and password
client.username_pw_set("Albardin", "Password")

# connect to HiveMQ Cloud on port 8883
client.connect("52267785dc8c4134a1bcd0ad0d491cf9.s1.eu.hivemq.cloud", 8883)

# subscribe to the topic "my/test/topic"
client.subscribe("project/air/report")

while True:        
    pmt_2_5, pmt_10 = get_data()
    aqi_2_5, aqi_10 = conv_aqi(pmt_2_5, pmt_10)
    tPayload = "field1=" + str(pmt_2_5)+ "&field2=" + str(aqi_2_5)+ "&field3=" + str(pmt_10)+ "&field4=" + str(aqi_10)
    try:
        # publish "Hello" to the topic "my/test/topic"
        client.publish(tPayload)
        # Blocking call that processes network traffic, dispatches callbacks and handles reconnecting.
        client.loop_forever()
        time.sleep(600)
    except:
        print ("[INFO] Failure in sending data")
        
        
            
            


