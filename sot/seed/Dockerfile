# small linux with python
FROM python:3.13-slim
# same package versions as uv.lock
RUN pip install --no-cache-dir pynetbox==7.9.0 python-dotenv==1.2.4 pyyaml==6.0.3
# non-root user
RUN useradd --uid 1000 --create-home app
# seed.py opens sot/seed/seed.yaml, so run from a folder like the repo root
WORKDIR /repo
COPY src sot/seed/src
COPY seed.yaml sot/seed/seed.yaml
# where python finds the code
ENV PYTHONPATH=/repo/sot/seed/src
# show print output in the logs right away
ENV PYTHONUNBUFFERED=1
USER app
