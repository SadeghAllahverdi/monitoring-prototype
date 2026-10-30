import os
import pynetbox
from dotenv import load_dotenv
from snmp_sim.simulate import run

load_dotenv()

url = os.environ["NETBOX_URL"]
tkn = os.environ["NETBOX_TOKEN"]
nb = pynetbox.api(url=url, token=tkn)

def main() -> None:
    print("Hello from snmp-sim!")
    status= nb.status()
    print(f"Testing connection to netbox: {status["netbox-version"]}")
    run(nb)

