import os
import pynetbox
from dotenv import load_dotenv
from telegraf_config_gen.generate import run


def main() -> None:
    load_dotenv()
    nb = pynetbox.api(url=os.environ["NETBOX_URL"], token=os.environ["NETBOX_TOKEN"])
    print(f"Testing connection to netbox: {nb.status()["netbox-version"]}")
    run(nb)
