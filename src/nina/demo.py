"""
ninaAPI demo code
(c) 2024 by Christian Rödel 
"""

import logging
from nina.ninaAPI import ninaAPI

def main():
   logging.basicConfig( level=logging.DEBUG, format="%(asctime)s : %(levelname)s : %(message)s" )
   api = ninaAPI()
#   api.set_location("Oberschleißheim")
   warnings = api.get_warnings()
   print( "Warnings for ARS {}: {} ".format(api.ars, api.location) )
   if warnings:
      for item in warnings:
         print( "---" )
         print( "{} - {}".format(item["type"], item["severity"]) ) 
         print( "{} ({})".format(item["headline"], item["msgType"]) ) 
         print( "{}".format(item["description"]) )
   else:
      print( "All GREEN - No warnings for your region." )

#---------------------------------------------------
if __name__ == '__main__':
  main()