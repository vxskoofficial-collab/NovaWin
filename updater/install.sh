
#!/usr/bin/env bash
set -Eeuo pipefail

VERSION="0.7.0-dev"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ $EUID -ne 0 ]]; then
    echo "Lance ce script avec : sudo bash install.sh"
    exit 1
fi

for file in app.py helper.py; do
    if [[ ! -f "$SCRIPT_DIR/$file" ]]; then
        echo "Fichier manquant : $file"
        exit 1
    fi
done

echo "Installation NovaWin Updater $VERSION"

python3 -m py_compile "$SCRIPT_DIR/app.py" "$SCRIPT_DIR/helper.py"

BACKUP="/var/backups/novawin-updater-before-0.7.0-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"

for path in \
    /opt/novawin-updater \
    /usr/local/bin/novawin-updater \
    /usr/local/bin/novawin-updater-helper \
    /usr/local/share/novawin-updater \
    /usr/share/applications/novawin-updater.desktop
do
    if [[ -e "$path" || -L "$path" ]]; then
        mkdir -p "$BACKUP$(dirname "$path")"
        cp -a -- "$path" "$BACKUP$path"
    fi
done

TEMP="$(mktemp -d)"
cleanup() {
    rm -rf "$TEMP"
}
trap cleanup EXIT

install -d -o root -g root -m 755 \
    /opt/novawin-updater \
    /usr/local/share/novawin-updater \
    /opt/novawin/managed \
    /var/lib/novawin-updater \
    /usr/share/applications

install -o root -g root -m 755 \
    "$SCRIPT_DIR/helper.py" \
    /opt/novawin-updater/helper.py

install -o root -g root -m 755 \
    "$SCRIPT_DIR/app.py" \
    /usr/local/share/novawin-updater/app.py

cat > /usr/local/bin/novawin-updater <<'EOF'
#!/bin/sh
exec /usr/bin/python3 /usr/local/share/novawin-updater/app.py "$@"
EOF

chmod 755 /usr/local/bin/novawin-updater
chown root:root /usr/local/bin/novawin-updater

cat > /usr/share/applications/novawin-updater.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=NovaWin Updater
Comment=Gestion des mises à jour NovaWin et Ubuntu
Exec=/usr/local/bin/novawin-updater
Icon=system-software-update
Terminal=false
Categories=System;Settings;
EOF

chmod 644 /usr/share/applications/novawin-updater.desktop

python3 -m py_compile \
    /opt/novawin-updater/helper.py \
    /usr/local/share/novawin-updater/app.py

rm -rf \
    /opt/novawin-updater/__pycache__ \
    /usr/local/share/novawin-updater/__pycache__

echo
echo "NovaWin Updater $VERSION installé."
echo "Sauvegarde : $BACKUP"
echo "Lancement : novawin-updater"
