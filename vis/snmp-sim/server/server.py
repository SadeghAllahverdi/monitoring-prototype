import os
import csv
import yaml
import shutil
import subprocess
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
PROFILES_FILE = Path(__file__).parent / "profiles.yaml"
SNMP_AGENTS_DIR = Path(__file__).parent / "snmp-agents"

def read_secret(name):
    with open(f"/run/secrets/{name}", encoding="utf-8") as f:
        return f.read().strip()

def main():
    with open(PROFILES_FILE, encoding="utf-8") as f:
        profiles = yaml.safe_load(f)

    with open(DATA_DIR / "devices.csv", encoding="utf-8") as f:
        devices = list(csv.DictReader(f))

    for device in devices:
        subprocess.run(["ip", "addr", "add", f"{device['ip']}/16", "dev", "eth0"], check=True)
    print(len(devices), "device IPs added")

    # start with an empty device folder
    shutil.rmtree(SNMP_AGENTS_DIR, ignore_errors=True)
    os.mkdir(SNMP_AGENTS_DIR)

    command = ["snmpsim-command-responder", "--process-user=nobody", "--process-group=nogroup"]
    for device in devices:
        profile = profiles[device["profile"]]

        # each device gets its own folder
        snmp_agent_dir = SNMP_AGENTS_DIR / device["name"]
        os.mkdir(snmp_agent_dir)

        if profile["version"] == 2:
            file_name = read_secret(profile["community_secret"])
        else:
            file_name = "device"
        shutil.copy(DATA_DIR / f"{device['name']}.snmprec", snmp_agent_dir / f"{file_name}.snmprec")

        # fixed engine id per device, made from its IP: v3 passwords are tied to it
        ip_hex = ""
        for part in device["ip"].split("."):
            ip_hex += f"{int(part):02x}"

        command.append(f"--v3-engine-id=80001f8805{ip_hex}")
        command.append(f"--data-dir={snmp_agent_dir}")
        command.append(f"--agent-udpv4-endpoint={device['ip']}:161")

        if profile["version"] == 3:
            command.append(f"--v3-user={profile['user']}")
            command.append(f"--v3-auth-key={read_secret(profile['auth_secret'])}")
            command.append(f"--v3-auth-proto={profile['auth_protocol']}")
            if "priv_secret" in profile:
                command.append(f"--v3-priv-key={read_secret(profile['priv_secret'])}")
                command.append(f"--v3-priv-proto={profile['priv_protocol']}")

    print("starting snmpsim for", len(devices), "devices")
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
