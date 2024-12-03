#!/usr/bin/env python3
"""
command line tool for homesrv
(c) 2024 by Christian Rödel 
"""

from awido.awidoAPI import awidoAPI
from openweathermap.openweathermapAPI import openweathermapAPI
from DButils.DBtimetableAPI import DBtimetableAPI
from nina.ninaAPI import ninaAPI

#-----------------------------------
# AWIDO
def interactive_oid_selection(api: awidoAPI):
    region = input("Enter your region code [e.g. ffb]: ")

    places = api.retrieve_places(region)
    for k, _ in places.items():
        print( "  - {}".format(k) )
    place = input("Enter your place: ")
    if not places.get(place):
        print( "ERROR - Invalid place" )
        return False
    
    streets = api.retrieve_streets(region, places.get(place))
    for k, _ in streets.items():
        print( "  - {}".format(k) )
    street = input("Enter your street: ")
    if not streets.get(street):
        print( "ERROR - Invalid street" )
        return False

    street_parts = api.retrieve_street_parts(region, streets.get(street))
    if len(street_parts) > 1:    
        for k, _ in street_parts.items():
            print( "  - {}".format(k) )
        street_part = input("Enter your street part: ")
        if not street_parts.get(street_part):
            print( "ERROR - Invalid street part" )
            return False
        oid = street_parts[street_part]   
    else:
        oid = street_parts[""]

    print( "Your OID: {}".format(oid) )    
    return oid

#-------------------------------
# Deutsche Bahn
def search_dbstation(api: DBtimetableAPI):
    station_name = input("DB station name you want to search: ")
    stations = api.search_stations_by_name(station_name)
    print("Name: Id")
    for name, id in stations:
        print("{}: {}".format(name, id))

#--------------------------------
# openweathermap
def search_location(api: openweathermapAPI):
    location = input("location name you want to search: ")
    data = api.search_location(location)
    if data:
        for item in data:
            print("{}, {} ({}): lat {}, lon {}".format( item["name"], item["country"], item["state"], item["lat"], item["lon"]) )
    else:
        print("Couldn't find location")    


#================================================
def main(): 
    awido_api = awidoAPI()
    db_api = DBtimetableAPI()
    weather_api = openweathermapAPI()

    while True:
        print( "=====================================" )
        print( "Menu:")
        print( "  1: AWIDO: Find your OID" )
        print( "  2: Deutsche Bahn: Find stations and station_id's" )
        print( "  3: Openweathermap: Find geo location" )
        print( "  x: Exit" )

        opt = input("Please select: ")
        if opt == "1": 
            interactive_oid_selection(awido_api)
        elif opt == "2": 
            search_dbstation(db_api)
        elif opt == "3": 
            search_location(weather_api)
        elif opt == "x" or opt == "X":  
            break
    
    print( "Bye!")
 
#---------------------------------------------------
if __name__ == '__main__':
  main()
