#!/usr/bin/env python3
# NovaWin Updater 0.7.0 DEV
# Moteur sécurisé de mise à jour Ubuntu 24.04

import json
import os
import subprocess
import sys

VERSION = "0.7.0-dev"
REBOOT_FLAG = "/var/run/reboot-required"


def run_command(command):
    process = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return {
        "success": process.returncode == 0,
        "output": process.stdout,
        "returncode": process.returncode
    }


def check_root():
    if os.geteuid() != 0:
        return False
    return True


def refresh():
    return run_command(["apt-get", "update"])


def simulate():
    return run_command(["apt-get", "-s", "full-upgrade"])


def install():
    if not check_root():
        return {"success": False, "output": "Administrator privileges required"}

    result = run_command([
        "apt-get",
        "full-upgrade",
        "-y"
    ])

    result["reboot_required"] = os.path.exists(REBOOT_FLAG)
    return result


def main():
    if len(sys.argv) != 2:
        print(json.dumps({
            "success": False,
            "error": "Invalid action"
        }))
        sys.exit(1)

    action = sys.argv[1]

    if not check_root():
        print(json.dumps({
            "success": False,
            "error": "Administrator privileges required"
        }))
        sys.exit(1)

    actions = {
        "refresh": refresh,
        "simulate": simulate,
        "install": install
    }

    if action not in actions:
        print(json.dumps({
            "success": False,
            "error": "Unknown action"
        }))
        sys.exit(1)

    result = actions[action]()
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
