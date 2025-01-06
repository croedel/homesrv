#!/usr/bin/env python3
"""
homesrv-html 
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

#================================================
class HomeSrvHtml:
    def __init__(self):
        self.last_update = None
        self.html_data = None
        self._initialize()

    #-------------------------------------------
    def refresh(self):
        now = datetime.now()
        if not self.last_update or now > self.last_update + timedelta(seconds=cfg.get("HTML_REFRESH", 60)):
            logging.info("Refreshing html data")
            html_data = self._read_html_template()

            if self.api_nina: # nina Wetterwarnungen
                snippet = self._get_nina_snippet()    
                html_data = html_data.replace('%%Nina%%', snippet)

            if self.api_awido: # Abfall
                snippet = self._get_awido_snippet()    
                html_data = html_data.replace('%%Waste%%', snippet)

            if self.api_db: # Deutsche Bahn: Abfahrt
                snippet = self._get_db_snippet()    
                html_data = html_data.replace('%%DBtimetable%%', snippet)

            if self.api_disruptions: # Deutsche Bahn: Störungen
                snippet = self._get_disruptions_snippet()    
                html_data = html_data.replace('%%DBdisruptions%%', snippet)

            # Current Date/Time
            snippet = '<div class="refresh-date">Aktualisiert am: {}</div>\n'.format(now.strftime("%d.%m.%Y %H:%M:%S"))
            html_data = html_data.replace('%%CurrentDateTime%%', snippet)

            self.last_update = now
            self.html_data = html_data

    #-------------------------------------------
    def _initialize(self):
        # Create html entity replacement table
        self.html_map = {k: '&{};'.format(v) for k, v in html.entities.codepoint2name.items()}
        self.html_preserve_tags = self.html_map
        del self.html_preserve_tags[38]  # &
        del self.html_preserve_tags[60]  # <
        del self.html_preserve_tags[62]  # >

        # initialite APIs
        self.api_awido = awidoAPI()
        self.api_db = DBtimetableAPI()
        self.api_disruptions = DBdisruptionsAPI()
#        self.api_weather = openweathermapAPI()
        self.api_nina = ninaAPI()

    #-------------------------------------------
    def _read_html_template(self):
        html_path = cfg["WEB_ROOT"]     # Web root directory
        fname = os.path.join(html_path, "index-template.html")  
        try:
            with open(fname, "r") as file: 
                data = file.read()   
                return data
        except Exception as ex:
            logging.error("Couldn't read {}: {}".format(fname, ex))
            return None

    #----------------------------------
    def _get_nina_snippet(self):    
        snippet = '<div class="nina">\n'
        for location in self.api_nina.locations:
            snippet += '<div class="nina-location">\n'
            snippet += '<h3>{}</h3>\n'.format(location["location"].translate(self.html_map))
            data = self.api_nina.get_warnings(ars=location["ars"])
            if len(data["warnings"]) == 0:
                snippet += '<div class="nina-nowarnings">\n'
                snippet += 'Keine Warnungen\n'.translate(self.html_map)
                snippet += '</div>\n\n'
            else:        
                for item in data["warnings"]:
                    snippet += '<div class="nina-warning">\n'
                    snippet += '  <div class="nina-warning-headline">{} ({})</div>\n'.format(item["headline"].translate(self.html_map), 
                                                                                        item["severity"].translate(self.html_map)) 
                    snippet += '  <div class="nina-warning-desc">{}</div>\n'.format(item["description"].translate(self.html_map))
                    snippet += '</div>\n\n'
            snippet += '</div>\n\n'
        snippet += '</div>\n\n'
        return snippet    

    #----------------------------------
    def _get_awido_snippet(self):    
        snippet = '<div class="waste">\n'
        snippet += '<h3>{}</h3>\n'.format(self.api_awido.title.translate(self.html_map))
        snippet += '<table class="waste-table">\n'
        snippet += '<tr>\n'
        snippet += '  <th>Datum</td>\n'
        snippet += '  <th>Typ</td>\n'
        snippet += '  <th>Ort</td>\n'
        snippet += '</tr>\n'
        for item in self.api_awido.upcoming_collections():
            snippet += '<tr>\n'
            snippet += '  <td>{}</td>\n'.format(item["date"].translate(self.html_map))
            snippet += '  <td>{}</td>\n'.format(item["waste_type"].translate(self.html_map))
            snippet += '  <td>{}</td>\n'.format(item["site"].translate(self.html_map))
            snippet += '</tr>\n'
        snippet += '</table>\n'
        snippet += '</div>\n\n'    
        return snippet    

    #----------------------------------
    def _get_db_snippet(self):
        snippet = '<div class="db">\n'
        for dbstation in self.api_db.get_dbstations():
            dbstation.refresh(self.api_db, dt=None)
            dbtt = dbstation.get_timetable(tt_type="departure")
            snippet += '<div class="db-location">\n'
            snippet += '<h3>{}</h3>\n'.format(dbstation.station_name.translate(self.html_map))
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
                snippet += '  <td>{}</td>\n'.format(time_str.translate(self.html_map))
                snippet += '  <td>{}</td>\n'.format(item["train"].translate(self.html_map))
                snippet += '  <td>{}</td>\n'.format(from_to.translate(self.html_map))
                snippet += '  <td>{}</td>\n'.format(platform.translate(self.html_map))
                snippet += '  <td>{}</td>\n'.format(status.translate(self.html_map))
                snippet += '</tr>\n'
            snippet += '</table>\n'
            snippet += '</div>\n\n'
        snippet += '</div>\n\n'    
        return snippet    

    #----------------------------------
    def _get_disruptions_snippet(self):
        snippet = '<div class="db-disruptions">\n'
        for item in self.api_disruptions.get_disruptions():
            snippet += '<div class="db-disruption">\n'
            snippet += '<div class="db-disruption-lines">\n'
            for i in item["lines"]:
                snippet += '  <div class="db-disruption-line-item">{}</div>\n'.format(i["name"])
            snippet += '</div>\n'
            snippet += '  <div class="db-disruption-headline">{}</div>\n'.format(item["headline"].translate(self.html_map))
            snippet += '  <div class="db-disruption-reason">Grund: {}</div>\n'.format(item["cause"]["label"].translate(self.html_map))
            snippet += '  <details>\n' 
            snippet += '    <summary class="db-disruption-summary">{}</summary>\n'.format(item["summary"].translate(self.html_map))
            snippet += '    <div class="db-disruption-text">{}</div>\n'.format(item["text"].translate(self.html_preserve_tags))
            snippet += '  </details>\n' 
            snippet += '</div>\n\n'
        snippet += '</div>\n\n'    
        return snippet    

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

#==========================================

#----------------------------------
def signal_handler(signal_number, frame):
    global run_status
    logging.warning('Received Signal {}. Graceful shutdown initiated.'.format(signal_number))
    run_status = False

#----------------------------------
def main():
    logging.info("Initializing...")
    global run_status
    run_status = True 
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    hsrv = HomeSrvHtml()
                
    logging.info("Entering the main loop")
    while run_status:
        hsrv.refresh()
        print(hsrv.html_data)
        time.sleep(10)

    # clean up
    logging.info("Exiting")

#---------------------------------------------------
if __name__ == '__main__':
    main()
