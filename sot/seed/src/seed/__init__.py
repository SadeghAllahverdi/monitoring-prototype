import os
import yaml
import pynetbox
from dotenv import load_dotenv
# importing the builder
from seed.builder import run

load_dotenv()

url = os.environ["NETBOX_URL"]
tkn = os.environ["NETBOX_TOKEN"]
nb = pynetbox.api(url=url, token=tkn)




def main() -> None:
    print("Hello from seed!")
    status = nb.status()
    print(f"Testing connection to netbox: {status["netbox-version"]}")
    print("looping over regions")
    with open("sot/seed/seed.yaml", encoding="utf-8") as f:
        conf= yaml.safe_load(f)
        run(netbox_instance=nb, config=conf)
        
