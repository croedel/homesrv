""" 
Retrieve NINA warnings 
"""

import requests
import logging
from homesrv.config import cfg

#================================================
class ninaAPI:
    nina_base_url = "https://nina.api.proxy.bund.dev/api31"    
    ars_url = "https://www.xrepository.de/api/xrepository/urn:de:bund:destatis:bevoelkerungsstatistik:schluessel:rs_2021-07-31/download/Regionalschl_ssel_2021-07-31.json"

    #---------------------------
    def __init__(self):
        self.locations=[] 
        self._refresh_ars_list()
        self._init_locations()
        
    #-----------------------------------
    def search_location(self, name):
        list = []
        for line in self.ars_list:
            if name in line[1]:
                item = {}
                item["ars"] = line[0]
                item["location"] = line[1]
                list.append(item)
        return list    

    #-----------------------------------
    def add_location(self, ars):
        item = None
        for line in self.ars_list:
            if ars == line[0]:
                item = {}
                item["ars"] = line[0]
                item["location"] = line[1]
                self.locations.append(item)
        if not item:
            logging.error("Can't find location ars {}".format(ars))
                        
    #-----------------------------------
    # get data from NINA API
    def get_warnings(self, ars):
        data = None
        # lookup ars
        for item in self.locations:
            if item["ars"] == ars:
                logging.info("Retrieve NINA info for ARS {}, {}".format(item["ars"], item["location"]))
                data = {}
                data["location"] = item["location"]
                data["ars"] = item["ars"]
                data["warnings"] = []
                break

        if data:        
            # get dashboard data
            ars_district = data["ars"][:5] + "0000000" # Data is available on "Kreisebene" only -> replace last 7 digits with 0
            url = self.nina_base_url + "/dashboard/" + ars_district + ".json"
            warnings = self._do_API_call( url )
            
            if warnings:
                for warning in warnings:
                    item = {}
                    item["type"] = warning["payload"]["type"]
                    item["severity"] = warning["payload"]["data"]["severity"]
                    item["msgType"] = warning["payload"]["data"]["msgType"]

                    # get details for the warning id
                    id = warning["payload"]["id"]
                    url = self.nina_base_url + "/warnings/" + id + ".json"
                    warning_details = self._do_API_call( url )            
                    if warning_details:
                        item["headline"] = warning_details["info"][0]["headline"]
                        item["description"] = warning_details["info"][0]["description"]
                    
                    data["warnings"].append(item)                       
        return data      
    
    #-----------------------------------
    def _refresh_ars_list(self):
        ars_list = self._do_API_call( self.ars_url )
        if ars_list:
            self.ars_list = ars_list.get("daten") 
        else:    
            logging.error("Can't retrieve ars list")

    #---------------------------
    def _init_locations(self):
        cfg_locations = cfg.get("nina_locations")
        if cfg_locations and len(cfg_locations)>0:
            for _, ars in cfg_locations.items():
                self.add_location(ars=ars)        

    #---------------------------
    def _do_API_call(self, url):
        try:
            response = requests.get( url, timeout=3 )
        except requests.exceptions.RequestException as err:
            logging.error( "Couldn't request NINA API: {} Exception {:s}".format(url, str(err)) )
        else:
            if response.status_code == 200:
                return response.json()
            else:
                logging.error( "Error while requesting NINA API: {:s} -> {:d} {:s}".format( url, response.status_code, response.reason) )

#===============================================================
# Some test and demo code
#-------------------------------
def main(): 
    api = ninaAPI()

    print("Find location")
    locations = api.search_location("München")
    for item in locations:
        print("- {}: {}".format(item["location"], item["ars"]))

    api.add_location("091620000000")

    print("Get warnings for all locations")
    for location in api.locations:
        data = api.get_warnings(ars=location["ars"])     
        print( data )   


#---------------------------------------------------
if __name__ == '__main__':
  main()