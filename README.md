# homesrv MQTT

## Introduction
Welcome to the `homesrv_mqtt` project!

This project uses several public available REST services to retrieve data and writes them to your mqtt server.
Currently supported data sources:
- Awido waste collection
- Deutsche Bahn `Timetable API` and `Disruptions`
- Nina
- Openweathermap 

I hope you like it and it will help you with for your home automation project :-) !

### Disclaimer 
This project is a pure hobby project.
Usage is completely on you own risk. I don't take any responsibility on functionality or potential damage.


## Setup & configuration
### Prerequisites
The `homesrv_mqtt` project retrieves relevant data from different data sources, and writes them to a MQTT broker (https://mqtt.org/) of your choice. MQTT provides a light-weight publish/subscribe model which is widely used for Internet of Things messaging.  
That means, you obviously require a MQTT server. 
If you don't have one yet, you might want to try https://mosquitto.org/. 
You can easily install it like this:

```
sudo apt install mosquitto mosquitto-clients
```

### Installation

(1) Create a new directory for the installation (e.g. within your HOME directory)
```
mkdir homesrv_mqtt && cd homesrv_mqtt
```

(2) Create and activate a virtual python environment for the project
```
python -m venv . && source bin/activate
```

(3) Install the homesrv_mqtt project from github
```
pip install https://github.com/croedel/homesrv_mqtt/archive/refs/heads/main.zip
```

(4) Configure the project (please see following section for details)  

(5) As a next step, we can try to start `homesrv`. It will print out some debug info, so you can see what it does.
```
homesrv
```
You can stop the service by pressing CTRL-C or sending a SIGHUB. This will initiate a graceful shutdown. Please be patient - this might take a few seconds.

(6) Starting the service in a shell - as we just did - will not create a permanent running service and is probably only useful for testing. If you want a permanently running service, you need to install a systemd autostart script for `homesrv`. The following command does this job:
```
sudo bin/install_systemd_service.sh 
```

To check if the service is running smoothly, you can execute:
```
sudo systemctl status homesrv_mqtt
```

### Configuration 

The installer will create a `config.yaml` file in the default location of your OS.
For a Linux system it's probably `~/.config/homesrv_mqtt/config.yaml`, on Windowns something like `C:\Users\xxxxx\AppData\Roaming\config.yaml`

The config file contains sections for the different data sources:

* MQTT settings: General settings for MQTT server and to define which data sources / integrations shall be activated
* awido waste
* Deutsche Bahn
* Nina
* Openweathermap

#### MQTT settings
In order to enable access to your MQTT server, you need to provide `MQTT_server` and `MQTT_port`.
If your MQTT server is set up with authentification, specify your credentials in `MQTT_login` and `MQTT_password`.

`homesrv`will write the data as subtopics of `MQTT_base_topic`.
The data will be written / refreshed every `MQTT_refesh` seconds. 

```
MQTT_server:                # MQTT server name or IP
MQTT_port:                  # MQTT server port
MQTT_login:                 # MQTT server login
MQTT_password:              # MQTT server password
MQTT_base_topic: homesrv    # base topic
MQTT_disable:   True        # Disable writing to MQTT server - can be set to True for Debug purposes

MQTT_refesh:    300         # refresh info every N seconds

```

To enable / disable the different integrations, use following config entries:

```
# enable / disable integrations
MQTT_enable_awido:   True
MQTT_enable_db:      True
MQTT_enable_weather: True
MQTT_enable_nina:    True
```

#### awido waste

```
awido_region: ffb       # put your region code here
awido_title: Zuhause    # choose a title 
awido_oid: xxxxxxxxxxxx     # put your oid here 
awido_waste_types:                                  # restrict the data to the listed waste types
    - "Bioabfall"
    - "Restmülltonne 40-240 L"
    - "Papiertonne 4-wöchentlich"
    - "Wertstofftonne 80-1100 L"
#    - "Papiercontainer 2-wöchentlich"
#    - "Restmüllcontainer 660-1100 L"
    - "Problemmüll"
```

#### DButils

```
DB_client_id:      xxxxxx     # put you DB client id here
DB_client_secret:  xxxxxx     # put you DB client secret here

DB_stations:
    Pasing: 8004158            # list at least one station, using the format <Name>: <StationId>                 
#    München Hbf: 8000261
#    München Hbf Gl.27-36: 8098261
#    München Hbf Gl.5-10: 8098262
#    München Hbf (tief): 8098263

# Filter disruptions
DB_disruptions_authors:
DB_disruptions_states: 
    - BY
    - BW
DB_disruptions_withtxt: True

DB_refresh_schedule:    1800    # refresh interval from (main) schedule [seconds]
DB_refresh_changes:     60      # refreh interval for changes [seconds] (should be set >=30s)
DB_refresh_disruptions: 600     # refreh interval for disruptions [seconds]

DB_timetable_base_url:   https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/
DB_disruptions_base_url:   https://www.s-bahn-muenchen.de/.rest/verkehrsmeldungen?path=%2Faktuell
```

#### NINA

```
nina_location: xxxxxx    # Name of you city / location
```

#### openweathermap settings

```
weather_api_key: xxxxxx   # put your openweathermap api key here 
weather_lang:    de
weather_units:   metric

weather_locations:  # you can specify you locations here
    Mycity:          
        lat: 22.2222222
        lon: 11.1111111
```


