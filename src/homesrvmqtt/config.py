#!/usr/bin/env python3
"""
read config.yaml file
(c) 2024 by Christian Rödel 
"""

import os
import yaml
import logging

#-----------------------------------
# Read configuration from YAML file
def read_config():
  # Look in different locations for config.yaml file
  conf_files = []
  conf_files.append(os.path.join(os.getcwd(), "config.yaml"))  # CWD/config.yaml
  cfg_path = os.environ.get('XDG_CONFIG_HOME') or os.environ.get('APPDATA')
  if cfg_path: # Usually something like ~/.config/mtecmqtt/config.yaml resp. 'C:\\Users\\xxxx\\AppData\\Roaming'
    conf_files.append(os.path.join(cfg_path, "mtecmqtt", "config.yaml"))  
  else:
    conf_files.append(os.path.join(os.path.expanduser("~"), ".config", "mtecmqtt", "config.yaml"))  # ~/.config/mtecmqtt/config.yaml
  
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

#--------------------------------------
# Test code only
if __name__ == "__main__":
    logging.info( "Config: {}".format( str(cfg)) )