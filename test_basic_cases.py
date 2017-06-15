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
subnet_name = "Snet"
instance_name = 'inst'
subnet = "10.2.0.0/24"
grid_ip = "10.39.12.233"
grid_master_name = "infoblox.localdomain"


class TestOpenStackCases(unittest.TestCase):
    @classmethod
    def setup_class(cls):
	pass

    @pytest.mark.run(order=1)	
    def test_create_Network_OpenStack_Side(self):
        proc = util.utils()
        proc.create_network(network)
	flag = proc.get_network(network)
	assert flag == network

    @pytest.mark.run(order=2)
    def test_create_subnet_openstack_side(self):
	proc = util.utils()
	proc.create_subnet(network, subnet_name, subnet)
	flag = proc.get_subnet_name(subnet_name)
	assert flag == subnet_name

    @pytest.mark.run(order=3)
    def test_validate_network_on_NIOS(self):
	flag = False	
	proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
	if (re.search(r""+subnet,proc)):
	    flag = True
	assert flag, "Network creation failed "

    @pytest.mark.run(order=4)
    def test_validate_NIOS_EAs_Cloud_API_Owned_CMP_Type(self):
	proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
	resp = json.loads(proc)
	ref_v = resp[0]['_ref']
	EAs = json.loads(wapi_module.wapi_request('GET',object_type = ref_v + '?_return_fields=extattrs'))
	assert EAs['extattrs']['Cloud API Owned']['value'] == 'True' and EAs['extattrs']['CMP Type']['value'] == 'OpenStack'

    @pytest.mark.run(order=5)
    def test_Validate_NIOS_EAs_Network_Name_Network_ID_Subnet_Name_Subnet_ID(self):
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
	session = util.utils()
	Net_name = session.get_network(network)
	Net_id = session.get_network_id(network)
	Sub_name = session.get_subnet_name(subnet_name)
	Snet_ID = session.get_subnet_id(subnet_name)
	resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        EAs = json.loads(wapi_module.wapi_request('GET',object_type = ref_v + '?_return_fields=extattrs'))
        assert EAs['extattrs']['Network Name']['value'] == Net_name and \
               EAs['extattrs']['Network ID']['value'] == Net_id and \
               EAs['extattrs']['Subnet Name']['value'] == Sub_name and \
               EAs['extattrs']['Subnet ID']['value'] == Snet_ID and \
               EAs['extattrs']['Network Encap']['value'] == 'vxlan' 

    @pytest.mark.run(order=6)
    def test_validate_NIOS_EAs_Tenant_ID_Tenant_Name(self):
	proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
        session = util.utils()
        tenant_id = session.get_tenant_id(network)
	resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        EAs = json.loads(wapi_module.wapi_request('GET',object_type = ref_v + '?_return_fields=extattrs'))
        assert EAs['extattrs']['Tenant ID']['value'] == tenant_id and \
	       EAs['extattrs']['Tenant Name']['value'] == 'admin'

    @pytest.mark.run(order=7)
    def test_validate_NIOS_Router(self):
	proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
	resp = json.loads(proc)
        ref_v = resp[0]['_ref']
	options = json.loads(wapi_module.wapi_request('GET',object_type = ref_v + '?_return_fields=options'))
	route_list = options['options']
	list_route = route_list[1]
	route_nios = list_route['value']
	ip = IPNetwork(subnet).iter_hosts()
        route = str(ip.next())
	assert route_nios == route

    @pytest.mark.run(order=8)
    def test_delete_net_subnet_openstack_side(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == None

    @pytest.mark.run(order=9)
    def test_validate_delete_network_on_NIOS(self):
        flag = True
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
        if (re.search(r""+subnet,proc)):
            flag = False
        assert flag, "Network didn't remove from NIOS "

    @pytest.mark.run(order=10)
    def test_enable_DHCP_DNS_support_Default_Domain_Name_Pattern_TENENT_NAME_EAs(self):
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
                "Relay Support": {"value": "False"},\
                "Report Grid Sync Time": {"value": "True"},\
                "Tenant Name Persistence": {"value": "False"},\
                "Use Grid Master for DHCP": {"value": "True"},\
                "Zone Creation Strategy": {"value": ["Forward","Reverse"]}}} 
	proc = wapi_module.wapi_request('PUT',object_type=ref,fields=json.dumps(data))
	flag = False
        if (re.search(r"infoblox.localdomain",proc)):
            flag = True
        assert proc != "" and flag

    @pytest.mark.run(order=11)
    def test_create_network_DHCP_DNS_support_Domain_Name_TENANT_Name_openstack_side(self):
	proc = util.utils()
        proc.create_network(network)
	proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
	flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=12)
    def test_validate_member_assiged_network(self):
	resp = json.loads(wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet))
	ref_v = resp[0]['_ref']
	members = json.loads(wapi_module.wapi_request('GET',object_type = ref_v+'?_return_fields=members'))
	name = members['members'][0]['name']
	assert grid_master_name == name, "Member has not been assign to Netwrok"
	
    @pytest.mark.run(order=13)
    def test_validate_zone_name(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	zone_name = ref_v[0]['fqdn']
	assert tenant_name+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=14)
    def test_validate_zone_EAs(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        ref = ref_v[0]['_ref']
	EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=extattrs'))
	tenant_name_nios = EAs['extattrs']['Tenant Name']['value']
	tenant_id_nios = EAs['extattrs']['Tenant ID']['value']		
	cmp_type_nios = EAs['extattrs']['CMP Type']['value']
	cloud_api_owned_nios = EAs['extattrs']['Cloud API Owned']['value']
	session = util.utils()
        tenant_id_openstack = session.get_tenant_id(network)
	assert tenant_id_openstack == tenant_id_nios and \
               tenant_name_nios == tenant_name and \
	       cmp_type_nios == 'OpenStack' and \
	       cloud_api_owned_nios == 'True'

	# EAs 'Default Host Name Pattern': host-{ip_address}
    @pytest.mark.run(order=15)
    def test_deploy_instnace_host_name_pattern_host_ip_address(self):
	proc = util.utils()
	proc.launch_instance(instance_name,network)
	instance = proc.get_server_name(instance_name)
	assert instance_name == instance
		
