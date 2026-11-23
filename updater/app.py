
#!/usr/bin/env python3
# NovaWin Updater 0.7.0 DEV
# Interface graphique GTK4

import json
import subprocess
import threading
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib

HELPER = "/opt/novawin-updater/helper.py"


class NovaWinUpdater(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.novawin.Updater")
        self.window = None
        self.busy = False

    def do_activate(self):
        if self.window:
            self.window.present()
            return

        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title("NovaWin Updater")
        self.window.set_default_size(760, 560)

        root = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=16
        )
        root.set_margin_top(24)
        root.set_margin_bottom(24)
        root.set_margin_start(24)
        root.set_margin_end(24)

        title = Gtk.Label(label="NovaWin Updater")
        title.add_css_class("title-1")
        root.append(title)

        subtitle = Gtk.Label(
            label="Gestion des mises à jour du système Ubuntu"
        )
        root.append(subtitle)

        self.status = Gtk.Label(label="Prêt")
        self.status.set_wrap(True)
        root.append(self.status)

        buttons = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12
        )

        self.refresh_button = Gtk.Button(
            label="Rechercher les mises à jour"
        )
        self.refresh_button.connect(
            "clicked", self.on_refresh
        )
        buttons.append(self.refresh_button)

        self.simulate_button = Gtk.Button(
            label="Voir les changements"
        )
        self.simulate_button.connect(
            "clicked", self.on_simulate
        )
        buttons.append(self.simulate_button)

        self.install_button = Gtk.Button(
            label="Installer les mises à jour"
        )
        self.install_button.add_css_class("suggested-action")
        self.install_button.connect(
            "clicked", self.on_install
        )
        buttons.append(self.install_button)

        root.append(buttons)

        self.output = Gtk.TextView()
        self.output.set_editable(False)
        self.output.set_monospace(True)
        self.output.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_child(self.output)
        root.append(scroll)

        self.window.set_child(root)
        self.window.present()

    def set_output(self, text):
        buffer = self.output.get_buffer()
        buffer.set_text(text)

    def set_busy(self, busy, message):
        self.busy = busy
        self.status.set_text(message)

        for button in (
            self.refresh_button,
            self.simulate_button,
            self.install_button
        ):
            button.set_sensitive(not busy)

    def run_helper(self, action, callback):
        if self.busy:
            return

        self.set_busy(True, "Opération en cours...")

        def worker():
            try:
                process = subprocess.run(
                    [
                        "pkexec",
                        "/usr/bin/python3",
                        HELPER,
                        action
                    ],
                    capture_output=True,
                    text=True,
                    timeout=3600
                )

                try:
                    result = json.loads(process.stdout)
                except json.JSONDecodeError:
                    result = {
                        "success": False,
                        "output": process.stdout + process.stderr
                    }

            except Exception as error:
                result = {
                    "success": False,
                    "output": str(error)
                }

            GLib.idle_add(self.finish_action, callback, result)

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def finish_action(self, callback, result):
        self.set_busy(False, "Terminé" if result.get("success") else "Erreur")
        callback(result)
        return False

    def on_refresh(self, button):
        self.run_helper("refresh", self.show_result)

    def on_simulate(self, button):
        self.run_helper("simulate", self.show_result)

    def on_install(self, button):
        dialog = Gtk.AlertDialog(
            message="Installer les mises à jour Ubuntu ?",
            detail=(
                "NovaWin va installer les mises à jour disponibles. "
                "Aucune suppression automatique de paquet ne sera autorisée."
            )
        )

        dialog.set_buttons(["Annuler", "Installer"])
        dialog.set_default_button(0)
        dialog.set_cancel_button(0)
        dialog.choose(
            self.window,
            None,
            self.on_install_confirmed
        )

    def on_install_confirmed(self, dialog, result):
        try:
            choice = dialog.choose_finish(result)
        except Exception:
            return

        if choice == 1:
            self.run_helper("install", self.show_result)

    def show_result(self, result):
        output = result.get("output", "")
        removals = result.get("removals", [])

        if removals:
            output += "\n\nSUPPRESSIONS BLOQUÉES :\n"
            output += "\n".join(removals)

        if result.get("reboot_required"):
            output += "\n\nUn redémarrage du système est nécessaire."

        self.set_output(output)


app = NovaWinUpdater()
app.run(None)

