#!/usr/bin/python

import random
import daemon
import time

from novaclient import client as nova_cient


auth_url='http://172.16.0.5:35357/v2.0'
admin_pass='beyond630'


def get_nova_client():
    cred=dict(username='admin',
              api_key=admin_pass,
              project_id='admin',
              auth_url=auth_url)
    n_client = nova_cient.Client('1.1', **cred)
    return n_client


def check_server(state='down'):
    """Return servers that is down."""
    hosts = []
    client = get_nova_client()
    servers = client.services.list(binary='nova-compute')
    for server in servers:
        if server.state == state:
            hosts.append(server.host)
    return hosts


def evacuate_instances():
    """Return instances uuid if HA meta set."""
    search_opts = {'all_tenants': 1}
    client = get_nova_client()
    down_hosts = check_server()
    up_hosts = check_server(state='up')
    if down_hosts:
        instances = client.servers.list(search_opts=search_opts)
        for instance in instances:
            host = instance.__dict__['OS-EXT-SRV-ATTR:host']
            if (instance.metadata.get('instance_ha') and
                host in down_hosts):
                target_host = random.choice(up_hosts)
                client.servers.evacuate(instance.id,
                                        target_host, True)
        

with daemon.DaemonContext():
    while(1):
        time.sleep(5)
        evacuate_instances()
