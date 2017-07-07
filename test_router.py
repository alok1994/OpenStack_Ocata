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
subnet_name = "snet"
instance_name = 'inst'
subnet = "10.2.0.0/24"
grid_ip = "10.39.12.121"
grid_master_name = "infoblox.localdomain"
custom_net_view = "openstack_view"
network_ipv6 = 'net_ipv6'
subnet_name_ipv6 = 'subnet_ipv6'
subnet_ipv6 = '1113::/64'
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
router_name = 'router'
interface_name = 'interface_name'

class TestOpenStackCases(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        pass

    @pytest.mark.run(order=1)
    def test_select_EAs_ExternalDomainNamePattern_as_SubnetID_and_ExternalHostNamePattern_as_InstanceName_router(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        ref = ref_v[0]['_ref']
        data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value": "default"},\
                "Default Domain Name Pattern": {"value": "{tenant_name}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{ip_address}"},\
                "Default Network View": {"value": "default"},\
                "Default Network View Scope": {"value": "Single"},\
                "External Domain Name Pattern": {"value": "{subnet_id}.external.global.com"},\
                "External Host Name Pattern": {"value": "{instance_name}"},\
                "Grid Sync Maximum Wait Time": {"value": 10},\
                "Grid Sync Minimum Wait Time": {"value": 10},"Grid Sync Support": {"value": "True"},\
                "IP Allocation Strategy": {"value": "Fixed Address"},\
                "Relay Support": {"value": "True"},\
                "Report Grid Sync Time": {"value": "True"},\
                "Tenant Name Persistence": {"value": "True"},\
                "Use Grid Master for DHCP": {"value": "True"},\
                "Zone Creation Strategy": {"value": ["Forward","Reverse"]}}}
        proc = wapi_module.wapi_request('PUT',object_type=ref,fields=json.dumps(data))
        flag = False
        if (re.search(r""+grid_master_name,proc)):
            flag = True
        assert proc != "" and flag

    @pytest.mark.run(order=2)
    def test_create_network_external_network_for_router(self):
        proc = util.utils()
        proc.create_network(ext_network, external = True, shared = True)
        proc.create_subnet(ext_network, ext_subnet_name, ext_subnet)
        flag = proc.get_subnet_name(ext_subnet_name)
        flag = proc.get_subnet_name(ext_subnet_name)
        assert flag == ext_subnet_name

    @pytest.mark.run(order=3)
    def test_add_Router_with_ExternalNetwork(self):
	proc = util.utils()
	proc.create_router(router_name,ext_network)
	router = proc.get_routers_name(router_name)
	assert router_name == router

    @pytest.mark.run(order=4)
    def test_create_network_for_router(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=5)
    def test_add_InternalNetwork_to_router_interface(self):
	proc = util.utils()
	proc.add_router_interface(interface_name,router_name,subnet_name)
	router_opstk = proc.get_routers_name(router_name)
	assert router_opstk == router_name

    @pytest.mark.run(order=6)
    def test_deploy_instnace_router(self):
	proc = util.utils()
	proc.launch_instance(instance_name,network)
	instance = proc.get_server_name()
        status = proc.get_server_status()
	assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=7)
    def test_attach_floating_ip(self):
	proc = util.utils()
	proc.add_floating_ip(interface_name,instance_name,ext_network,ext_subnet_name)
	
