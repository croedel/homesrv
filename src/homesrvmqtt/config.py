#!/usr/bin/env python3
"""
read config.yaml file
(c) 2024 by Christian Rödel 
"""

import os
import sys
import yaml
import logging

#----------------------------------------
# Create new config file
def create_config_file():
    logging.debug("Creating config file")

    # Read template 
    try:
        BASE_DIR = os.path.dirname(__file__) # Base installation directory
        templ_fname = os.path.join(BASE_DIR, "config-template.yaml")
        with open(templ_fname, "r") as file: 
            data = file.read()   
    except Exception as ex:
        print("ERROR - Couldn't read 'config-template.yaml': {}".format(ex))
        return False

    # Write customized config
    cfg_path = os.environ.get('XDG_CONFIG_HOME') or os.environ.get('APPDATA')
    if cfg_path: # Usually something like ~/.config/homesrv_mqtt/config.yaml resp. 'C:\\Users\\xxxx\\AppData\\Roaming'
        cfg_fname = os.path.join(cfg_path, "homesrv_mqtt", "config.yaml")  
    else:
        cfg_fname = os.path.join(os.path.expanduser("~"), ".config", "homesrv_mqtt", "config.yaml")  # ~/.config/homesrv_mqtt/config.yaml

    try:
        os.makedirs(os.path.dirname(cfg_fname), exist_ok=True)
        with open(cfg_fname, "w") as file: 
            file.write(data) 
    except Exception as ex:
        logging.error("ERROR - Couldn't write {}: {}".format(cfg_fname, ex))
        return False

    logging.info("Successfully created {}".format(cfg_fname))
    return True

#-----------------------------------
# Read configuration from YAML file
def read_config():
  # Look in different locations for config.yaml file
  conf_files = []
  conf_files.append(os.path.join(os.getcwd(), "config.yaml"))  # CWD/config.yaml
  cfg_path = os.environ.get('XDG_CONFIG_HOME') or os.environ.get('APPDATA')
  if cfg_path: # Usually something like ~/.config/homesrv_mqtt/config.yaml resp. 'C:\\Users\\xxxx\\AppData\\Roaming'
    conf_files.append(os.path.join(cfg_path, "homesrv_mqtt", "config.yaml"))  
  else:
    conf_files.append(os.path.join(os.path.expanduser("~"), ".config", "homesrv_mqtt", "config.yaml"))  # ~/.config/homesrv_mqtt/config.yaml
  
  cfg = False
  for fname_conf in conf_files:
    try:
      with open(fname_conf, 'r', encoding='utf-8') as f_conf:
        cfg = yaml.safe_load(f_conf)
        logging.info("Using config YAML file: {}".format(fname_conf) )      
        break
    except IOError as err:
      logging.debug("Couldn't open config YAML file: {}".format(str(err)) )
    except yaml.YAMLError as err:
      logging.debug("Couldn't read config YAML file {}: {}".format(fname_conf, str(err)) )
  return cfg  

#-----------------------------------
logging.basicConfig( level=logging.INFO, format="[%(levelname)s] %(filename)s: %(message)s" )
cfg = read_config()
if not cfg:
  logging.info("No config.yaml found - creating new one from template.")
  if create_config_file():  # Create a new config
    cfg = read_config()
    if not cfg:
      logging.fatal("Couldn't open fresh created config YAML file")
      sys.exit(1)
    else:
      logging.warning("Please edit and adapt freshly created config.yaml. Restart afterwards.")
      sys.exit(0)      
  else:
    logging.fatal("Couldn't create config YAML file from templare")
    sys.exit(1)


#--------------------------------------
# Test code only
if __name__ == "__main__":
    print()