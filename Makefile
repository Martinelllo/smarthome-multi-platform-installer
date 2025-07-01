# Production environment
PROD_HOST = pi@192.168.178.46# Zentrale_1
# PROD_HOST = pi@192.168.178.47# test pi 3
# PROD_HOST = pi@192.168.178.48# sophia raspy
# PROD_HOST = pi@192.168.178.49# Jalousien Raspi
# PROD_HOST = pi@192.168.178.53# Temp

PROD_HOSTS = pi@192.168.178.46 pi@192.168.178.47 pi@192.168.178.48 pi@192.168.178.49

PROD_HOST_PROJECT_DIR = ~/multi_module_platform
SERVICE_TARGET = /etc/systemd/system

# Development Environment Variables
DEV_HOST = pi@192.168.178.50# development raspy
DEV_DIR = ~/projects/multi-module-platform
DEV_SSH_DIR = ~/.ssh/id_ed25519.pub
DEV_SERVICE_PATH = ./$(SERVICE_NAME)

# Project Variables
SERVICE = multi_module_platform
SERVICE_NAME = $(SERVICE).service
SCRIPT_NAME = main.py

# Local Environment Variables
LOCAL_DIR = $(CURDIR)
LOCAL_SSH_DIR = ~/.ssh/id_ed25519.pub
LOCAL_SERVICE_PATH = ./$(SERVICE_NAME)

help: ## shows this helpfile
	@grep --no-filename -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


# build and push to git
build-push:
	mkdir -p .dist
	cp -r ./* ./.dist
	sh ./push-dist.sh

# Development environment raspy 4
install: sync ## insalls all packages on the host system anyway
	ssh -t $(DEV_HOST) " \
		cd $(DEV_DIR) \
		&& sudo apt-get update -y \
		&& sudo apt-get install python3-pip -y \
		&& pip3 install -r requirements.txt --break-system-packages \
		&& sudo systemctl enable pigpiod \
		&& sudo systemctl start pigpiod \
		&& sudo raspi-config nonint do_i2c 0 \
		&& sudo apt-get install -y python3-smbus i2c-tools \
		" \

run: ## runs the script on the dev pi
	ssh -t $(DEV_HOST) " \
	cd $(DEV_DIR) \
	&& python3 $(SCRIPT_NAME) \
	" \

sync: ## sync to the HOST, enforce ssh authentication example
	rsync \
	--verbose \
	--archive \
	--recursive \
	--delete-during \
	--exclude=*__pycache__ \
	--exclude=logs \
	--exclude=data \
	--exclude=.env \
	-e 'ssh -p 22' \
	$(LOCAL_DIR)/src/ \
	$(DEV_HOST):$(DEV_DIR)

sync-run: sync run ## updates the files and runns the app on ssh

console: ## get the ssh pash of the DEV_HOST
	ssh $(DEV_HOST)


read-i2c: ## print all devices on the i2c bus to the console
	ssh -t $(DEV_HOST) " \
		sudo i2cdetect -y 1
		" \

# Production host env
install-prod: sync-prod ## insalls all packages on the host system anyway
	ssh -t $(PROD_HOST) " \
		cd $(PROD_HOST_PROJECT_DIR) \
		&& sudo apt-get update -y \
		&& sudo apt-get install python3-pip -y \
		&& pip3 install -r requirements.txt --break-system-package \
		&& sudo apt-get install pigpiod -y \
		&& sudo systemctl start pigpiod \
		&& sudo systemctl enable pigpiod \
		&& sudo raspi-config nonint do_i2c 0 \
		&& sudo apt-get install -y python3-smbus i2c-tools \
		" \

# pip3 install -r requirements.txt --break-system-packages the last option is required on some distros of pi os

ssh-install-prod: ## install ssh on the PROD_HOST
	# -ssh-keygen -f $(LOCAL_KNOWN_HOSTS) -R $(PROD_HOST) #comment this in if you want to generate new key instead of using the current
	-ssh-copy-id -i $(LOCAL_SSH_DIR) $(PROD_HOST)

console-prod: ## get the ssh pash of the PROD_HOST
	ssh $(PROD_HOST)

sync-prod:  ## sync to the HOST, enforce ssh authentication example
	rsync \
	--verbose \
	--archive \
	--recursive \
	--delete-during \
	--exclude=*__pycache__ \
	--exclude=logs \
	--exclude=data \
	--exclude=.env \
	-e 'ssh -p 22' \
	$(LOCAL_DIR)/src/ \
	$(PROD_HOST):$(PROD_HOST_PROJECT_DIR)

run-prod:  ## runs the script on the pi
	ssh -t $(PROD_HOST) " \
		cd $(PROD_HOST_PROJECT_DIR) \
		&& python3 $(SCRIPT_NAME) \
		" \

sync-run-prod: sync-prod run-prod ## updates the files and runns the app on ssh

sync-restart-prod: sync-prod service-restart-prod ## uploades changes and restarts the server

# service remote PROD_HOST
service-status-prod:  ## shows the status of the service
	ssh -t $(PROD_HOST) "sudo systemctl status $(SERVICE_NAME)"

service-restart-prod:  ## restart the service
	ssh -t $(PROD_HOST) "sudo systemctl restart $(SERVICE_NAME)"

service-disable-prod:  ## disables the service
	ssh -t $(PROD_HOST) " \
	sudo systemctl stop $(SERVICE_NAME) \
	&& sudo systemctl disable $(SERVICE_NAME)"

service-up-prod: ## moves the service file to the directory on the debian and registers the service
	rsync \
	--verbose \
	--archive \
	--delete-during \
	--delete-excluded \
	--rsync-path="sudo rsync" \
	-e 'ssh -p 22' \
	$(LOCAL_SERVICE_PATH) \
	$(PROD_HOST):$(SERVICE_TARGET)

	ssh -t $(PROD_HOST) " \
		sudo chmod 644 $(SERVICE_TARGET)/$(SERVICE_NAME) \
		&& sudo chmod 644 $(PROD_HOST_PROJECT_DIR)/$(SCRIPT_NAME) \
		&& sudo systemctl enable $(SERVICE_NAME) \
		&& sudo systemctl daemon-reload \
		&& sudo systemctl start $(SERVICE_NAME)"

sync-all: ## moves the service file to the directory on the debian and restarts the service
	@for host in $(PROD_HOSTS); do \
		echo "Syncing to $$host..."; \
		rsync \
		--verbose \
		--archive \
		--recursive \
		--delete-during \
		--exclude=*__pycache__ \
		--exclude=logs \
		--exclude=data \
		--exclude=.env \
		-e 'ssh -p 22' \
		$(LOCAL_DIR)/src/ \
		$$host:$(PROD_HOST_PROJECT_DIR) \
		&& \
		ssh -t $$host "sudo systemctl restart $(SERVICE_NAME)"; \
	done

restart-all: ## restarts the service
	@for host in $(PROD_HOSTS); do \
		ssh -t $$host "sudo systemctl restart $(SERVICE_NAME)"; \
	done

.PHONY: console install console-prod install-prod