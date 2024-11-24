#!/usr/bin/env python3
"""
homesrv
(c) 2024 by Christian Rödel 
"""

from datetime import datetime, timedelta
import logging
import time
import signal
from homesrvmqtt.config import cfg
from homesrvmqtt.mqtt import mqtt_start, mqtt_stop, mqtt_publish
from openweathermap.openweathermapAPI import openweathermapAPI

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

    logging.info("Starting")
    api = openweathermapAPI()
    last_update = None
  
    while run_status:
        now = datetime.now()
        if not last_update or now > last_update + timedelta(minutes=1):
            last_update = now
            for location in api.get_locations():
                topic = "weather/{}".format(location)
                wdata = api.get_weather(location, ['base','now'])
                mqtt_publish(topic, wdata)

        time.sleep(5)

    # clean up
    logging.info("Exiting")
 
#---------------------------------------------------
if __name__ == '__main__':
    main()
