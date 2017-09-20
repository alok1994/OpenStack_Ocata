import pytest
import unittest
import json
import wapi_module
import re
import time
import util
import os
from netaddr import IPNetwork

tenant_name = 'admin'
network = 'net1'
updated_network_name = 'updated_net1'
subnet_name = "snet"
updated_subnet_name = 'updated_snet'
instance_name = 'inst'
updated_instance_name = 'updated_inst'
subnet = "10.2.0.0/24"
grid_ip = "10.39.12.121"
grid_master_name = "infoblox.localdomain"
custom_net_view = "openstack_view"
ext_network = "ext_net"
ext_subnet_name = "ext_sub"
ext_subnet = "10.39.12.0/24"
address_scope_name_ip4 = 'address_scope_ipv4'
address_scope_name_ip6 = 'address_scope_ipv6'
ip_version = [4,6]
address_scope_subnet_name_ipv4 = 'subnet-pool-ip4'
address_scope_subnet_name_ipv6 = 'subnet-pool-ip6'
address_scope_pool_prefix = '200.0.113.0/26'
address_scope_prefixlen = '26'

class TestOpenStackCases(unittest.TestCase):
    @classmethod
    def setup_class(cls):
	pass

    @pytest.mark.run(order=1)	
    def test_create_Network_disable_EAs_DHCPSupport_and_DNSSupport(self):
        proc = util.utils()
        proc.create_network(network)
	flag = proc.get_network(network)
	assert flag == network

    @pytest.mark.run(order=2)
    def test_create_subnet_disable_EAs_DHCPSupport_and_DNSSupport(self):
	proc = util.utils()
	proc.create_subnet(network, subnet_name, subnet)
	flag = proc.get_subnet_name(subnet_name)
	assert flag == subnet_name

    @pytest.mark.run(order=3)
    def test_deploy_instnace_HostNamePattern_as_HostIPAddress(self):
	proc = util.utils()
	proc.launch_instance(instance_name,network)
	instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
	assert instance_name == instance and \
               status == 'ACTIVE'

	
    @pytest.mark.run(order=4)
    def test_terminate_instance_HostNamePattern_as_HostIPAddress(self):
        proc = util.utils()
        proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None
'''
    @pytest.mark.run(order=5)	
    def test_create_Network_disable_EAs_DHCPSupport_and_DNSSupport(self):
        proc = util.utils()
        created_network = proc.create_network(network)
	assert created_network == network

    @pytest.mark.run(order=6)
    def test_update_network_name(self):
	proc = util.utils()
	modified_network = proc.update_network(network,updated_network_name)
	assert modified_network == updated_network_name

    @pytest.mark.run(order=7)
    def test_update_subnet_name(self):
        proc = util.utils()
        modified_subnet = proc.update_subnet(subnet_name,updated_subnet_name)
        assert modified_subnet == updated_subnet_name

    @pytest.mark.run(order=8)
    def test_update_instnace_name(self):
        proc = util.utils()
        modified_instance = proc.update_instance(updated_instance_name)
	flag = False
        instance_name = str(modified_instance)
        if (re.search(r""+updated_instance_name,instance_name)):
            flag = True
        assert flag
        #assert modified_instnace == updated_instance_name

    @pytest.mark.run(order=3)
    def test_get_server_name(self):
        proc = util.utils()
	instance = proc.get_server_name(instance_name)
	assert instance == instance_name
'''
