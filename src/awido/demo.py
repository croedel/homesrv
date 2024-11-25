"""
awidoAPI demo code
(c) 2024 by Christian Rödel 
"""

import logging
from awidoAPI import awidoAPI

def main():
    logging.basicConfig( level=logging.DEBUG, format="%(asctime)s : %(levelname)s : %(message)s" )

    awido = awidoAPI()
#    region = "ffb"
#    oid = "539b263d-88a4-a375-1b17-ce7b1f162aaa"
#    awido.set_location(region, oid)

    print("All:")
    all = awido.all_collections()
    for item in all:
       site = "-> " + item.get("site") if item.get("site") else ""
       print( "  - {}: {} {}".format(item["date"], item["waste_type"], site) )   

    print("Upcoming:")
    upcoming = awido.upcoming_collections()
    for item in upcoming:
       site = "-> " + item.get("site") if item.get("site") else ""
       print( "  - {}: {} {}".format(item["date"], item["waste_type"], site) )   

    print("Current:")
    current = awido.current_collections()
    for item in current:
       site = "-> " + item.get("site") if item.get("site") else ""
       print( "  - {}: {} {}".format(item["date"], item["waste_type"], site) )   

#---------------------------------------------------
if __name__ == '__main__':
  main()