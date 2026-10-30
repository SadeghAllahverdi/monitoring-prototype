FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends iproute2 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir snmpsim==1.2.2 pysmi==2.0.0 pyyaml==6.0.3 cryptography==50.0.2
WORKDIR /app
COPY server.py .
CMD ["python", "-u", "server.py"]