# Monitoring Prototype

NetBox holds the devices. A simulator fakes them, Telegraf polls them, InfluxDB stores the data and Grafana shows it. There are 50 fake devices, because my laptop is small.

## Run it

You only need Docker Desktop.

```powershell
docker compose up -d --build
```

First start takes about 5 minutes. To stop it: `docker compose down`. Adding `-v` wipes the data.

- Grafana: http://127.0.0.1:3000/d/germany-noc (password in `vis/grafana/secrets/admin-password.txt`)
- InfluxDB: http://127.0.0.1:8086 (password in `vis/influxdb/secrets/admin-password.txt`)
- NetBox: http://127.0.0.1:8000 (password in `sot/netbox-docker/secrets/superuser_password.txt`)

The user is `admin` everywhere.

Secrets and `sot/netbox-docker` are not in git, so a plain clone won't start.

## For production

1. Remove the simulation lines in `docker-compose.yml`.
2. Follow the note at the top of `docker-compose.override.yml`.
3. In `vis/telegraf/docker-compose.yml`, remove `snmp-lab` and set `NETBOX_URL` to the real NetBox.
4. In `vis/snmp-bucket/profiles.yaml`, remove the `context_name` lines.
5. Make 3 tokens: read-only NetBox for the generator, write-only InfluxDB for Telegraf, read-only InfluxDB for Grafana. The generator's token setup in `vis/telegraf/docker-compose.yml` has to change, because it reads lab secrets.
6. Make new passwords, and set the InfluxDB retention.
