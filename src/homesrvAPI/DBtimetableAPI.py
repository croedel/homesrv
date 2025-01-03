#!/usr/bin/env python3
"""
DBtimetableAPI main class
(c) 2024 by Christian Rödel 
"""

import logging
#FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
FORMAT = '[%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

import requests
import xmltodict
from homesrv.config import cfg
from homesrvAPI.DBtimetableHelpers import DBtimetable, DBtrain_stop
from datetime import datetime, timedelta


#===============================================================
# Main API class
class DBtimetableAPI:
    #---------------------------
    def __init__(self):
        self.station_map = None
        self.station_map_date = None
        self.dbstations = []
        self.headers = {
            "DB-Api-Key": cfg.get("DB_client_secret"),
            "DB-Client-Id": cfg.get("DB_client_id"),
            "accept": "application/xml"
        }
        self._init_stations()
        
    #---------------------------
    def search_stations_by_name(self, substring):
        self._refresh_station_map()
        stations = []
        for eva, name in self.station_map.items():
            if substring in name:
                stations.append( [name, eva] )
        return stations    

    #---------------------------
    def get_dbstations(self):
        return self.dbstations

    #---------------------------
    def _init_stations(self):
        cfg_stations = cfg.get("DB_stations")
        if cfg_stations and len(cfg_stations)>0:
            for name, id in cfg_stations.items():
                dbstation = self._get_station_by_id(id)
                if dbstation:
                    self.dbstations.append(dbstation)    

    #---------------------------
    def _get_station_by_id(self, station_id):
        self._refresh_station_map()
        station_name = self.station_map.get(str(station_id))
        if station_name:    
            return DBstation(station_id=station_id, station_name=station_name)
        else:
            logging.error( "Unknown station_id {}".format(station_id) )
            
    #---------------------------
    def _refresh_station_map(self):
        dt_now = datetime.now() 
        if not self.station_map_date or self.station_map_date < dt_now-timedelta(hours=24): 
            logging.info( "Refreshing station list from API. This will take a few seconds..." )
            self.station_map = {}
            json = self._do_API_call( "station/*" )
            if json and json.get("stations"):
                for item in json["stations"]["station"]:
                    name = item["@name"]
                    eva = item["@eva"]
                    self.station_map[eva] = name
                self.station_map_date = dt_now
            else:
                logging.error( "Error while refreshing station list!" )

    #---------------------------
    def _do_API_call(self, path):
        try:
            url = cfg["DB_timetable_base_url"] + path
            response = requests.get( url, headers=self.headers, timeout=10 )

        except requests.exceptions.RequestException as err:
            logging.error( "Couldn't request DB API: {} Exception {:s}".format(url, str(err)) )
        else:
            if response.status_code == 200:
                response_json = xmltodict.parse(response.text)
                return response_json
            else:
                logging.error( "Error while requesting DB API: {:s} -> {:d} {:s}".format( url, response.status_code, response.reason) )
        return None  


