# small linux with python
FROM python:3.12-slim
# iproute2 gives the ip command, server.py uses it to add the device IPs
RUN apt-get update && apt-get install -y --no-install-recommends iproute2 && rm -rf /var/lib/apt/lists/*
# the fake snmp server, cryptography is needed for v3 encryption
RUN pip install --no-cache-dir snmpsim==1.2.2 pysmi==2.0.0 pyyaml==6.0.3 cryptography==50.0.2
WORKDIR /app
COPY server.py .
# starts as root to add IPs and open port 161, then snmpsim drops to user nobody
# -u shows print output in the logs right away
CMD ["python", "-u", "server.py"]
