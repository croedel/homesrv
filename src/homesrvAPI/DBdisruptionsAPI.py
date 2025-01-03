#!/usr/bin/env python3
"""
DBdisruptions main class
(c) 2024 by Christian Rödel 
"""

import logging
from homesrv.config import cfg
import requests
from datetime import datetime, timedelta


#===============================================================
# Main API class
class DBdisruptionsAPI:
    #---------------------------
    def __init__(self):
        self.disruptions = None
        self.disruptions_date = None

    #---------------------------
    def get_disruptions(self):
        disruptions = self._get_disruptions( authors=cfg["DB_disruptions_authors"], states=cfg["DB_disruptions_states"], withtxt=cfg["DB_disruptions_withtxt"] )
        return disruptions.disruptions
    
    #---------------------------
    def _get_disruptions(self, authors=None, states=None, withtxt=True):
        self._refresh_disruptions()
        disruptions = DBdisruptions()
        for item in self.disruptions:
            if item.get("cause") and item["cause"].get("category") in ("additional_service", "other_cause"):
                continue 
            if authors and item.get("author") not in authors:
                continue
            if states and item.get("states"):
                found = False
                for i in item["states"]:
                    if i in states:
                        found = True
                if not found:
                    continue
            if withtxt == False:
                if item.get("text"):
                    del item["text"]    
            disruptions.append(item)
        return disruptions
            
    #---------------------------
    def _refresh_disruptions(self):
        dt_now = datetime.now() 
        if not self.disruptions_date or self.disruptions_date < dt_now-timedelta(seconds=cfg["DB_refresh_disruptions"]): 
            json = self._do_API_call()
            if json and json.get("disruptions"):
                self.disruptions = json.get("disruptions")
                self.disruptions_date = dt_now

    #---------------------------
    def _do_API_call(self):
        try:
            url = cfg["DB_disruptions_base_url"]
            response = requests.get( url, timeout=10 )

        except requests.exceptions.RequestException as err:
            logging.error( "Couldn't request disruptions API: {} Exception {:s}".format(url, str(err)) )
        else:
            if response.status_code == 200:
                return response.json()
            else:
                logging.error( "Error while requesting disruptions API: {:s} -> {:d} {:s}".format( url, response.status_code, response.reason) )
        return None  

#===============================================================
# Helper class for returning a list of disruptions
class DBdisruptions:
    #---------------------------
    def __init__(self):
        self.disruptions = []

    #---------------------------
    def append(self, item):
        self.disruptions.append(item)

    #---------------------------
    def print(self, withtext=False):
        txt = ""
        for item in self.disruptions:
            txt += "---\n"
            lines = ""
            for line in item.get("lines"):
                lines += line.get("name") + ", " 
            lines = lines[:-2]        
            txt += "{}\n".format(lines)
            txt += "{}: {} - {}\n".format( item["cause"].get("label"), item.get("durationBegin"), item.get("durationEnd") ) 
            txt += "{}\n".format(item.get("headline")) 
            if withtext:
                txt += "{}\n".format(item.get("text")) 
        return txt


#===============================================================
# Some test and demo code
#-------------------------------
def main(): 
    api = DBdisruptionsAPI()

    disruptions = api.get_disruptions( authors="S_BAHN_MUC" )
#    disruptions = api.get_disruptions( states="BY" )
    print( disruptions.print(withtext=False) )

#---------------------------------------------------
if __name__ == '__main__':
  main()