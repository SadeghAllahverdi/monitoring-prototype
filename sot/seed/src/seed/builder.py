import random

def run (netbox_instance, config):
    random.seed(42)
    #adding custom field to netbox for snmp profiles
    if netbox_instance.extras.custom_fields.get(name="snmp_profile") is None:
        netbox_instance.extras.custom_fields.create({"name": "snmp_profile", "label": "SNMP profile", "type": "text", "object_types": ["dcim.device"]})

    all_sites = []
    # adding region cols to netbox
    for rg, rg_sites in config["regions"].items():
        region = netbox_instance.dcim.regions.get(slug=rg.lower())
        if region is None:
            region = netbox_instance.dcim.regions.create({"name": rg, "slug": rg.lower()})
        # adding sites to netbox under each region
        for st in rg_sites:
            site = netbox_instance.dcim.sites.get(slug=st.lower())
            if site is None:
                site = netbox_instance.dcim.sites.create({"name": st, "slug": st.lower(), "region": region.id, "status": "active"})
            all_sites.append(site)

    type_role_pair = []
    # adding manufacturer cols to netbox
    for mf, dev_models in config["manufacturers"].items():
        manufacturer = netbox_instance.dcim.manufacturers.get(slug=mf.lower())
        if manufacturer is None:
            manufacturer = netbox_instance.dcim.manufacturers.create({"name": mf, "slug": mf.lower()})
        # adding device types under each manufacturer
        for model in dev_models:
            device_type = netbox_instance.dcim.device_types.get(slug=model.lower())
            if device_type is None:
                device_type = netbox_instance.dcim.device_types.create({"manufacturer": manufacturer.id, "model": model, "slug": model.lower()})
       
    # adding device role cols to the netbox
    for rl, dev_models in config["roles"].items():
        role = netbox_instance.dcim.device_roles.get(slug=rl.lower())
        if role is None:
            role = netbox_instance.dcim.device_roles.create({"name": rl, "slug": rl.lower()})

        for model in dev_models:
            device_type = netbox_instance.dcim.device_types.get(slug=model.lower())
            type_role_pair.append((device_type, role))

    # adding IP + prefix columns
    company_netwrk = netbox_instance.ipam.prefixes.get(prefix=config["ip_network"])
    if company_netwrk is None:
        company_netwrk = netbox_instance.ipam.prefixes.create({"prefix": config["ip_network"], "status": "container"})
    for site in all_sites:
        prefix = netbox_instance.ipam.prefixes.get(scope_type="dcim.site", scope_id=site.id)
        if prefix is None:
            company_netwrk.available_prefixes.create({"prefix_length": 24, "scope_type": "dcim.site", "scope_id": site.id, "status": "active"})

    profiles = config["snmp_profiles"]
    # filling in data to the columns
    for i in range(1, config["total_devices"] + 1):
        site = random.choice(all_sites) 
        device_type, role = random.choice(type_role_pair)
        profile = random.choices(list(profiles.keys()), weights=list(profiles.values()))[0]
        interface_count = random.randint(config["interface_per_device"]["min"], config["interface_per_device"]["max"])

        name = f"{site.slug}-{i:03d}"
        device = netbox_instance.dcim.devices.get(name=name)
        if device is None:
            device = netbox_instance.dcim.devices.create({"name": name, "site": site.id, "device_type": device_type.id, "role": role.id, "status": "active", "custom_fields": {"snmp_profile": profile}})

        for n in range(1, interface_count + 1):
            if netbox_instance.dcim.interfaces.get(device_id=device.id, name=f"eth{n}") is None:
                netbox_instance.dcim.interfaces.create({"device": device.id, "name": f"eth{n}", "type": "1000base-t"})

        mgmt = netbox_instance.dcim.interfaces.get(device_id=device.id, name="mgmt0")
        if mgmt is None:
            mgmt = netbox_instance.dcim.interfaces.create({"device": device.id, "name": "mgmt0", "type": "1000base-t", "mgmt_only": True})

        if device.primary_ip4 is None:
            prefix = netbox_instance.ipam.prefixes.get(scope_type="dcim.site", scope_id=site.id)
            ip = prefix.available_ips.create({"assigned_object_type": "dcim.interface", "assigned_object_id": mgmt.id, "status": "active"})
            device.update({"primary_ip4": ip.id})

        print(name, profile, interface_count)
