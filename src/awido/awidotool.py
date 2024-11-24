#!/usr/bin/env python3
"""
command line tool for awidoAPI. Demonstrates API usage
(c) 2024 by Christian Rödel 
"""

import logging
#FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
FORMAT = '[%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

from awidoAPI import awidoAPI

#-----------------------------------
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


#================================================
def main(): 
    api = awidoAPI()

    while True:
        print( "=====================================" )
        print( "Menu:")
        print( "  1: Find your OID" )
        print( "  x: Exit" )

        opt = input("Please select: ")
        if opt == "1": 
            interactive_oid_selection(api)
        elif opt == "x" or opt == "X":  
            break
    
    print( "Bye!")
 
#---------------------------------------------------
if __name__ == '__main__':
  main()
