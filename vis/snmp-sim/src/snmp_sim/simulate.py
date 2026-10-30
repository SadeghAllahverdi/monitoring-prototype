import os
import csv
import shutil
import random
from pathlib import Path

DATA_DIR = Path(__file__).parents[2] / "data"

# snmp addresses
SYS_DESCRIPTION = "1.3.6.1.2.1.1.1.0"
SYS_UPTIME = "1.3.6.1.2.1.1.3.0"
SYS_NAME = "1.3.6.1.2.1.1.5.0"
PORT_STATUS = "1.3.6.1.2.1.2.2.1.8"
PORT_NAME = "1.3.6.1.2.1.31.1.1.1.1"
PORT_BYTES_IN = "1.3.6.1.2.1.31.1.1.1.6"
PORT_BYTES_OUT = "1.3.6.1.2.1.31.1.1.1.10"
PORT_SPEED = "1.3.6.1.2.1.31.1.1.1.15"

# snmp values
TEXT = "4"
NUMBER = "2"
GAUGE = "66"
TICKS = "67:numeric"
COUNTER = "70:numeric"

# traffic per ports in byte/s
TRAFFIC_BY_ROLE = {
    "core-switch": (20000000, 80000000),
    "router": (5000000, 40000000),
    "firewall": (5000000, 30000000),
    "access-switch": (100000, 5000000),
}
DEFAULT_TRAFFIC = (100000, 5000000)
HOT_SITES = ["frankfurt-am-main"]
HOT_TRAFFIC = (100000000, 120000000)

def run(netbox_instance):
    devices = list(netbox_instance.dcim.devices.all(limit=1000))
    if not devices:
        print("no devices in netbox, nothing to simulate")
        return

    dev_interfaces = {}
    for interface in netbox_instance.dcim.interfaces.filter(mgmt_only=False, limit=1000):
        if interface.device.id not in dev_interfaces:
            dev_interfaces[interface.device.id] = []
        dev_interfaces[interface.device.id].append(interface.name)

    # delete the old data folder
    shutil.rmtree(path=DATA_DIR, ignore_errors=True)
    # make it fresh
    os.mkdir(path=DATA_DIR)

    rows = []
    for device in devices:
        if device.primary_ip4 is None or not device.custom_fields.get("snmp_profile"):
            print("skipping", device.name, "(no IP or no snmp profile)")
            continue

        ip = device.primary_ip4.address.split("/")[0]
        profile = device.custom_fields["snmp_profile"]

        port_names = dev_interfaces.get(device.id, [])

        rng = random.Random(device.name)
        low, high = TRAFFIC_BY_ROLE.get(device.role.slug, DEFAULT_TRAFFIC)
        if device.site.slug in HOT_SITES:
            low, high = HOT_TRAFFIC

        answers = [
            f"{SYS_DESCRIPTION}|{TEXT}|{device.device_type.model}",
            f"{SYS_UPTIME}|{TICKS}|rate=100",
            f"{SYS_NAME}|{TEXT}|{device.name}",
        ]

        port_status, port_name, bytes_in, bytes_out, port_speed = [], [], [], [], []

        for i, name in enumerate(port_names, start=1):
            up = rng.random() < 0.9
            port_status.append(f"{PORT_STATUS}.{i}|{NUMBER}|{1 if up else 2}")
            port_name.append(f"{PORT_NAME}.{i}|{TEXT}|{name}")
            bytes_in.append(f"{PORT_BYTES_IN}.{i}|{COUNTER}|rate={rng.randint(low, high) if up else 0}")
            bytes_out.append(f"{PORT_BYTES_OUT}.{i}|{COUNTER}|rate={rng.randint(low // 2, high // 2) if up else 0}")
            port_speed.append(f"{PORT_SPEED}.{i}|{GAUGE}|1000")

        answers += port_status + port_name + bytes_in + bytes_out + port_speed

        with open(f"{DATA_DIR}/{device.name}.snmprec", "w", encoding="utf-8") as f:
            f.write("\n".join(answers) + "\n")

        rows.append({"name": device.name, "ip": ip, "profile": profile})

    with open(f"{DATA_DIR}/devices.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "ip", "profile"])
        writer.writeheader()
        writer.writerows(rows)

    print(len(rows), "devices written to", DATA_DIR)