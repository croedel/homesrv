#!/usr/bin/env python3
"""
homeserver - server daemon which retrieves data from configured data sources and writes the data as HTML 
(c) 2024 by Christian Rödel 
"""

from datetime import datetime, timedelta
import html.entities
import logging
import time
import signal
import os
import html
from homesrv.config import cfg
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
    # Initialization
    global run_status
    logging.info("Initializing...")
    run_status = True 

    # create html entity replacement table
    html_map = {k: '&{};'.format(v) for k, v in html.entities.codepoint2name.items()}
    html_preserve_tags = html_map
    del html_preserve_tags[38]  # &
    del html_preserve_tags[60]  # <
    del html_preserve_tags[62]  # >

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
                
    last_update = None
    api_awido = awidoAPI()
    api_db = DBtimetableAPI()
    api_disruptions = DBdisruptionsAPI()
#    api_weather = openweathermapAPI()
    api_nina = ninaAPI()
  
    logging.info("Entering the run loop")
    while run_status:
        now = datetime.now()
        if not last_update or now > last_update + timedelta(seconds=cfg.get("MQTT_refresh", 300)):
            last_update = now
            logging.info("Refreshing data")
            html_data = read_html_template()

            # nina Wetterwarnungen
            if api_nina:
                snippet = ''
                for location in api_nina.locations:
                    snippet += '<h3>{}</h3>\n'.format(location["location"].translate(html_map))
                    data = api_nina.get_warnings(ars=location["ars"])
                    if len(data["warnings"]) == 0:
                        snippet += '<div class="nina-nowarnings">\n'
                        snippet += 'Keine Warnungen\n'.translate(html_map)
                        snippet += '</div>\n\n'
                    else:        
                        for item in data["warnings"]:
                            snippet += '<div class="nina-warning">\n'
                            snippet += '  <div class="nina-warning-headline">{} ({})</div>\n'.format(item["headline"].translate(html_map), 
                                                                                                item["severity"].translate(html_map)) 
                            snippet += '  <div class="nina-warning-desc">{}</div>\n'.format(item["description"].translate(html_map))
                            snippet += '</div>\n\n'
                html_data = html_data.replace('%%Nina%%', snippet)

            # Abfall
            if api_awido:
                snippet = ''
                snippet += '<h3>{}</h3>\n'.format(api_awido.title.translate(html_map))
                snippet += '<table class="waste-table">\n'
                snippet += '<tr>\n'
                snippet += '  <th>Datum</td>\n'
                snippet += '  <th>Typ</td>\n'
                snippet += '  <th>Ort</td>\n'
                snippet += '</tr>\n'
                for item in api_awido.upcoming_collections():
                    snippet += '<tr>\n'
                    snippet += '  <td>{}</td>\n'.format(item["date"].translate(html_map))
                    snippet += '  <td>{}</td>\n'.format(item["waste_type"].translate(html_map))
                    snippet += '  <td>{}</td>\n'.format(item["site"].translate(html_map))
                    snippet += '</tr>\n'
                snippet += '</table>\n\n'
                html_data = html_data.replace('%%Waste%%', snippet)

            # Deutsche Bahn: Abfahrt    
            if api_db:
                snippet = ''
                for dbstation in api_db.get_dbstations():
                    dbstation.refresh(api_db, dt=None)
                    dbtt = dbstation.get_timetable(tt_type="departure")
                    snippet = ''
                    snippet += '<h3>{}</h3>\n'.format(dbstation.station_name.translate(html_map))
                    snippet += '<table class="db-table">\n'
                    snippet += '<tr>\n'
                    snippet += '  <th>Zeit</td>\n'
                    snippet += '  <th>Zug</td>\n'
                    snippet += '  <th>Ziel</td>\n'
                    snippet += '  <th>Gleis</td>\n'
                    snippet += '  <th>Status</td>\n'
                    snippet += '</tr>\n'
                    for item in dbtt.timetable:
                        dtime = datetime.strptime(item["date"], "%d.%m.%Y %H:%M")
                        if item.get("scheduled_date"):    
                            dtime_scheduled = datetime.strptime(item["scheduled_date"], "%d.%m.%Y %H:%M")
                            time_str = "{} ({})".format(dtime.strftime("%H:%M"), dtime_scheduled.strftime("%H:%M"))
                        else:    
                            time_str = "{}".format(dtime.strftime("%H:%M"))
                        platform = item.get("platform")
                        if item.get("scheduled_platform"):
                            platform = "{} [{}]".format(platform, item["scheduled_platform"])         
                        from_to = item.get("from_to")
                        if item.get("scheduled_from_to"):
                            from_to = "{} [{}]".format(from_to, item["scheduled_from_to"])
                        status = ""
                        if item.get("status") and len(item.get("status"))>0:
                            status = "- " + item.get("status")     
                        if item.get("message"):
                            status += " ! " + item.get("message") + " !"    

                        snippet += '<tr>\n'
                        snippet += '  <td>{}</td>\n'.format(time_str.translate(html_map))
                        snippet += '  <td>{}</td>\n'.format(item["train"].translate(html_map))
                        snippet += '  <td>{}</td>\n'.format(from_to.translate(html_map))
                        snippet += '  <td>{}</td>\n'.format(platform.translate(html_map))
                        snippet += '  <td>{}</td>\n'.format(status.translate(html_map))
                        snippet += '</tr>\n'
                    snippet += '</table>\n\n'
    
                html_data = html_data.replace('%%DBtimetable%%', snippet)

            # Deutsche Bahn: Störungen
            if api_disruptions:
                snippet = ''
                for item in api_disruptions.get_disruptions():
                    snippet += '<div class="db-disruption">\n'
                    snippet += '<div class="db-disruption-lines">\n'
                    for i in item["lines"]:
                        snippet += '  <div class="db-disruption-line-item">{}</div>\n'.format(i["name"])
                    snippet += '</div>\n'
                    snippet += '  <div class="db-disruption-headline">{}</div>\n'.format(item["headline"].translate(html_map))
                    snippet += '  <div class="db-disruption-reason">Grund: {}</div>\n'.format(item["cause"]["label"].translate(html_map))
                    snippet += '  <details>\n' 
                    snippet += '    <summary class="db-disruption-summary">{}</summary>\n'.format(item["summary"].translate(html_map))
                    snippet += '    <div class="db-disruption-text">{}</div>\n'.format(item["text"].translate(html_preserve_tags))
                    snippet += '  </details>\n' 
                    snippet += '</div>\n\n'
                html_data = html_data.replace('%%DBdisruptions%%', snippet)

            # Current Date/Time
            snippet = '<div class="refresh-date">Letzte Aktualisierung: {}</div>\n'.format(now.strftime("%d.%m.%Y %H:%M:%S"))
            html_data = html_data.replace('%%CurrentDateTime%%', snippet)
            # Write html file
            write_html_file(html_data)            

        time.sleep(10)

    # clean up
    logging.info("Exiting")

