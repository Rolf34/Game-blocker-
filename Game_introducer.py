import os
import time
import logging  
import subprocess

GAMES = {
    "Steam": r"C:\Program Files (x86)\Steam\steam.exe",
    "Epic Games": r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
    "Rust": r"C:\Program Files (x86)\Steam\steamapps\common\Rust\RustClient.exe",
}

INTERVAL = 300
BLOCK_DURATION = 30

logging.basicConfig(
    filename=os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "game_introducer.log"

    ),
    level = logging.INFO,
    format = "%(asctime)s - %(message)s"
)

def ps_quote(value):
    return "'" + value.replace("'", "''") + "'"

def firewall_rule(name, path, direction, enabled):
    rule = ps_quote(name)
    program = ps_quote(path)
    state = "True" if enabled else "False"

    command = f"""
    $r = Get-NetFirewallRule -DisplayName {rule} -ErrorAction SilentlyContinue
    if (-not $r) {{
        $params = @{{
            DisplayName = {rule}
            Program = {program}
            Direction = '{direction}'
            Action = 'Block'
            Enabled = $false
        }}
        New-NetFirewallRule @params | Out-Null
    }}
    Set-NetFirewallRule -DisplayName {rule} -Enabled {state}
    """
    subprocess.run(["powershell", "-NoProfile", "-Command", command],
       check = True,
         capture_output = True,
            text = True
    )

def set_block(enabled):
    for app, path in GAMES.items():
        if not os.path.isfile(path):
            logging.warning("File not found: %s (%s)", app, path)
            continue

        for direction in ("Inbound", "Outbound"):
            name = f"Game Introducer - {app} - {direction}"
            firewall_rule(name, path, direction, enabled)

def set_block_temporarily(duration):
    logging.info("Blocking games for %d seconds...", duration)
    try:
        set_block(True)
        time.sleep(duration)
    finally:
        set_block(False)
        logging.info("Unblocking games.")

def main():
    logging.info("Starting Game Introducer...")

    try:
        while True:
            time.sleep(INTERVAL)
            logging.info("Blocking games for %d seconds...", BLOCK_DURATION)
            try:
                set_block(True)
                time.sleep(BLOCK_DURATION)
            finally:
                set_block(False)
                logging.info("Unblocking games.")
    except KeyboardInterrupt:
        logging.info("Stopping Game Introducer...")
    finally:
        try:
            set_block(False)
        except Exception:
            logging.exception("Failed to unblock games on exit.")

if __name__ == "__main__":
    main()