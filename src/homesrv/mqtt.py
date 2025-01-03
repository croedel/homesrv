#!/usr/bin/env python3
"""
MQTT client base implemantation
(c) 2024 by Christian Rödel 
"""
from homesrv.config import cfg
import json
import logging

try:
    import paho.mqtt.client as mqttcl
    import paho.mqtt.publish as publish
except Exception as e:
    logging.warning("MQTT not set up because of: {}".format(e))
    
# ============ MQTT ================
def on_mqtt_connect(mqttclient, userdata, flags, rc, prop):
    if rc == 0:
        logging.info("Connected to MQTT broker")
    else:
        logging.error("Error while connecting to MQTT broker: rc={}".format(rc))

def on_mqtt_disconnect(mqttclient, userdata, rc):
    logging.warning("MQTT broker disconnected: rc={}".format(rc))
  
def on_mqtt_subscribe(mqttclient, userdata, mid, granted_qos):
    logging.info("MQTT broker subscribed to mid {}".format(mid))

def on_mqtt_message(mqttclient, userdata, message):
    try:
        msg = message.payload.decode("utf-8")
        topic = message.topic.split("/")
        logging.info("Received topic {}, msg {}".format(topic, msg))
    except Exception as e:
        logging.warning("Error while handling MQTT message: {}".format(str(e)))

def mqtt_start( api=None ): 
    try: 
        client = mqttcl.Client(mqttcl.CallbackAPIVersion.VERSION2)
        client.user_data_set(api) # register API instance
        if cfg['MQTT_login']:
            client.username_pw_set(cfg['MQTT_login'], cfg['MQTT_password']) 
        client.on_connect = on_mqtt_connect
        client.on_disconnect = on_mqtt_disconnect
        client.on_message = on_mqtt_message
        client.on_subscribe = on_mqtt_subscribe
        client.connect(cfg['MQTT_server'], cfg['MQTT_port'], keepalive = 60) 
        if api:
            client.subscribe(cfg["MQTT_base_topic"]+"/cmd", qos=0)
            client.loop_start()
            logging.info('MQTT server started')
        return client
    except Exception as e:
        logging.warning("Couldn't start MQTT: {}".format(str(e)))

def mqtt_stop(client):
    try: 
        client.loop_stop()
        logging.info('MQTT server stopped')
    except Exception as e:
        logging.warning("Couldn't stop MQTT: {}".format(str(e)))

def mqtt_publish(topic, data):
    topic = cfg["MQTT_base_topic"] + "/" + topic
    if isinstance(data, (dict, list)):
        payload = json.dumps(data)
    if cfg['MQTT_disable']: # Don't do anything - just logg
        logging.info("- {}: {}".format(topic, payload))
    else:  
        auth = None
        if cfg['MQTT_login']:
            auth = { 'username': cfg['MQTT_login'], 'password': cfg['MQTT_password'] }  
        logging.debug("- {}: {}".format(topic, payload))
        try:
            publish.single(topic, payload=payload, hostname=cfg['MQTT_server'], port=cfg['MQTT_port'], auth=auth)
        except Exception as e:
            logging.error("Could't send MQTT command: {}".format(str(e)))
