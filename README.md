# segment-display

## Install

Run `https://raw.githubusercontent.com/Martinelllo/smarthome-multi-platform-installer/main/install-multi-plattform.sh` on the raspberry pi.




!!deprecated!! look at the Makefile. there are the install scripts.

run `ssh-install-prod` to install your public key on the host
run `make install` to remote-install the requirements on the raspberry py

add the host adresses and users to the Makefile variable and 
run `make sync` to transfere all required files
run `make remote` to get the host console
run
```bash
sudo apt-get update &&
sudo apt-get install build-essential python-dev python-openssl git-core
```
run 
```bash
sudo apt-get install -y pigpio python-pigpio python3-pigpio && 
sudo systemctl enable pigpiod &&
sudo systemctl start pigpiod &&
pip install -r requirements.txt &&
make service-up
```

## Trubel shooting

Run `i2cdetect -y 1` to show all devices on the i2c
