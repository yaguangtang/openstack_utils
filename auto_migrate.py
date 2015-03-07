#!/usr/bin/python

import random
import daemon
import json
import syslog
import time

from novaclient import client as nova_cient
from ceilometerclient import client as meter_client 
from bottle import route, run,get, post, request


auth_url='http://172.16.0.5:35357/v2.0'
admin_pass='********'


def get_nova_client():
    cred=dict(username='admin',
              api_key=admin_pass,
              project_id='admin',
              auth_url=auth_url)
    n_client = nova_cient.Client('1.1', **cred)
    return n_client

def get_meter_client():
    cred=dict(os_username='admin',
              os_password=admin_pass,
              os_tenant_name='admin',
              os_auth_url=auth_url)
    n_client = meter_client.get_client('2', **cred)
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


def migrate_instances(hot_host):
    """Migrate instance to reduce server load."""
    search_opts = {'all_tenants': 1}
    client = get_nova_client()
    if hot_host:
        instances = client.servers.list(search_opts=search_opts)
        for instance in instances:
            host = instance.__dict__['OS-EXT-SRV-ATTR:host']
            if host == hot_host:
                client.servers.live_migrate(instance.id, None,
                                            False, False)
                break
        
@post('/cpu')
def trigger_cpu():
    print request.forms.__dict__
    alarm_id = json.loads(request.forms.keys()[0]).get('alarm_id')
    reason = json.loads(request.forms.keys()[0]).get('reason_data')
    meter_client = get_meter_client()
    print dir(meter_client)
    return "Hello World!"

#with daemon.DaemonContext():
if __name__ == "__main__":
    meter_client = get_meter_client()
    alarm = meter_client.alarms.get('f3154fd0-cdf6-43f9-8d0f-f55a5e31011f')
    host = str(alarm.threshold_rule['query'][0]['value'])
    migrate_instances(host)
run(host='localhost', port=6000, debug=True)
