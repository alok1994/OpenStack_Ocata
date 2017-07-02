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
        source("/home/stack/keystone_admin")
	pass 

    @pytest.mark.run(order=6)
    def test_RUNSYNCTool_network_DomainNamePattern_as_TenantName_EAs_sync_tool(self):
	#os.system('rm -rf log.txt')
        cmd = 'python /opt/stack/networking-infoblox/networking_infoblox/tools/sync_neutron_to_infoblox.py > log.txt'
	proc = commands.getoutput(cmd)
	a=open('log.txt','rb')
        lines = a.readlines()
        if lines:
           last_line = lines[-1]
	migration = last_line.find('Ending migration...')
	flag = True
	if migration < 1:
 	    flag = False
	assert flag

