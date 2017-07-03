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
network_v6 = 'net_ipv6'
subnet_name_ipv6 = 'subnet_ipv6'
subnet_ipv6 = '1111::/64'
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
    def test_EAs_disable_DHCPSupport_and_DNSSupport_ipv6(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        ref = ref_v[0]['_ref']
        data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "False"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "False"},"DNS View": {"value": "default"},\
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
    def test_create_Network_disable_EAs_DHCPSupport_and_DNSSupport_ipv6(self):
        proc = util.utils()
        proc.create_network(network_v6)
	flag = proc.get_network(network_v6)
	assert flag == network_v6

    @pytest.mark.run(order=3)
    def test_create_subnet_disable_EAs_DHCPSupport_and_DNSSupport_ipv6(self):
	proc = util.utils()
	proc.create_subnet(network_v6, subnet_name_ipv6, subnet_ipv6, ip_version = 6)
	flag = proc.get_subnet_name(subnet_name_ipv6)
	assert flag == subnet_name_ipv6

    @pytest.mark.run(order=4)
    def test_validate_network_disable_EAs_DHCPSupport_and_DNSSupport_ipv6(self):
	flag = False	
	proc = wapi_module.wapi_request('GET',object_type = 'ipv6network',params="?network="+subnet_ipv6)
	if (re.search(r""+subnet_ipv6,proc)):
	    flag = True
	assert flag, "Network creation failed "

    @pytest.mark.run(order=5)
    def test_validate_network_EAs_disable_EAs_DHCPSupport_and_DNSSupport_ipv6(self):
        session = util.utils()
        net_name = session.get_network(network_v6)
        net_id = session.get_network_id(network_v6)
        sub_name = session.get_subnet_name(subnet_name_ipv6)
        snet_ID = session.get_subnet_id(subnet_name_ipv6)
        tenant_id = session.get_tenant_id(network_v6)
        proc = wapi_module.wapi_request('GET',object_type = 'ipv6network',params="?network="+subnet_ipv6)
        resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        EAs = json.loads(wapi_module.wapi_request('GET',object_type = ref_v + '?_return_fields=extattrs'))
        assert EAs['extattrs']['Network Name']['value'] == net_name and \
               EAs['extattrs']['Network ID']['value'] == net_id and \
               EAs['extattrs']['Subnet Name']['value'] == sub_name and \
               EAs['extattrs']['Subnet ID']['value'] == snet_ID and \
               EAs['extattrs']['Network Encap']['value'] == 'vxlan' and \
               EAs['extattrs']['Cloud API Owned']['value'] == 'True' and \
               EAs['extattrs']['Tenant Name']['value'] == tenant_name
