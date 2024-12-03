""" 
Retrieve NINA warnings 
"""

import requests
import logging
from homesrvmqtt.config import cfg

#================================================
class ninaAPI:
    nina_base_url = "https://nina.api.proxy.bund.dev/api31"    
    ars_url = "https://www.xrepository.de/api/xrepository/urn:de:bund:destatis:bevoelkerungsstatistik:schluessel:rs_2021-07-31/download/Regionalschl_ssel_2021-07-31.json"

    #---------------------------
    def __init__(self): 
        self.ars = cfg.get("nina_ars")
        self.location = cfg.get("nina_location")
        if self.location and not self.ars:
            self.set_location(self.location)

    #-----------------------------------
    def set_location(self, name):
        self.ars = None
        self.location = None
        ars_list = self._do_API_call( self.ars_url )
        if ars_list:
            for line in ars_list["daten"]:
                if name in line[1]:
                    self.ars = line[0]
                    self.location = line[1]
            if not self.ars:
                logging.error("Can't find location: {}".format(name))
                        
    #-----------------------------------
    # get data from NINA API
    def get_warnings(self):
        if not self.ars or len(self.ars) != 12:
            logging.error("Can't retrieve NINA data: Invalid ARS {}".format(self.ars))
            return None

        warning_data = []
        logging.debug("Retrieve NINA info for ARS {}".format(self.ars))
    
        # get dashboard data
        ars_district = self.ars[:5] + "0000000" # Data is available on "Kreisebene" only -> replace last 7 digits with 0
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
                
                warning_data.append(item)
                    
        return warning_data      
    
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
