#!/usr/bin/env bash
set -e

# ───────────────────────────────
# Konfiguration
# ───────────────────────────────
PROJECT_DIR="/home/pi/multi-platform"
SERVICE_DIR="/etc/systemd/system/multi_module_platform.service"
REPO_URL="https://github.com/Martinelllo/smarthome-multi-platform-installer.git"

CRON_CMD="/bin/bash /home/pi/multi-platform/install/install-multi-platform.sh"
CRON_JOB="*/1 * * * * $CRON_CMD" # Jede Minute

ENV_BACKUP="/tmp/multi-platform.env"
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
sudo apt-get install -y git python3-pip pigpio python3-smbus i2c-tools

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

    # .env sichern
    if [ -f "$PROJECT_DIR/.env" ]; then
        cp "$PROJECT_DIR/.env" "$ENV_BACKUP"
    fi

    rm -rf "$PROJECT_DIR"
    git clone "$REPO_URL" "$PROJECT_DIR"

    # .env wiederherstellen
    if [ -f "$ENV_BACKUP" ]; then
        cp "$ENV_BACKUP" "$PROJECT_DIR/.env"
    else
        cp "$PROJECT_DIR/.env_dist" "$PROJECT_DIR/.env"
    fi

    sudo chmod 644 "$PROJECT_DIR/main.py"

    pip3 install -r "$PROJECT_DIR/install/requirements.txt"

    sudo systemctl enable pigpiod
    sudo systemctl start pigpiod

    sudo raspi-config nonint do_i2c 0

    sudo cp "$PROJECT_DIR/install/multi_module_platform.service" "$SERVICE_DIR"
    sudo chmod 644 "$SERVICE_DIR"

    sudo systemctl daemon-reload
    sudo systemctl enable multi_module_platform
    sudo systemctl restart multi_module_platform
fi
