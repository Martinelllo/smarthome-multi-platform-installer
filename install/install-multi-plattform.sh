#!/usr/bin/env bash
set -e

PROJECT_DIR=~/multi-platform
SERVICE_DIR=/etc/systemd/system/multi_module_platform.service
REPO_URL=https://github.com/Martinelllo/smarthome-multi-platform-installer.git
CRON_CMD="/bin/bash /home/pi/multi-platform/install/install-multi-platform.sh"
CRON_JOB="*/10 * * * * $CRON_CMD"
ENV_BACKUP="/tmp/multi-platform.env"
LOCKFILE="/tmp/multi-platform-installer.lock"

exec 9>"$LOCKFILE" || exit 1
flock -n 9 || exit 0

sudo apt-get update -y
sudo apt-get install git -y

# Prüfen, ob Neuinstallation oder Update erforderlich ist.
INSTALLATION=false

if [ ! -d "$PROJECT_DIR/.git" ]; then
    echo "Kein Git-Repository gefunden → Neuinstallation"
    INSTALLATION=true
else
    echo "Git-Repository gefunden → Vergleiche mit origin"
    cd "$PROJECT_DIR"
    git fetch origin

    LOCAL_HASH=$(git rev-parse HEAD)
    REMOTE_HASH=$(git rev-parse origin/HEAD)

    if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
        echo "Origin ist neuer → Neuinstallation"
        INSTALLATION=true
    else
        echo "Repository ist aktuell → keine Neuinstallation"
        exit 0
    fi
fi

if [ "$INSTALLATION" = true ]; then
    sudo systemctl stop multi_module_platform 2>/dev/null || true

    if [ -f "$PROJECT_DIR/.env" ]; then
        cp "$PROJECT_DIR/.env" "$ENV_BACKUP"
    fi

    rm -rf "$PROJECT_DIR"
    git clone "$REPO_URL" "$PROJECT_DIR"

    sudo chmod 644 "$PROJECT_DIR/main.py"

    # install python3 and pip
    sudo apt-get install python3-pip -y
    pip3 install -r "$PROJECT_DIR/install/requirements.txt"

    # install pigpiod
    sudo apt-get install pigpio -y
    sudo systemctl enable pigpiod
    sudo systemctl start pigpiod

    # enable i2c
    sudo raspi-config nonint do_i2c 0

    # install i2c tools
    sudo apt-get install -y python3-smbus i2c-tools

    # install and start service
    sudo cp "$PROJECT_DIR/install/multi_module_platform.service" "$SERVICE_DIR"
    sudo chmod 644 "$SERVICE_DIR"

    sudo systemctl daemon-reload
    sudo systemctl enable multi_module_platform
    sudo systemctl start multi_module_platform

    rm -rf "$PROJECT_DIR/install"

    if [ -f "$ENV_BACKUP" ]; then
        cp "$ENV_BACKUP" "$PROJECT_DIR/.env"
    else
        cp "$PROJECT_DIR/.env_dist" "$PROJECT_DIR/.env"
    fi

    # Cronjob nur anlegen, wenn er noch nicht existiert
    (crontab -l 2>/dev/null | grep -F "$CRON_CMD") || \
    ( crontab -l 2>/dev/null; echo "$CRON_JOB" ) | crontab -

fi
