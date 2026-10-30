import os
import sys
import yaml
from pathlib import Path

PROFILES_FILE = Path(__file__).parents[4] / "snmp-bucket" / "profiles.yaml"
TELEGRAF_DIR = Path(__file__).parents[3] / "telegraf.d"

# refuse to write when more than 20 % of the devices would disappear
MAX_DEVICE_DROP = 0.2

# what telegraf asks every device
POLL_FIELDS = """
  [[inputs.snmp.field]]
    name = "sys_name"
    oid = "1.3.6.1.2.1.1.5.0"
    is_tag = true

  [[inputs.snmp.field]]
    name = "uptime"
    oid = "1.3.6.1.2.1.1.3.0"

  [[inputs.snmp.table]]
    name = "interface"
    inherit_tags = ["sys_name"]

    [[inputs.snmp.table.field]]
      name = "interface_name"
      oid = "1.3.6.1.2.1.31.1.1.1.1"
      is_tag = true

    [[inputs.snmp.table.field]]
      name = "interface_status"
      oid = "1.3.6.1.2.1.2.2.1.8"

    [[inputs.snmp.table.field]]
      name = "bytes_in"
      oid = "1.3.6.1.2.1.31.1.1.1.6"

    [[inputs.snmp.table.field]]
      name = "bytes_out"
      oid = "1.3.6.1.2.1.31.1.1.1.10"

    [[inputs.snmp.table.field]]
      name = "speed_mbps"
      oid = "1.3.6.1.2.1.31.1.1.1.15"
"""


def read_current_ips():
    ips = set()
    for conf_file in TELEGRAF_DIR.glob("*.conf"):
        with open(conf_file, encoding="utf-8") as f:
            for line in f:
                if "udp://" in line:
                    ips.add(line.split("udp://")[1].split(":")[0])
    return ips


def credential_lines(profile):
    # only names of secrets go into the file, never the passwords
    if profile["version"] == 2:
        return ["  version = 2", f'  community = "${{{profile["community_secret"].upper()}}}"']

    lines = [
        "  version = 3",
        f'  sec_name = "{profile["user"]}"',
        f'  auth_protocol = "{profile["auth_protocol"]}"',
        f'  auth_password = "@{{docker:{profile["auth_secret"]}}}"',
    ]
    if "priv_secret" in profile:
        lines.append('  sec_level = "authPriv"')
        lines.append(f'  priv_protocol = "{profile["priv_protocol"]}"')
        lines.append(f'  priv_password = "@{{docker:{profile["priv_secret"]}}}"')
    else:
        lines.append('  sec_level = "authNoPriv"')
    if "context_name" in profile:
        lines.append(f'  context_name = "{profile["context_name"]}"')
    return lines


def build_conf(site, region, profile_name, profile, ips):
    lines = ["[[inputs.snmp]]", "  agents = ["]
    for ip in sorted(ips):
        lines.append(f'    "udp://{ip}:161",')
    lines.append("  ]")
    lines.append('  agent_host_tag = "source"')
    lines += credential_lines(profile)
    lines.append("")
    lines.append("  [inputs.snmp.tags]")
    lines.append(f'    site = "{site}"')
    lines.append(f'    region = "{region}"')
    lines.append(f'    snmp_profile = "{profile_name}"')
    return "\n".join(lines) + "\n" + POLL_FIELDS


def write_conf(file_name, text):
    # write to a temp file first, so telegraf never sees a half written config
    tmp_file = TELEGRAF_DIR / f"{file_name}.tmp"
    with open(tmp_file, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp_file, TELEGRAF_DIR / file_name)


def run(netbox_instance):
    dry_run = "--dry-run" in sys.argv
    force = "--force" in sys.argv

    with open(PROFILES_FILE, encoding="utf-8") as f:
        profiles = yaml.safe_load(f)

    regions = {}
    for site in netbox_instance.dcim.sites.all(limit=1000):
        regions[site.id] = site.region.name if site.region else "none"

    # one group per site + profile: devices in one group share tags and credentials
    groups = {}
    new_ips = set()
    for device in netbox_instance.dcim.devices.filter(status="active", limit=1000):
        profile_name = device.custom_fields.get("snmp_profile")
        if device.primary_ip4 is None or profile_name not in profiles:
            print("skipping", device.name, "(no IP or unknown snmp profile)")
            continue

        ip = device.primary_ip4.address.split("/")[0]
        new_ips.add(ip)

        group = (device.site.slug, regions[device.site.id], profile_name)
        if group not in groups:
            groups[group] = []
        groups[group].append(ip)

    old_ips = read_current_ips()
    added = new_ips - old_ips
    removed = old_ips - new_ips
    print(len(new_ips), "devices:", len(added), "added,", len(removed), "removed")

    if not new_ips:
        raise SystemExit("no devices from netbox, keeping the old config")

    if len(removed) > len(old_ips) * MAX_DEVICE_DROP and not force:
        raise SystemExit(f"{len(removed)} of {len(old_ips)} devices would disappear, keeping the old config. check netbox, then use --force")

    if dry_run:
        print("dry run, nothing written")
        return

    TELEGRAF_DIR.mkdir(parents=True, exist_ok=True)

    new_files = set()
    for (site, region, profile_name), ips in groups.items():
        file_name = f"{site}-{profile_name}.conf"
        write_conf(file_name, build_conf(site, region, profile_name, profiles[profile_name], ips))
        new_files.add(file_name)

    # delete configs of sites that are gone
    for conf_file in TELEGRAF_DIR.glob("*.conf"):
        if conf_file.name not in new_files:
            conf_file.unlink()

    print(len(new_files), "telegraf configs written to", TELEGRAF_DIR)
