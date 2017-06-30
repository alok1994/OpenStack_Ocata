import pytest
import unittest
import json
import wapi_module
import re
import time
import util
import os
from netaddr import IPNetwork
import commands
import os, subprocess as sp, json
import os, pickle

import subprocess

tenant_name = 'admin'
network = 'net1'
subnet_name = "snet"
instance_name = 'inst'
subnet = "10.2.0.0/24"
grid_ip = "10.39.12.121"
grid_master_name = "infoblox.localdomain"
custom_net_view = "openstack_view"
custom_DNS_view = "dns_view"

def source(fileName = None, username = None, password = None, update = True):
    pipe = sp.Popen(". {fileName} {username} {password}; env".format(
        fileName=fileName,
        username=username,
        password=password
    ), stdout = subprocess.PIPE, shell = True)
    data = pipe.communicate()[0]
    env = dict((line.split("=", 1) for line in data.splitlines() if (len(line.split("=", 1)) == 2)))
    print env
    if update is True:
        os.environ.update(env)
    return(env)


class TestOpenStackCases(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        # source("/opt/devstack/openrc", "admin", "admin")
        source("/home/stack/keystone_admin")
	pass 
	#cmd = '/bin/bash -c "source /opt/devstack/openrc admin admin"'
        #commands.getoutput(cmd)
        #command = ['bash', '-c', 'source /opt/devstack/openrc admin admin']
        #proc = subprocess.Popen(command, stdout = subprocess.PIPE)
        #for line in proc.stdout:
        #    (key, _, value) = line.partition("=")
        #    os.environ[key] = value
        #proc.communicate()
        #pprint.pprint(dict(os.environ)

    @pytest.mark.run(order=5)
    def test_RUNSource(self):
        
        #bash.execute('a-tool.sh --args')
	#cmd = 'export OS_USERNAME=admin'
        #cmd = 'source /opt/devstack/openrc admin admin'
        #os.system(cmd)
	#source = 'source /opt/devstack/openrc admin admin'
        #dump = '/usr/bin/python -c "import os, json;print json.dumps(dict(os.environ))"'
        #pipe = sp.Popen(['/bin/bash', '-c', '%s && %s' %(source,dump)], stdout=sp.PIPE)
        #env = json.loads(pipe.stdout.read())
        #os.environ = env
	pass

    @pytest.mark.run(order=6)
    def test_RUNSYNCTool_network_DomainNamePattern_as_TenantName_EAs_sync_tool(self):
        import os
        log = open('log.txt', 'w')
        print >> log, os.environ["OS_USERNAME"]
        # cmd = 'python /opt/stack/networking-infoblox/networking_infoblox/tools/sync_neutron_to_infoblox.py >> log.txt'
	# proc = commands.getoutput(cmd)
	# time.sleep(20)
	# import pdb;pdb.set_trace()
	a=open('log.txt','rb')
        lines = a.readlines()
        if lines:
           last_line = lines[-1]	

