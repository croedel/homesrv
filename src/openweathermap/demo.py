"""
openweathermapAPI demo code
(c) 2024 by Christian Rödel 
"""

from homesrvmqtt.config import cfg
from openweathermap.openweathermapAPI import openweathermapAPI

def main():
    api = openweathermapAPI()
#    api.clear_locations()

    location = api.add_location_by_name(city="Lillehammer")
#    location = api.add_location_by_name(city="Tergowisch")
#    location = api.add_location_by_name(city="Germering", country="DE")
    print( api.print_locations() )

    api.refresh()


    for location in api.get_locations():
        wdata = api.get_weather(location)
 
        base = wdata.get("base")
        print( "* {}: Base".format(location) )
        if base:
            for tag, val in base.items():
                print( " - " + tag + ": " + str(val) )
        print()

        now = wdata.get("now")
        print( "* {}: Now".format(location) )
        if now:
            for tag, val in now.items():
                print( " - " + tag + ": " + str(val) )
        print()

        forecast = wdata.get("hourly")
        print( "* {}: Forecast hourly".format(location) )
        if forecast:
            for item in forecast:
                for tag, val in item.items():
                    print( " - " + tag + ": " + str(val) )
                print()  

        forecast = wdata.get("daytime")
        print( "* {}: Forecast daytime".format(location) )
        if forecast:
            for item in forecast:
                for tag, val in item.items():
                    print( " - " + tag + ": " + str(val) )
                print()  

        forecast = wdata.get("daily")
        print( "* {}: Forecast daily".format(location) )
        if forecast:
            for item in forecast:
                for tag, val in item.items():
                    print( " - " + tag + ": " + str(val) )
                print()  

#---------------------------------------------------
if __name__ == '__main__':
    main()