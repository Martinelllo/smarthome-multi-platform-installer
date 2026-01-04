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

UPDATE_INTERVAL_DAYS=7
UPDATE_FILE="/tmp/last_update.txt"

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
# System Updates
# ───────────────────────────────
UPDATE_NEEDED=false
if [ ! -f "$UPDATE_FILE" ]; then
    UPDATE_NEEDED=true
else
    LAST_UPDATE=$(cat "$UPDATE_FILE")
    NOW=$(date +%s)
    DIFF=$(( (NOW - LAST_UPDATE) / 86400 ))  # Sekunden → Tage
    if [ "$DIFF" -ge "$UPDATE_INTERVAL_DAYS" ]; then
        UPDATE_NEEDED=true
    fi
fi
if [ "$UPDATE_NEEDED" = true ]; then
    sudo apt-get update -y
    date +%s > "$UPDATE_FILE"
fi

# ───────────────────────────────
# Basisabhängigkeiten
# ───────────────────────────────
if ! command -v git >/dev/null 2>&1; then
    sudo apt-get install -y git
fi

# ───────────────────────────────
# Prüfen, ob Installation nötig ist
# ───────────────────────────────
BRANCH=$(git remote show origin | sed -n 's/.*HEAD branch: //p')
if [ -z "$BRANCH" ]; then
    echo "Konnte Default-Branch nicht ermitteln"
    exit 1
fi

INSTALLATION=false
if [ ! -d "$PROJECT_DIR/.git" ]; then
    INSTALLATION=true
else
    cd "$PROJECT_DIR" || exit 1

    git fetch origin

    LOCAL_HASH=$(git rev-parse HEAD)
    REMOTE_HASH=$(git rev-parse "origin/$BRANCH")

    if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
        INSTALLATION=true
    fi
fi

# ───────────────────────────────
# Installation / Update
# ───────────────────────────────
if [ "$INSTALLATION" = true ]; then
    sudo systemctl stop multi_module_platform 2>/dev/null || true

    if [ -d "$PROJECT_DIR/.git" ]; then
        cd "$PROJECT_DIR"
        git fetch origin
        git reset --hard "origin/$BRANCH"
    else
        git clone "$REPO_URL" "$PROJECT_DIR"
    fi

    # .env anlegen, falls sie nicht existiert
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        cp "$PROJECT_DIR/.env_dist" "$PROJECT_DIR/.env"
    else
        rm "$PROJECT_DIR/.env_dist"
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
