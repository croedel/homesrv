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
For a Linux system it's probably `~/.config/mtecmqtt/config.yaml`, on Windowns something like `C:\Users\xxxxx\AppData\Roaming\config.yaml`




## Data sources / APIs

### awido

### Deutsche Bahn (DButils)

### nina
This project offers a (hopefully) user-friendly API to the NINA API https://nina.api.bund.dev/ and allows you to retrieve warning messages for your home location.

### openweathermap


