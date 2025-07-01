#!/usr/bin/env bash

sudo apt-get update -y
sudo apt-get install python3-pip -y
pip3 install -r requirements.txt --break-system-packages
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
sudo raspi-config nonint do_i2c 0
sudo apt-get install -y python3-smbus i2c-tools