'''
            # weather
            if api_weather:
                for location in api_weather.get_locations():
                    topic = "weather/{}".format(location)
                    data = api_weather.get_weather(location, 'base')

                    topic = "weather/{}/now".format(location)
                    data = api_weather.get_weather(location, 'now')

                    topic = "weather/{}/daytime".format(location)
                    data = api_weather.get_weather(location, 'daytime')

                    topic = "weather/{}/daily".format(location)
                    data = api_weather.get_weather(location, 'daily')
'''

#-------------------------------------------
def read_html_template():
    try:
        BASE_DIR = os.path.dirname(__file__) # Base installation directory
        templ_fname = os.path.join(BASE_DIR, "html-template.html")
        with open(templ_fname, "r") as file: 
            data = file.read()   
    except Exception as ex:
        print("ERROR - Couldn't read 'html-template.html': {}".format(ex))
        return None

    return data

#-------------------------------------------
def write_html_file(html_data):
    html_path = os.path.dirname(__file__) # Base installation directory
#    html_path = cfg["HTML_DIR"]     # HTML directory
    fname = os.path.join(html_path, "homesrv.html")  
 
    try:
        os.makedirs(os.path.dirname(html_path), exist_ok=True)
        with open(fname, "w", encoding="UTF-8") as file: 
            file.write(html_data) 
    except Exception as ex:
        logging.error("ERROR - Couldn't write {}: {}".format(fname, ex))
        return False

    logging.info("Successfully created {}".format(fname))
    return True




#---------------------------------------------------
if __name__ == '__main__':
    main()