#===============================================================
# Representation of a station and the related, cached train schedules
class DBstation:
    #---------------------------
    def __init__(self, station_id=None, station_name=None):
        self.station_id = station_id
        self.station_name = station_name
        self.schedule = []  # data from original schedule
        self.changes = []   # data from last change-info
        self.consolidated = []  # consolidated data
        self.schedule_date = None
        self.schedule_refresh_date = None
        self.change_refresh_date = None

    #---------------------------
    def refresh(self, api: DBtimetableAPI, dt: datetime=None):
        dt_now = datetime.now() 
        if not dt:
            dt = dt_now.replace(second=0, microsecond=0, minute=0) # round to hour

        if dt != self.schedule_date: # refresh requested for a different date than previously -> force a refresh
            self.schedule_refresh_date = None
            self.change_refresh_date = None
            self.schedule_date = dt   

        # refresh main schedule
        if not self.schedule_refresh_date or self.schedule_refresh_date < dt_now-timedelta(seconds=cfg["DB_refresh_schedule"]):     
            logging.info( "Refreshing schedule for station_id {}".format(self.station_id) )
            self.schedule.clear()      
            self._get_schedule(api, dt=dt)
            self._get_schedule(api, dt=dt+timedelta(hours=1))
            self.schedule_refresh_date = dt_now
            self.change_refresh_date = None # force refresh of changes to avoid
        # refresh changes
        if not self.change_refresh_date or self.change_refresh_date < dt_now-timedelta(seconds=cfg["DB_refresh_changes"]): 
            logging.info( "Refreshing changes for station_id {}".format(self.station_id) )
            self.changes.clear()      
            self._get_changes(api)
            self._apply_changes()

    #---------------------------
    def get_timetable(self, tt_type="departure", dt: datetime=None):
        now = datetime.now()
        timetable = DBtimetable(tt_type=tt_type)
        for schedule_item in self.consolidated:
            item = None        
            if tt_type == "arrival":
                item = schedule_item.get_arrival()
            elif tt_type == "departure":   
                if schedule_item.departure.get("time") and datetime.strptime(schedule_item.departure["time"], "%d.%m.%Y %H:%M") >= now-timedelta(minutes=1):
                    item = schedule_item.get_departure()
            if item:
                timetable.append(item)    
        timetable.sort()        
        return timetable

    #---------------------------
    def print(self):
        txt = ""
        for schedule_item in self.consolidated:
            line = schedule_item.print()
            if line:
                txt += "---\n"    
                txt += line 
        return txt        

    #---------------------------
    def print_changes(self):
        txt = ""
        for schedule_item in self.changes:
            line = schedule_item.print()
            if line:
                txt += "---\n"    
                txt += line 
        return txt        

    #---------------------------
    def _search_schedules(self, train_id):
        schedules = []
        for item in self.schedule:
            if item.base["train_id"] == train_id:
                schedules.append(item)
        return schedules

    #---------------------------
    def _search_changes(self, train_id):
        schedules = []
        for item in self.changes:
            if item.base["train_id"] == train_id:
                schedules.append(item)
        return schedules

    #---------------------------
    def _get_schedule(self, api: DBtimetableAPI, dt: datetime=None):
        if not dt:
            dt = datetime.now() 
        logging.debug( "Fetching train stops for station_id {}, {}".format( self.station_id, dt.strftime("%d.%m.%Y %H:00")) )

        url = "plan/{}/{}/{}".format(self.station_id, dt.strftime("%y%m%d"), dt.strftime("%H"))
        json = api._do_API_call( url )
        if json and json.get("timetable"):
            timetable = json.get("timetable")
            self.station_name = timetable.get("@station")

            # iterate over all trains in timetable    
            for item in timetable["s"]: 
                train = DBtrain_stop()
                train.base["train_id"] = item.get("@id")
                if item.get("tl"):               
                    train.base["category"] = item["tl"].get("@c")   
                    train.base["flags"] = item["tl"].get("@f")  
                    train.base["train_no"] = item["tl"].get("@n")  
                    train.base["owner"] = item["tl"].get("@o")  
                    train.base["trip_type"] = item["tl"].get("@t")  

                if item.get("ar"):               
                    train.arrival["time"] = datetime.strptime(item["ar"].get("@pt"), "%y%m%d%H%M").strftime("%d.%m.%Y %H:%M")
                    train.arrival["platform"] = item["ar"].get("@pp")
                    train.arrival["line"] = item["ar"].get("@l")
                    train.arrival["path"] = item["ar"].get("@ppth")
                    if "|" in train.arrival["path"]:
                        train.arrival["from"] = train.arrival["path"].split("|")[0]
                    else:
                        train.arrival["from"] = train.arrival["path"]

                if item.get("dp"):               
                    train.departure["time"] = datetime.strptime(item["dp"].get("@pt"), "%y%m%d%H%M").strftime("%d.%m.%Y %H:%M")
                    train.departure["platform"] = item["dp"].get("@pp")
                    train.departure["line"] = item["dp"].get("@l")
                    train.departure["path"] = item["dp"].get("@ppth")
                    if "|" in train.departure["path"]:
                        train.departure["to"] = train.departure["path"].rsplit("|",1)[1]
                    else:
                        train.departure["to"] = train.departure["path"]
                self.schedule.append(train)
        else:
            logging.error( "No train stops found for station_id {}, {}".format( self.station_id, dt.strftime("%d.%m.%Y %H:00")) )


    #---------------------------
    def _get_changes(self, api: DBtimetableAPI):
        logging.debug( "Fetching train stop changes for station_id {}".format(self.station_id) )

        url = "fchg/{}".format(self.station_id)
        json = api._do_API_call( url )
        timetable = json["timetable"]

        if timetable:
            # iterate over all trains in timetable    
            for item in timetable["s"]: 
                train = DBtrain_stop()
                train.base["train_id"] = item.get("@id")

                if item.get("ar"):     
                    if item["ar"].get("@ct"):
                        train.arrival["changed_time"] = datetime.strptime(item["ar"].get("@ct"), "%y%m%d%H%M").strftime("%d.%m.%Y %H:%M")          
                    train.arrival["change_status"] = item["ar"].get("@cs")
                    train.arrival["changed_platform"] = item["ar"].get("@cp")
                    train.arrival["changed_path"] = item["ar"].get("@cpth")
                    if train.arrival["changed_path"]:
                        if "|" in train.arrival["changed_path"]:
                            train.arrival["changed_from"] = train.arrival["changed_path"].split("|")[0]
                        else:
                            train.arrival["changed_from"] = train.arrival["changed_path"]

                if item.get("dp"):
                    if item["dp"].get("@ct"):
                        train.departure["changed_time"] = datetime.strptime(item["dp"].get("@ct"), "%y%m%d%H%M").strftime("%d.%m.%Y %H:%M")          
                    train.departure["change_status"] = item["dp"].get("@cs")
                    train.departure["changed_platform"] = item["dp"].get("@cp")
                    train.departure["changed_path"] = item["dp"].get("@cpth")
                    if train.departure["changed_path"]:
                        if "|" in train.departure["changed_path"]:
                            train.departure["changed_to"] = train.departure["changed_path"].rsplit("|",1)[1]
                        else:
                            train.departure["changed_to"] = train.departure["changed_path"]

                if item.get("m"):
                    # can be a single onject or a list of objects
                    if isinstance(item["m"], list):
                        msg = item["m"]
                    else:    
                        msg = [item["m"]] # wrap into a list                        
                    for i in msg:
                        message = {}       
                        message["type"] = i.get("@t")
                        message["category"] = i.get("@cat") 
                        message["priority"] = i.get("@pr") 
                        train.messages.append(message)

                self.changes.append(train)
                

    #---------------------------
    def _apply_changes(self):
        self.consolidated = self.schedule.copy() # create a fresh copy of schedule
        for schedule_item in self.consolidated:
            for change_item in self._search_changes(schedule_item.base["train_id"]):
                for p, v in change_item.arrival.items():
                    sched_p = p.split('_')[1]
                    if schedule_item.arrival.get(sched_p) != v: # just set changed_* param, if value has changed    
                        schedule_item.arrival[p] = v     
                for p, v in change_item.departure.items():
                    sched_p = p.split('_')[1]
                    if schedule_item.departure.get(sched_p) != v: # just set changed_* param, if value has changed    
                        schedule_item.departure[p] = v     
                schedule_item.messages = change_item.messages.copy()


#===============================================================
# Some test and demo code
#-------------------------------
def main(): 
    api = DBtimetableAPI()

    # Search for a station by Name
    print("------------------------------------------")
    stations = api.search_stations_by_name("Pasing")
    for name, id in stations:
        print("- {}: {}".format(id, name))

    for station in api.get_dbstations():
        station.refresh(api, dt=None)
        timetable = station.get_timetable(tt_type="departure")
        timetable.sort("date")
        print("------------------------------------------")
        print("Timetable for {}: {}".format(station.station_name, station.station_id) )
        print("------------------------------------------")
        print( timetable.print() )

#        print( station.print() )

        timetable.filter_destination("Augsburg")
        print("------------------------------------------")
        print("Timetable for {}: {} to Augsburg".format(station.station_name, station.station_id) )
        print("------------------------------------------")
        print( timetable.print(path_filter="Augsburg") )

#---------------------------------------------------
if __name__ == '__main__':
  main()