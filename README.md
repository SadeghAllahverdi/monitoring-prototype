# Monitoring Prototype

A network monitoring lab. NetBox knows what's on the network, and everything else builds itself from that: fake switches, Telegraf's config, the data in InfluxDB, and the dashboards in Grafana.

All the devices are fake. There are 50 of them, because that's what fits on a laptop.

## How it works

```
NetBox -> seed fills it with 50 fake devices
       -> simulator pretends to be those devices
       -> generator writes the Telegraf config, every 10 minutes
          Telegraf asks every device every 30 seconds
          InfluxDB stores the answers for 7 days
          Grafana shows it all
```

## Start it

You need Docker Desktop. Nothing else, no Python, no uv.

Make sure Docker Desktop is running, open a terminal in this folder, and run:

```powershell
docker compose up -d --build
```

Grab a coffee. The first start takes about 5 minutes, plus the image downloads. Everything starts in the right order by itself.

Stop it with:

```powershell
docker compose down
```

Your data stays. Adding `-v` wipes it, and the next start builds everything again from nothing.

## Where to look

| What | Link | User | Password file |
|---|---|---|---|
| Grafana | http://127.0.0.1:3000/d/germany-noc | admin | `vis/grafana/secrets/admin-password.txt` |
| InfluxDB | http://127.0.0.1:8086 | admin | `vis/influxdb/secrets/admin-password.txt` |
| NetBox | http://127.0.0.1:8000 | admin | `sot/netbox-docker/secrets/superuser_password.txt` |

Grafana needs a minute or two to show data, and the map needs internet.

## The dashboards

- **Overview:** all of Germany, with a map and a network tree. Start here.
- **Site view:** one city. Click a site in the tree, or open a bubble on the map.
- **Device view:** one device. Click a device name in the tree or a table.

The dashboards are JSON files in `vis/grafana/dashboards/`. Change them there, then restart Grafana. Changes made in Grafana's own editor don't reach those files.

```powershell
docker compose restart grafana
```

## Who does what

| Folder | What's in it |
|---|---|
| `sot/seed` | fills NetBox with fake devices |
| `sot/netbox-docker` | NetBox itself |
| `vis/snmp-sim` | the fake devices (lab only) |
| `vis/snmp-bucket` | SNMP profiles and passwords, shared by the simulator and Telegraf |
| `vis/telegraf` | Telegraf and the generator |
| `vis/influxdb` | the database |
| `vis/grafana` | the dashboards |

`docker-compose.yml` lists the stacks. `docker-compose.override.yml` says what waits for what, and which token to use.

## Good to know

- **The generator has safety nets.** If NetBox is down, or more than 20% of the devices suddenly vanish, it keeps the old config instead of breaking monitoring. To allow a big change anyway, run it with `--force`.
- **A dead device disappears from the tree.** It doesn't turn red. Watch the **Devices polled** number.
- **Traffic lines look flat.** Each fake port has one fixed speed. That's the simulator, not a bug.
- **The simulator only reads NetBox when it starts.** After changing devices, restart it.
- **Secrets are not in git.** `sot/netbox-docker` isn't either, so a plain `git clone` won't start. Use the zip, or add both by hand.

## Going to production

Take your time with this part. The lab takes some shortcuts that production shouldn't.

**1. Remove the lab**

- In `docker-compose.yml`, delete the three lines under "for simulation only".
- In `docker-compose.override.yml`, delete the `telegraf-config-gen`, `snmp-data-sim` and `snmp-sim` blocks, `snmp-sim` under `telegraf`, and the `secrets` block. The generator itself stays.
- In `vis/telegraf/docker-compose.yml`, remove `snmp-lab`.
- In `vis/snmp-bucket/profiles.yaml`, delete the `context_name` lines. Real switches don't need them.

**2. Connect the real NetBox**

Set `NETBOX_URL` in `vis/telegraf/docker-compose.yml` to your real NetBox.

**3. Make three tokens**

| Who | Token | Where it's made |
|---|---|---|
| Generator | read-only | your real NetBox |
| Telegraf | write-only for bucket `snmp` | InfluxDB |
| Grafana | read-only for bucket `snmp` | InfluxDB |

- **Telegraf:** save the token in `vis/telegraf/secrets/influx-token.txt`, with no newline at the end.
- **Grafana:** save the token in `vis/grafana/secrets/influx-read-token.txt`, also with no newline.
- **Generator:** this one needs a small change. It currently builds its token from two lab secret files in `sot/netbox-docker/secrets`, and those won't exist anymore. Give it one secret file holding the full read-only token, and change its `NETBOX_TOKEN` line to read that file.

**4. Make new passwords**

Create new secrets for SNMP, InfluxDB and Grafana. Never reuse the lab ones.

**5. Decide how long to keep data**

Change `DOCKER_INFLUXDB_INIT_RETENTION` from `7d` to what your company needs.

**6. Add alerts**

No alerts exist yet. Add them before you rely on this.
