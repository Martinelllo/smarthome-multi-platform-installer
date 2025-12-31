#!/usr/bin/env bash
set -e

# ───────────────────────────────
# Konfiguration
# ───────────────────────────────
PROJECT_DIR="/home/pi/multi-platform"
SERVICE_DIR="/etc/systemd/system/multi_module_platform.service"
REPO_URL="https://github.com/Martinelllo/smarthome-multi-platform-installer.git"

CRON_CMD="curl -sL https://raw.githubusercontent.com/Martinelllo/smarthome-multi-platform-installer/main/install/install-multi-plattform.sh | bash"
CRON_JOB="*/1 * * * * $CRON_CMD" # Jede Minute

ENV_BACKUP="/tmp/multi-platform.env"
DATA_BACKUP="/tmp/multi-platform.data"

LOCKFILE="/tmp/multi-platform-installer.lock"

# ───────────────────────────────
# Lock gegen parallele Läufe
# ───────────────────────────────
exec 9>"$LOCKFILE" || exit 1
flock -n 9 || exit 0

# ───────────────────────────────
# Cronjob immer sicherstellen
# ───────────────────────────────
(crontab -l 2>/dev/null | grep -F "$CRON_CMD") || \
( crontab -l 2>/dev/null; echo "$CRON_JOB" ) | crontab -

# ───────────────────────────────
# Basisabhängigkeiten
# ───────────────────────────────
sudo apt-get update -y
sudo apt-get install -y git

# ───────────────────────────────
# Prüfen, ob Installation nötig ist
# ───────────────────────────────
INSTALLATION=false

if [ ! -d "$PROJECT_DIR/.git" ]; then
    INSTALLATION=true
else
    cd "$PROJECT_DIR"
    git fetch origin

    LOCAL_HASH=$(git rev-parse HEAD)
    REMOTE_HASH=$(git rev-parse origin/HEAD)

    if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
        INSTALLATION=true
    fi
fi

# ───────────────────────────────
# Installation / Update
# ───────────────────────────────
if [ "$INSTALLATION" = true ]; then
    sudo systemctl stop multi_module_platform 2>/dev/null || true

    # .env and data sichern
    if [ -f "$PROJECT_DIR/.env" ]; then
        cp "$PROJECT_DIR/.env" "$ENV_BACKUP"
    fi
    if [ -f "$PROJECT_DIR/data/config.json" ]; then
        cp "$PROJECT_DIR/data/config.json" "$DATA_BACKUP"
    fi

    rm -rf "$PROJECT_DIR"
    git clone "$REPO_URL" "$PROJECT_DIR"

    # .env and data wiederherstellen
    if [ -f "$ENV_BACKUP" ]; then
        cp "$ENV_BACKUP" "$PROJECT_DIR/.env"
    else
        cp "$PROJECT_DIR/.env_dist" "$PROJECT_DIR/.env"
    fi
    if [ -f "$DATA_BACKUP" ]; then
        cp "$DATA_BACKUP" "$PROJECT_DIR/data/config.json"
    fi

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
fi
