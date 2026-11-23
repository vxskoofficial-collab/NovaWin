
#!/usr/bin/env bash
# NovaWin Updater 0.7.0 DEV
# Ubuntu 24.04

set -Eeuo pipefail

VERSION="0.7.0-dev"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ $EUID -ne 0 ]]; then
    echo "Lance ce script avec : sudo bash install.sh"
    exit 1
fi

echo "Préparation de NovaWin Updater $VERSION..."

for file in app.py helper.py test_helper.py; do
    if [[ ! -f "$SCRIPT_DIR/$file" ]]; then
        echo "ERREUR : fichier manquant : $file"
        exit 1
    fi
done

echo "Vérification de la syntaxe Python..."

python3 -m py_compile \
    "$SCRIPT_DIR/app.py" \
    "$SCRIPT_DIR/helper.py" \
    "$SCRIPT_DIR/test_helper.py"

echo "Vérification des dépendances..."

if ! python3 -c "import gi" 2>/dev/null; then
    echo "Installation de python3-gi..."
    apt-get update
    apt-get install -y python3-gi gir1.2-gtk-4.0 policykit-1
fi

python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk"

BACKUP="/var/backups/novawin-updater-before-0.7.0-$(date +%Y%m%d-%H%M%S)"

TARGETS=(
    /opt/novawin-updater
    /usr/local/share/novawin-updater
    /usr/local/bin/novawin-updater
    /usr/share/applications/novawin-updater.desktop
)

echo "Création de la sauvegarde..."
install -d -o root -g root -m 700 "$BACKUP"

for path in "${TARGETS[@]}"; do
    if [[ -e "$path" || -L "$path" ]]; then
        mkdir -p "$BACKUP$(dirname "$path")"
        cp -a -- "$path" "$BACKUP$path"
    fi
done

TEMP="$(mktemp -d)"
ROLLBACK_NEEDED=0

restore_backup() {
    local path

    echo
    echo "ERREUR : restauration de la sauvegarde..."

    for path in "${TARGETS[@]}"; do
        rm -rf -- "$path"

        if [[ -e "$BACKUP$path" || -L "$BACKUP$path" ]]; then
            mkdir -p "$(dirname "$path")"
            cp -a -- "$BACKUP$path" "$path"
        fi
    done

    echo "Restauration terminée."
}

cleanup() {
    local status=$?

    if [[ $status -ne 0 && $ROLLBACK_NEEDED -eq 1 ]]; then
        restore_backup
    fi

    rm -rf -- "$TEMP"
    exit "$status"
}

trap cleanup EXIT

ROLLBACK_NEEDED=1

echo "Installation des répertoires..."

install -d -o root -g root -m 755 \
    /opt/novawin-updater \
    /usr/local/share/novawin-updater \
    /opt/novawin/managed \
    /var/lib/novawin-updater \
    /usr/share/applications

echo "Installation du moteur..."

install -o root -g root -m 755 \
    "$SCRIPT_DIR/helper.py" \
    /opt/novawin-updater/helper.py

echo "Installation de l'interface..."

install -o root -g root -m 755 \
    "$SCRIPT_DIR/app.py" \
    /usr/local/share/novawin-updater/app.py

cat > "$TEMP/novawin-updater" <<'EOF'
#!/bin/sh
exec /usr/bin/python3 /usr/local/share/novawin-updater/app.py "$@"
EOF

install -o root -g root -m 755 \
    "$TEMP/novawin-updater" \
    /usr/local/bin/novawin-updater

cat > "$TEMP/novawin-updater.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=NovaWin Updater
Comment=Gestion des mises à jour NovaWin et Ubuntu
Exec=/usr/local/bin/novawin-updater
Icon=system-software-update
Terminal=false
Categories=System;Settings;
EOF

install -o root -g root -m 644 \
    "$TEMP/novawin-updater.desktop" \
    /usr/share/applications/novawin-updater.desktop

echo "Vérification de l'installation..."

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

ROLLBACK_NEEDED=0
trap - EXIT
rm -rf -- "$TEMP"
