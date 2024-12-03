#!/bin/sh

DIR=$(dirname "$0")
BASE_DIR=$(readlink -f $DIR)

SVC_TXT="
[Unit]
Description=homesrv MQTT 
After=multi-user.target

[Service]
Type=simple
User=USER
WorkingDirectory=BASE_DIR
ExecStart=BASE_DIR/python3 homesrv_mqtt
Restart=always

[Install]
WantedBy=multi-user.target
"

echo "homesrv_mqtt: Installing systemd service to auto-start homesrv"

if [ $(id -u) != "0" ]; then
  echo "This script required root rights. Please restart using 'sudo'"
else
  echo "$SVC_TXT" | sed "s!BASE_DIR!$BASE_DIR!g" | sed "s/USER/$SUDO_USER/g" > /tmp/homesrv_mqtt.service 
  chmod 666 /tmp/homesrv_mqtt.service
  mv /tmp/homesrv_mqtt.service /etc/systemd/system
  systemctl daemon-reload
  systemctl enable homesrv_mqtt.service
  systemctl start homesrv_mqtt.service
  echo "==> systemd service '/etc/systemd/system/homesrv_mqtt.service' installed"
fi

