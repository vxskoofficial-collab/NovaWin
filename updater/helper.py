
#!/usr/bin/env python3
# NovaWin Updater 0.7.0 DEV
# Ubuntu 24.04 - System Update Engine

import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

VERSION = "0.7.0-dev"
REBOOT_FLAG = "/var/run/reboot-required"
PLAN_DIR = Path("/run/novawin-updater/plans")
PLAN_LIFETIME = 300
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


def get_simulation():
    success, output = run_command([
        "apt-get", "-s", "full-upgrade"
    ])

    if not success:
        response(False, output)

    removals = [
        line for line in output.splitlines()
        if line.startswith("Remv ")
    ]

    return output, removals


def save_plan(output):
    PLAN_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(PLAN_DIR.parent, 0o700)
    os.chmod(PLAN_DIR, 0o700)

    plan_id = secrets.token_urlsafe(32)
    plan = {
        "created": time.time(),
        "hash": hashlib.sha256(
            output.encode("utf-8")
        ).hexdigest()
    }

    plan_file = PLAN_DIR / f"{plan_id}.json"

    descriptor = os.open(
        plan_file,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600
    )

    with os.fdopen(descriptor, "w", encoding="utf-8") as file:
        json.dump(plan, file)

    return plan_id


def refresh():
    success, output = run_command(["apt-get", "update"])
    response(success, output)


def simulate():
    output, removals = get_simulation()

    if removals:
        response(
            False,
            output + "\n\nInstallation bloquée : suppressions détectées.",
            removals=removals,
            removal_count=len(removals)
        )

    plan_id = save_plan(output)

    response(
        True,
        output,
        plan_id=plan_id,
        expires_in=PLAN_LIFETIME,
        removal_count=0,
        reboot_required=os.path.exists(REBOOT_FLAG)
    )


def install(plan_id):
    if (
        not plan_id
        or len(plan_id) > 128
        or any(c not in
               "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
               for c in plan_id)
    ):
        response(False, "Invalid update plan.")

    plan_file = PLAN_DIR / f"{plan_id}.json"

    try:
        with plan_file.open("r", encoding="utf-8") as file:
            plan = json.load(file)
    except (OSError, ValueError):
        response(False, "Update plan missing or already used.")

    if time.time() - plan.get("created", 0) > PLAN_LIFETIME:
        plan_file.unlink(missing_ok=True)
        response(False, "Update plan expired. Run simulation again.")

    output, removals = get_simulation()

    if removals:
        plan_file.unlink(missing_ok=True)
        response(
            False,
            "Installation blocked: package removals detected.",
            removals=removals
        )

    current_hash = hashlib.sha256(
        output.encode("utf-8")
    ).hexdigest()

    if current_hash != plan.get("hash"):
        plan_file.unlink(missing_ok=True)
        response(
            False,
            "The update plan has changed. Run simulation again."
        )

    # Consommer le plan avant de lancer l'installation.
    plan_file.unlink(missing_ok=True)

    success, install_output = run_command([
        "apt-get", "full-upgrade", "-y"
    ])

    response(
        success,
        install_output,
        reboot_required=os.path.exists(REBOOT_FLAG)
    )


def main():
    require_root()

    if len(sys.argv) < 2:
        response(False, "Invalid action.")

    action = sys.argv[1]

    if action == "refresh" and len(sys.argv) == 2:
        refresh()

    elif action == "simulate" and len(sys.argv) == 2:
        simulate()

    elif action == "install" and len(sys.argv) == 3:
        install(sys.argv[2])

    else:
        response(False, "Unknown action or invalid arguments.")


if __name__ == "__main__":
    main()
