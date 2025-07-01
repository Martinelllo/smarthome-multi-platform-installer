#!/usr/bin/env bash

sudo apt-get update -y
sudo apt-get install git -y

rm -rf ~/multi-platform/
git clone https://github.com/Martinelllo/smarthome-multi-platform-installer.git ~/multi-platform

sudo apt-get install python3-pip -y
pip3 install -r ~/multi-platform/install/requirements.txt --break-system-packages

# install pigpiod
sudo apt-get install pigpiod -y
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# enable i2c on raspi-config
sudo raspi-config nonint do_i2c 0

# install i2c helper tools
sudo apt-get install -y python3-smbus i2c-tools

# install and start service
cp ~/multi-platform/install/multi_module_platform.service etc/systemd/system/multi_module_platform.service
sudo chmod 644 /etc/systemd/system/multi_module_platform.service
sudo chmod 644 ~/multi-platform/main.py
sudo systemctl enable multi_module_platform.service
sudo systemctl daemon-reload
sudo systemctl start multi_module_platform.service

rm -rf ~/multi-platform/install