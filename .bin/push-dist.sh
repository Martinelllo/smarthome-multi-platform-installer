#!/usr/bin/env bash
set -e

REPO="git@github.com:Martinelllo/smarthome-multi-platform-installer.git"
BRANCH="main"
DIST_DIR=".dist"

TMPDIR=$(mktemp -d)
git clone $REPO $TMPDIR
cd "$TMPDIR"

# Branch main neu auf origin/main setzen (force reset)
git fetch origin
git checkout -B $BRANCH origin/$BRANCH

# Dateien kopieren
cp -r "$OLDPWD/$DIST_DIR"/. "$TMPDIR"

# Commit falls Änderungen
git add -A
git commit -m "Update installer files: $(date)" || echo "No changes to commit."

# Push (ohne force, wenn Probleme mit fast-forward, dann force versuchen)
git push --force origin $BRANCH

rm -rf "$TMPDIR"
