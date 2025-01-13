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

            if self.api_weather: # Weather
                snippet = self._get_weather_snippet()    
                html_data = html_data.replace('%%weather%%', snippet)

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
        self.api_weather = openweathermapAPI()
        self.api_nina = ninaAPI()

    #-------------------------------------------
    def _read_file(self, fname):
        try:
            with open(fname, "r") as file: 
                data = file.read()   
                return data
        except Exception as ex:
            logging.debug("Couldn't read {}: {}".format(fname, ex))
            return None

    #-------------------------------------------
    def _read_html_template(self):
        html_path = cfg["WEB_ROOT"]     # Web root directory
        fname_user = os.path.join(html_path, "index.html") 
        fname_template = os.path.join(html_path, "index-template.html")
        # Try to read index.html (user generated) and use index-template.html as fallback
        data = self._read_file(fname_user)
        if not data: 
            data = self._read_file(fname_template)  
        if not data:
            logging.critical("Couldn't read {}: {}".format(fname, ex))
        return data    

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
                    if item["severity"] == "Extreme":
                        css_class = "nina-warning-extreme"
                    elif item["severity"] == "Severe":
                        css_class = "nina-warning-severe"
                    elif item["severity"] == "Moderate":
                        css_class = "nina-warning-moderate"
                    else: # Minimal or Unknown
                        css_class = "nina-warning-minimal"

                    snippet += '<div class="{}">\n'.format(css_class)
                    snippet += '  <div class="nina-warning-headline"><img src="images/alert.png" alt="alert" title="Achtung!">{} ({})</div>\n'.format(item["headline"].translate(self.html_map), 
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
        snippet += '  <th>Datum</th>\n'
        snippet += '  <th>Typ</th>\n'
        snippet += '  <th>Ort</th>\n'
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
            snippet += '  <th>Zeit</th>\n'
            snippet += '  <th>Zug</th>\n'
            snippet += '  <th>Ziel</th>\n'
            snippet += '  <th>Gleis</th>\n'
            snippet += '  <th>Status</th>\n'
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
            snippet += '  <div class="db-disruption-reason">{}</div>\n'.format(item["cause"]["label"].translate(self.html_map))
            snippet += '  <details>\n' 
            snippet += '    <summary class="db-disruption-summary">{}</summary>\n'.format(item["summary"].translate(self.html_map))
            snippet += '    <div class="db-disruption-text">{}</div>\n'.format(item["text"].translate(self.html_preserve_tags))
            snippet += '  </details>\n' 
            snippet += '</div>\n\n'
        snippet += '</div>\n\n'    
        return snippet    

    #----------------------------------
    def _get_weather_snippet(self):
        snippet = '<div class="weather">\n'
        for item in self.api_weather.get_locations():
            snippet += '<h3>{}</h3>\n'.format(item.translate(self.html_map))

            data = self.api_weather.get_weather(item, 'now')
            snippet += '<div class="weather-location">\n'

            snippet += '<div class="weather-overview">\n'
            snippet += '<div class="weather-generic">\n'
            snippet += '  <img src="images/sunrise.png" alt="sunrise" title="Sonnenaufgang">{} Uhr\n'.format(data['sunrise_txt'])
            snippet += '  <img src="images/sunset.png" alt="sunset" title="Sonnenuntergang">{} Uhr\n'.format(data['sunset_txt'])
            snippet += '  <img src="images/uvidx.png" alt="uv index" title="UV-Index">{}\n'.format(data['uv_index_txt'].translate(self.html_map))
            snippet += '</div>\n'
            snippet += '<div class="weather-situation">\n'
            snippet += '  <img src="images/{}" alt="weather situation" title="Wetterlage">\n'.format(data['icon'])
            snippet += '  <p>{}</p>\n'.format(data['description'].translate(self.html_map))
            snippet += '</div>\n'
            snippet += '</div>\n'

            snippet += '<div class="weather-detail">\n'
            snippet += '<ul>\n'
            snippet += '<li><img src="images/temp.png" alt="temperature" title="Temperatur">{}&#8451; (gef&uuml;hlt: {}&#8451;)</li>\n'.format(data['temp'], data['feels_like'])
            txt = ''
            if data.get("rain_txt"):
                txt = ' - Regen: {}'.format(data['rain_txt'].translate(self.html_map))
            if data.get("snow_txt"):
                txt = ' - Schneefall: {}'.format(data['snow_txt'].translate(self.html_map))
            snippet += '<li><img src="images/rainprop.png" alt="rainprop" title="Niederschlag">{}{}</li>\n'.format(data['precipitation_txt'].translate(self.html_map), txt)
            snippet += '<li><img src="images/humidity.png" alt="humidity" title="Luftfeuchtigkeit">{}&percnt;</li>\n'.format(data['humidity'])
            snippet += '<li><img src="images/pressure.png" alt="pressure" title="Luftdruck">{}hPa</li>\n'.format(data['pressure'])
            txt = ''
            if data.get("wind_gust_kmh") and int(data.get("wind_gust_kmh", 0))>0:
                txt = ' - B&ouml;en: {}km/h'.format(data['wind_gust_kmh'])
            snippet += '<li><img src="images/wind.png" alt="wind" title="Wind">{}km/h - {}{}</li>\n'.format(data['wind_speed_kmh'], data['wind_direction'], txt)
            snippet += '</ul>\n'
            data = self.api_weather.get_weather(item, 'daytime')
            snippet += '</div>\n'    
            snippet += '</div>\n\n'
        snippet += '</div>\n\n'    
        return snippet    

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
