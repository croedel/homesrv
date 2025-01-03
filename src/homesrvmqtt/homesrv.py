#!/usr/bin/env python3
"""
homesrv - server daemon which retrieves data from configured data sources and writes the data to you MQTT server 
(c) 2024 by Christian Rödel 
"""

from datetime import datetime, timedelta
import logging
import time
import signal
from homesrvmqtt.config import cfg
from homesrvmqtt.mqtt import mqtt_start, mqtt_stop, mqtt_publish
from homesrvAPI.awidoAPI import awidoAPI
from homesrvAPI.openweathermapAPI import openweathermapAPI
from homesrvAPI.DBtimetableAPI import DBtimetableAPI
from homesrvAPI.DBdisruptionsAPI import DBdisruptionsAPI
from homesrvAPI.ninaAPI import ninaAPI

#----------------------------------
def signal_handler(signal_number, frame):
    global run_status
    logging.warning('Received Signal {}. Graceful shutdown initiated.'.format(signal_number))
    run_status = False


#==========================================
def main():
    global run_status
    run_status = True 

    # Initialization
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logging.info("Initializing...")
    last_update = None
    api_awido = None
    api_weather = None
    api_db = None
    api_disruptions = None
    api_nina = None
    if cfg.get("MQTT_enable_awido"):
        logging.info("Initializing awidoAPI")
        api_awido = awidoAPI()
    if cfg.get("MQTT_enable_db"):
        logging.info("Initializing DB API")
        api_db = DBtimetableAPI()
        api_disruptions = DBdisruptionsAPI()
    if cfg.get("MQTT_enable_weather"):
        logging.info("Initializing openweathermapAPI")
        api_weather = openweathermapAPI()
    if cfg.get("MQTT_enable_nina"):
        logging.info("Initializing ninaAPI")
        api_nina = ninaAPI()
  
    logging.info("Entering the run loop")
    while run_status:
        now = datetime.now()
        if not last_update or now > last_update + timedelta(seconds=cfg.get("MQTT_refresh", 300)):
            last_update = now
            logging.info("Refreshing data")

            # nina
            if api_nina:
                for location in api_nina.locations:
                    topic = "nina/{}".format(location["ars"])
                    data = api_nina.get_warnings(ars=location["ars"])     
                    mqtt_publish(topic, data)

            # waste
            if api_awido:
                topic = "waste/{}/current".format(api_awido.title)
                data = api_awido.current_collections()
                mqtt_publish(topic, data)
                topic = "waste/{}/upcoming".format(api_awido.title)
                data = api_awido.upcoming_collections()
                mqtt_publish(topic, data)

            # Deutsche Bahn
            if api_db:
                for dbstation in api_db.get_dbstations():
                    topic = "db/{}".format(dbstation.station_id)
                    data = dbstation.get_station_base_data() 
                    mqtt_publish(topic, data)
                    topic = "db/{}/departure".format(dbstation.station_id)
                    dbstation.refresh(api_db, dt=None)
                    dbtt = dbstation.get_timetable(tt_type="departure")
                    data = dbtt.get_timetable()
                    mqtt_publish(topic, data)

                topic = "db/disruptions"
                data = api_disruptions.get_disruptions()
                mqtt_publish(topic, data)

            # weather
            if api_weather:
                for location in api_weather.get_locations():
                    topic = "weather/{}".format(location)
                    data = api_weather.get_weather(location, 'base')
                    mqtt_publish(topic, data)
                    topic = "weather/{}/now".format(location)
                    data = api_weather.get_weather(location, 'now')
                    mqtt_publish(topic, data)
                    topic = "weather/{}/daytime".format(location)
                    data = api_weather.get_weather(location, 'daytime')
                    mqtt_publish(topic, data)
                    topic = "weather/{}/daily".format(location)
                    data = api_weather.get_weather(location, 'daily')
                    mqtt_publish(topic, data)

        time.sleep(10)

    # clean up
    logging.info("Exiting")
 
#---------------------------------------------------
if __name__ == '__main__':
    main()
