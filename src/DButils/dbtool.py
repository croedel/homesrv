#!/usr/bin/env python3
"""
command line tool for DBtimetableAPI. Demonstrates API usage
(c) 2024 by Christian Rödel 
"""

import logging
#FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
FORMAT = '[%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

from datetime import datetime
from DButils.DBtimetableAPI import DBtimetableAPI
from DButils.DBdisruptionsAPI import DBdisruptionsAPI

#-------------------------------
def search_station(api: DBtimetableAPI ):
    station_name = input("Station name you want to search: ")
    stations = api.search_stations_by_name(station_name)
    for name, id in stations:
        print("- {}: {}".format(id, name))

#-------------------------------
def _ask_userinput():
    station_id = input("Station Id: ")
    val = input("For which Date and Time? [DD.MM.YY HH:00] (Default is 'now') ")
    dt = datetime.now()
    if len(val)==14:
        try:
            dt = datetime.strptime(val, "%d.%m.%y %H:%M")    
        except ValueError as e:
            print("Couldn't parse Date. Using 'now'")
            dt = datetime.now()

    val = input("(1) arrival or (2) departure? (default is 'departure') ")
    if val == "1":
        tt_type = "arrival"
    else:
        tt_type = "departure"
    return station_id, dt, tt_type

#-------------------------------
def get_station_timetables(api: DBtimetableAPI ):
    station_id, dt, tt_type = _ask_userinput()
    station = api.get_station_by_id(station_id)
    if station:
        station.refresh(api, dt=dt)
        timetable = station.get_timetable(tt_type=tt_type)
        timetable.sort("date")
        print("------------------------------------------")
        print("Timetable for {}: {} - {}".format(station.station_name, station.station_id, tt_type) )
        print("------------------------------------------")
        print( timetable.print() )
    else:
        print("Unknown StationId")

#-------------------------------
def get_train_timetables(api: DBtimetableAPI):
    station_id, dt, tt_type = _ask_userinput()
    train = input("Train you want to search for: ")

    station = api.get_station_by_id(station_id)
    if station:
        station.refresh(api, dt=dt)
        timetable = station.get_timetable(tt_type=tt_type)
        timetable.filter_train(train)
        timetable.sort("date")
   
        print("------------------------------------------")
        print("Timetable for {}: {} - {}".format(station.station_name, station.station_id, tt_type) )
        print("------------------------------------------")
        print( timetable.print() )
    else:
        print("Unknown StationId")

#-------------------------------
def get_destination_timetables(api: DBtimetableAPI):
    station_id, dt, tt_type = _ask_userinput()
    destination = input("Destination you want to search for: ")

    station = api.get_station_by_id(station_id)
    if station:
        station.refresh(api, dt=dt)
        timetable = station.get_timetable(tt_type=tt_type)
        timetable.filter_destination(destination)
        timetable.sort("date")

        print("------------------------------------------")
        print("Timetable for {}: {} - Destination {}".format(station.station_name, station.station_id, destination) )
        print("------------------------------------------")
        print( timetable.print(path_filter=destination) )

#-------------------------------
def get_disruptions(api: DBdisruptionsAPI):
    authors = input("Filter by author: (empty for none) ")
    states = input("Filter by states: [BY,RP,..] (empty for none) ")
    yn = input("With text? [y/N] ")    
    withtext = True if yn == "y" else False
    disruptions = api.get_disruptions(authors=authors, states=states)
    print( disruptions.print(withtext=withtext) )

#-------------------------------
def main(): 
    api = DBtimetableAPI()
    api_disruptions = DBdisruptionsAPI()

    while True:
        print( "=====================================" )
        print( "Menu:")
        print( "  1: Search for a station by name" )
        print( "  2: Get timetable for a station" )
        print( "  3: Get timetables for a station, filtered by train line(s)" )
        print( "  4: Get timetables for a station, filtered by a destination" )
        print( "  9: Get disruptions" )
        print( "  x: Exit" )
        opt = input("Please select: ")
        if opt == "1": 
            search_station(api)
        elif opt == "2": 
            get_station_timetables(api)
        elif opt == "3": 
            get_train_timetables(api)
        elif opt == "4": 
            get_destination_timetables(api)
        elif opt == "9": 
            get_disruptions(api_disruptions)
        elif opt == "x" or opt == "X":  
            break
    
    print( "Bye!")
 
#---------------------------------------------------
if __name__ == '__main__':
  main()
