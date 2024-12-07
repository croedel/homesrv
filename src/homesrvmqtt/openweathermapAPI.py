#!/usr/bin/python
""" 
API class which retrieves data from openweathermap.org 
(c) 2024 by Christian Rödel 
"""

from homesrvmqtt.config import cfg
import requests
import locale
from datetime import datetime, timedelta
import logging

#======================================
class openweathermapAPI:
    base_url = "https://api.openweathermap.org/data/3.0/onecall"
    geo_url = "http://api.openweathermap.org/geo/1.0/direct"

    #-----------------------------------
    def __init__(self):
        self.weather = {}
        self._read_config()
        if cfg['weather_lang'] == 'de':
            locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")     

    #-----------------------------------
    # add a location by specifying lat an lon coordinates
    def add_location(self, name, lat, lon, country="", state=""):
        self.weather[name] = {
            "country": country,
            "state": state,
            "lat": lat,
            "lon": lon,
            "last_refresh": None
        }
        logging.debug( "Added {}, {} {} : lat={}, lon={}".format(name, country, state, lat, lon) )

    #-----------------------------------
    # add a location by searching for a name; lat and lon will be retrieved using a geo-location service 
    def add_location_by_name(self, city, country=None):
        locations = self._search_location(city, country)
        if locations:
            loc = locations[0]  # take first one
            self.weather[loc["name"]] = {
                "country": loc.get("country",""),
                "state": loc.get("state",""),
                "lat": loc["lat"],
                "lon": loc["lon"],
                "last_refresh": None
            }
            logging.debug( "Added {}, {} {} : lat={}, lon={}".format(loc["name"], loc["country"], loc.get("state",""), loc["lat"], loc["lon"]) )
            return loc["name"]
        else:
            logging.error( "Location not found :-(" ) 

    #-----------------------------------
    # get list of locations
    def get_locations(self):
        locations = []
        for location, _ in self.weather.items():
            locations.append(location)
        return locations

    #-----------------------------------
    # delete the given location 
    def delete_location(self, location):
        if location in self.weather:
            del self.weather[location]
            logging.debug( "Location {} deleted".format(location) )
        else:
            logging.error( "Unknown location {} - couldn't delete this location".format(location) ) 

    #-----------------------------------
    def clear_locations(self):
        self.weather.clear()
        logging.debug( "Locations cleared" )

    #-----------------------------------
    def print_locations(self):
        txt = ""
        for location, val in self.weather.items():
            txt += "{}, {} {} : lat={}, lon={}\n".format(location, val["country"], val["state"], val["lat"], val["lon"]) 
        return txt    

    #------------------------------------------------------------------        
    def get_weather(self, location, categogy=None):
        self.refresh_location(location)
        wdata = self._prettify_weather(location)
        if categogy:
            ret = {}
            for k, v in wdata.items():
                if k == categogy:
                    return v    
        else:
            return wdata

    #------------------------------------------------------------------        
    # refresh all weather infos
    def refresh(self): 
        for location, _ in self.weather.items():
            self.refresh_location(location)

    #------------------------------------------------------------------        
    # refresh weather info for a location
    def refresh_location(self, location): 
        now = datetime.now()
        item = self.weather.get(location)
        if item:
            last_refresh = item.get("last_refresh")  
            if not last_refresh or now > last_refresh + timedelta(seconds=300):    
                logging.info("Refreshing weather info for {}".format(location))
                self.weather[location] = self._request_openweathermap(item["lat"], item["lon"])                
                self.weather[location]["last_refresh"] = now
                self.weather[location]['location'] = location
        else:    
            logging.error( "Undefined location: {}".format(location) )


    #-----------------------------------
    def search_location(self, city, country=None):
        locations = self._search_location(city, country, 10)
        if locations:
            result = []
            for loc in locations:
                data = {}
                data["name"] = loc.get("name","")
                data["country"] = loc.get("country","")
                data["state"] = loc.get("state","")
                data["lat"] = loc["lat"]
                data["lon"] = loc["lon"]
                result.append(data)
            return result
        else:
            logging.error( "Location not found :-(" ) 


    #-----------------------------------
    # Helper functions
    #-----------------------------------
    def _request_openweathermap(self, lat, lon):    # get weather info from OpenWeatherMap API
        payload = { 'lat': lat, 'lon': lon, 'units': cfg['weather_units'], 'lang': cfg['weather_lang'], 'appid': cfg['weather_api_key'] } 
        try:
            response = requests.get(self.base_url, payload, timeout=3)
        except requests.exceptions.RequestException as err:
            logging.error( "Couldn't request openweathermap API: Exception {:s}".format(str(err)) )
        else:
            if response.status_code == 200:
                return response.json()
            else:
                logging.error( "Error while requesting openweathermap API: {:s} -> {:d} {:s}".format( str(payload), response.status_code, response.reason) )

    #-----------------------------------
    def _search_location(self, city, country=None, limit=1):
        if country:
            location = "{},{}".format(city, country) 
        else:
            location = city 

        payload = { 'q': location, 'appid': cfg['weather_api_key'], 'limit': limit }
        try:
            response = requests.get(self.geo_url, payload, timeout=3)
        except requests.exceptions.RequestException as err:
            logging.error( "Couldn't request openweathermap API: Exception {:s}".format(str(err)) )
        else:
            if response.status_code == 200:
                json = response.json()
                if json:
                    return json
            else:
                logging.error( "Error while requesting openweathermap API: {:s} -> {:d} {:s}".format( str(payload), response.status_code, response.reason) )

    #-----------------------------------
    def _read_config(self):
        # read api_key as mandatory entry
        if len(cfg.get('weather_api_key', '')) < 30:
            logging.fatal("Invalid api_key. Please set valid key within config.yaml")
            exit()

        # read locations from config file    
        if cfg.get('weather_locations'):
            for name, params in cfg.get('weather_locations').items(): 
                self.add_location(name=name, lat=params['lat'], lon=params['lon'], country=params.get('country'), state=params.get('state'))

    #===============================================================
    # Helper functions
    #-----------------------------------
    def _uvi2str(self, uvi):
        if uvi < 3:
            return cfg['uv_index'][0]
        elif uvi < 6:
            return cfg['uv_index'][1]
        elif uvi < 8:
            return cfg['uv_index'][2]
        elif uvi < 11:
            return cfg['uv_index'][3]
        else:
            return cfg['uv_index'][4]

    #-----------------------------------
    def _degree2str(self, degree):
        wind_rose = ('N','NO','O','SO','S','SW','W','NW','N')
        idx = int((degree + 22.5) / 45)
        return wind_rose[idx]

    #-----------------------------------
    def _clouds2str(self, coverage):
        coverage = int(coverage/100*8)
        return cfg['clouds'][coverage]

    #-----------------------------------
    def _moon2str(self, moonphase):
        moon = float(moonphase)*8
        if moon < 0.1 or moon > 7.9:
            return cfg['moonphase'][0] # Neumond
        elif moon > 3.9 and moon < 4.1:
            return cfg['moonphase'][4] # Vollmond
        elif moon < 2:
            return cfg['moonphase'][1] 
        elif moon < 3:
            return cfg['moonphase'][2] 
        elif moon < 4:
            return cfg['moonphase'][3] 
        elif moon < 6:
            return cfg['moonphase'][5] 
        elif moon < 7:
            return cfg['moonphase'][6] 
        elif moon < 8:
            return cfg['moonphase'][7]        

    #-----------------------------------
    def _visibility2str(self, visibility):
        if visibility < 50:
            return cfg['visibility'][0]
        elif visibility < 100:
            return cfg['visibility'][1]
        elif visibility < 200:
            return cfg['visibility'][2]
        elif visibility < 500:
            return cfg['visibility'][3]
        elif visibility < 1000:
            return cfg['visibility'][4]
        elif visibility < 2000:
            return cfg['visibility'][5]
        elif visibility < 4000:
            return cfg['visibility'][6]
        else:
            return cfg['visibility'][7]

    #-----------------------------------
    def _precipitation2str(self, precipitation, text=True):
        if precipitation == 0:
            cat = 0
        elif precipitation < 2.5:
            cat = 1
        elif precipitation < 10:
            cat = 2
        elif precipitation < 25:
            cat = 3
        elif precipitation < 50:
            cat = 4
        else:
            cat = 5

        if text:
            return cfg['precipitation'][cat]
        else:
            return cat

    #-----------------------------------
    def _read_from_hourly_item(self, item):
        data = {}
 
        data['dt'] = item.get('dt')
        dt = datetime.fromtimestamp(data['dt'])
        data['dt_txt'] = datetime.strftime(dt, '%d.%m.%Y %H:00')        
        data['temp'] = item.get('temp')
        data['feels_like'] = item.get('feels_like')
        data['dew_point'] = item.get('dew_point')
        data['pressure'] = item.get('pressure')
        data['humidity'] = item.get('humidity')
        data['wind_speed_kmh'] = '{:.0f}'.format(item.get('wind_speed', 0) * 3.6)
        data['wind_direction'] = self._degree2str(item.get('wind_deg', '-'))
        data['wind_gust_kmh'] = '{:.0f}'.format(item.get('wind_gust', 0) * 3.6)
        data['visibility'] = item.get('visibility')
        data['visibility_txt'] = self._visibility2str(item.get('visibility', 10000)) 
        data['clouds_perc'] = item.get('clouds')
        data['clouds_txt'] = self._clouds2str(item.get('clouds', 0))
        data['pop_perc'] = '{:.0f}'.format(item.get('pop', 0) *100)
        if item.get('weather'):
            data['weather_id'] = item['weather'][0].get('id', '-')
            data['main_txt'] = item['weather'][0].get('main', '-')
            data['description'] = item['weather'][0].get('description', '-')
            data['icon'] = item['weather'][0].get('icon', '-') + '.png'

        return data    

    #-----------------------------------
    def _read_from_daily_item(self, item):
        data = {}
        data['dt'] = item.get('dt')
        dt = datetime.fromtimestamp(data['dt'])
        data['dt_txt'] = datetime.strftime(dt, '%d.%m.%Y')        
        data['sunrise'] = item.get('sunrise')
        data['sunrise_txt'] = datetime.strftime( datetime.fromtimestamp(item.get('sunrise')), '%H:%M' )
        data['sunset'] = item.get('sunset')
        data['sunset_txt'] = datetime.strftime( datetime.fromtimestamp(item.get('sunset')), '%H:%M' )
        data['moonrise'] = item.get('moonrise')
        data['moonrise_txt'] = datetime.strftime( datetime.fromtimestamp(item.get('moonrise')), '%H:%M' )
        data['moonset'] = item.get('moonset')
        data['moonset_txt'] = datetime.strftime( datetime.fromtimestamp(item.get('moonset')), '%H:%M' )
        data['moonphase'] = self._moon2str(item.get('moon_phase')) 
        data['uv_index'] = item.get('uvi')
        data['uv_index_txt'] = self._uvi2str(item.get('uvi', '-'))
        data['summary'] = item.get('summary')
        if item.get("temp"):
            data['temp_morning'] = item['temp'].get('morn')
            data['temp_day'] = item['temp'].get('day')
            data['temp_evening'] = item['temp'].get('eve')
            data['temp_min'] = item['temp'].get('min')
            data['temp_max'] = item['temp'].get('max')

        data['dew_point'] = item.get('dew_point')        
        data['pressure'] = item.get('pressure')
        data['humidity'] = item.get('humidity')
        data['wind_speed_kmh'] = '{:.0f}'.format(item.get('wind_speed', 0) * 3.6)
        data['wind_direction'] = self._degree2str(item.get('wind_deg', '-'))
        data['wind_gust_kmh'] = '{:.0f}'.format(item.get('wind_gust', 0) * 3.6)
        data['visibility'] = item.get('visibility')
        data['visibility_txt'] = self._visibility2str(item.get('visibility', 10000)) 
        data['clouds_perc'] = item.get('clouds')
        data['clouds_txt'] = self._clouds2str(item.get('clouds', 0))
        data['pop_perc'] = '{:.0f}'.format(item.get('pop', 0) *100)
        if item.get('weather'):
            data['weather_id'] = item['weather'][0].get('id', '-')
            data['main_txt'] = item['weather'][0].get('main', '-')
            data['description'] = item['weather'][0].get('description', '-')
            data['icon'] = item['weather'][0].get('icon', '-') + '.png'

        return data    

    #-----------------------------------
    def _prettify_weather(self, location):
        weather = self.weather.get(location)
        if weather:
            w_dict = {}
            w_dict['base'] = {}
            w_dict['now'] = {}
            w_dict['hourly'] = []
            w_dict['daytime'] = []
            w_dict['daily'] = []
            w_dict['alerts'] = []

            # base data
            w_dict['base']['location'] = weather['location']
            w_dict['base']['lat'] = weather['lat']
            w_dict['base']['lon'] = weather['lon']
            w_dict['base']['timezone'] = weather['timezone']
            w_dict['base']['timezone_offset'] = weather['timezone_offset']
            w_dict['base']['dt'] = weather['last_refresh'].timestamp()
            w_dict['base']['dt_txt'] = datetime.strftime(weather['last_refresh'], '%d.%m.%Y %H:%M:%S')
 
            try:  
                # current weather
                w_current = weather.get('current')
                if w_current:
                    precipitation = False
                    data = self._read_from_hourly_item(w_current)
                    w_dict['now'].update(data)

                    w_dict['now']['dt'] = w_current.get('dt')
                    dt = datetime.fromtimestamp(w_current.get('dt'))
                    w_dict['now']['dt_txt'] = datetime.strftime(dt, '%d.%m.%Y %H:%M:%S')        
                    w_dict['now']['sunrise'] = w_current.get('sunrise')
                    w_dict['now']['sunrise_txt'] = datetime.strftime( datetime.fromtimestamp(w_current.get('sunrise')), '%H:%M' )
                    w_dict['now']['sunset'] = w_current.get('sunset')
                    w_dict['now']['sunset_txt'] = datetime.strftime( datetime.fromtimestamp(w_current.get('sunset')), '%H:%M' )
                    w_dict['now']['uv_index'] = w_current.get('uvi')
                    w_dict['now']['uv_index_txt'] = self._uvi2str(w_current.get('uvi', '-'))
                    if w_current.get('rain'):
                        w_dict['now']['rain'] = w_current['rain']['1h']
                        w_dict['now']['rain_txt'] = self._precipitation2str(w_current['rain']['1h'])
                        precipitation = True        
                    if w_current.get('snow'):
                        w_dict['now']['snow'] = w_current['snow']['1h']
                        w_dict['now']['snow_txt'] = self._precipitation2str(w_current['snow']['1h'])
                        precipitation = True       

                    # minutely precipitation data
                    if weather.get('minutely'): 
                        prec_start_t = None
                        prec_stop_t = None
                        prec_array = []
                        for item in weather.get('minutely'):
                            prec_array.append(self._precipitation2str(item.get('precipitation', 0), text=False))
                            if precipitation and item.get('precipitation') == 0:
                                prec_stop_t = datetime.fromtimestamp(item.get('dt'))
                                prec_msg = cfg['prec_forecast']['prec_ends'].format(prec_stop_t.strftime('%H:%M')) 
                            elif not precipitation and item.get('precipitation') > 0:
                                prec_start_t = datetime.fromtimestamp(item.get('dt'))
                                prec_msg = cfg['prec_forecast']['prec_starts'].format(prec_start_t.strftime('%H:%M')) 
                        if precipitation and not prec_stop_t:
                            prec_msg = cfg['prec_forecast']['prec_cont']
                        if not precipitation and not prec_start_t:
                            prec_msg = cfg['prec_forecast']['prec_no']
                        w_dict['now']['precipitation_txt'] = prec_msg    
                        w_dict['now']['precipitation'] = prec_array

                # hourly forecast data
                w_hourly = weather.get('hourly')
                if w_hourly:
                    for item in w_hourly:
                        data = self._read_from_hourly_item(item)
                        w_dict['hourly'].append(data)

                        dt = datetime.fromtimestamp(data['dt'])
                        if dt.hour in (7,10,13,16,19,23):
                            data['dt_txt'] = cfg['daytime'][dt.hour]
                            w_dict['daytime'].append(data)

                # daily forecast data
                w_daily = weather.get('daily')
                if w_daily:
                    for item in w_daily:
                        data = self._read_from_daily_item(item)
                        w_dict['daily'].append(data)

                # alerts
                w_alerts = weather.get('alerts')
                if w_alerts:
                    for item in w_alerts:
                        data = {}
                        data['sender_name'] = item.get('sender_name')
                        data['event'] = item.get('event')
                        data['start'] = item.get('start')
                        data['start_txt'] = datetime.strftime( datetime.fromtimestamp(item.get('start')), '%d.%m.%Y %H:%M' )
                        data['end'] = item.get('end')
                        data['end_txt'] = datetime.strftime( datetime.fromtimestamp(item.get('end')), '%d.%m.%Y %H:%M' )
                        data['description'] = item.get('description')
                        w_dict['alerts'].append(data)

            except Exception as e:
                logging.error( "Error while normalizing weather data: Exception {:s}".format(str(e)) )
            return w_dict        

