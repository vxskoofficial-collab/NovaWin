
#!/usr/bin/env python3
# NovaWin Updater 0.7.0 DEV
# Ubuntu 24.04 - System Update Engine

import json
import os
import subprocess
import sys

VERSION = "0.7.0-dev"
REBOOT_FLAG = "/var/run/reboot-required"
TIMEOUT = 3600


def response(success, output="", **extra):
    result = {
        "success": success,
        "version": VERSION,
        "output": output
    }
    result.update(extra)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if success else 1)


def require_root():
    if os.geteuid() != 0:
        response(False, "Administrator privileges required.")


def run_command(command, timeout=TIMEOUT):
    try:
        process = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
            env={
                **os.environ,
                "DEBIAN_FRONTEND": "noninteractive"
            }
        )
        return process.returncode == 0, process.stdout or ""
    except subprocess.TimeoutExpired as error:
        output = error.stdout or ""
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        return False, output + "\nOperation timed out."
    except OSError as error:
        return False, str(error)


def refresh():
    success, output = run_command(["apt-get", "update"])
    response(success, output)


def simulate():
    success, output = run_command([
        "apt-get", "-s", "full-upgrade"
    ])

    if not success:
        response(False, output)

    removals = [
        line for line in output.splitlines()
        if line.startswith("Remv ")
    ]

    response(
        True,
        output,
        removals=removals,
        removal_count=len(removals),
        reboot_required=os.path.exists(REBOOT_FLAG)
    )


def install():
    # La confirmation doit être demandée par l'interface
    # avant l'appel de cette action.
    success, simulation = run_command([
        "apt-get", "-s", "full-upgrade"
    ])

    if not success:
        response(False, simulation)

    removals = [
        line for line in simulation.splitlines()
        if line.startswith("Remv ")
    ]

    # Refus de supprimer des paquets automatiquement.
    if removals:
        response(
            False,
            "Installation annulée : des suppressions de paquets "
            "sont prévues. Vérification manuelle nécessaire.",
            removals=removals,
            removal_count=len(removals)
        )

    success, output = run_command([
        "apt-get", "full-upgrade", "-y"
    ])

    response(
        success,
        output,
        reboot_required=os.path.exists(REBOOT_FLAG)
    )


def main():
    require_root()

    if len(sys.argv) != 2:
        response(False, "Invalid action.")

    actions = {
        "refresh": refresh,
        "simulate": simulate,
        "install": install
    }

    action = sys.argv[1]

    if action not in actions:
        response(False, "Unknown action.")

    actions[action]()


if __name__ == "__main__":
    main()
