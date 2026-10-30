# small linux with python
FROM python:3.13-slim
# same package versions as uv.lock
RUN pip install --no-cache-dir pynetbox==7.9.0 python-dotenv==1.2.4
# non-root user
RUN useradd --uid 1000 --create-home app
# same folders as the repo, so Path(__file__) still works
COPY src /snmp-sim/src
# where python finds the code
ENV PYTHONPATH=/snmp-sim/src
# show print output in the logs right away
ENV PYTHONUNBUFFERED=1
USER app
