""" 
Retrieve NINA warnings 
"""

import requests
import logging

#================================================
class ninaAPI:
  nina_base_url = "https://nina.api.proxy.bund.dev/api31"    
  ars_url = "https://www.xrepository.de/api/xrepository/urn:de:bund:destatis:bevoelkerungsstatistik:schluessel:rs_2021-07-31/download/Regionalschl_ssel_2021-07-31.json"

  #-----------------------------------
  # get data from NINA API
  def get_warnings(self, ars):
    if(len(ars) != 12):
      logging.error("Can't retrieve NINA data: Invalid ARS {}".format(ars))

    logging.debug("Retrieve NINA info for ARS {}".format(ars))
    
    # get dashboard data
    ars_district = ars[:5] + "0000000" # Data is available on "Kreisebene" only -> replace last 7 digits with 0
    url = self.nina_base_url + "/dashboard/" + ars_district + ".json"
    warnings = self._do_API_call( url )
    
    if warnings:
      warning_data = []
      # iterate over all warnings
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

  #-----------------------------------
  # get ars
  def get_ars(self, name):
    ars_list = self._do_API_call( self.ars_url )
    if ars_list:
      for line in ars_list["daten"]:
        if name in line[1]:
          return line[0], line[1]  # ars, city
    
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
    return None  
