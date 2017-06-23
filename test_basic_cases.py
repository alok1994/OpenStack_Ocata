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


class TestOpenStackCases(unittest.TestCase):
    @classmethod
    def setup_class(cls):
	pass

    @pytest.mark.run(order=1)
    def test_disable_DHCP_DNS_support(self):
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
                "Relay Support": {"value": "False"},\
                "Report Grid Sync Time": {"value": "True"},\
                "Tenant Name Persistence": {"value": "False"},\
                "Use Grid Master for DHCP": {"value": "True"},\
                "Zone Creation Strategy": {"value": ["Forward","Reverse"]}}}
        proc = wapi_module.wapi_request('PUT',object_type=ref,fields=json.dumps(data))
        flag = False
        if (re.search(r""+grid_master_name,proc)):
            flag = True
        assert proc != "" and flag

    @pytest.mark.run(order=2)	
    def test_create_Network_OpenStack_Side(self):
        proc = util.utils()
        proc.create_network(network)
	flag = proc.get_network(network)
	assert flag == network

    @pytest.mark.run(order=3)
    def test_create_subnet_openstack_side(self):
	proc = util.utils()
	proc.create_subnet(network, subnet_name, subnet)
	flag = proc.get_subnet_name(subnet_name)
	assert flag == subnet_name

    @pytest.mark.run(order=4)
    def test_validate_network_on_NIOS(self):
	flag = False	
	proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
	if (re.search(r""+subnet,proc)):
	    flag = True
	assert flag, "Network creation failed "

    @pytest.mark.run(order=5)
    def test_validate_NIOS_EAs_Cloud_API_Owned_CMP_Type(self):
	proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
	resp = json.loads(proc)
	ref_v = resp[0]['_ref']
	EAs = json.loads(wapi_module.wapi_request('GET',object_type = ref_v + '?_return_fields=extattrs'))
	assert EAs['extattrs']['Cloud API Owned']['value'] == 'True' and EAs['extattrs']['CMP Type']['value'] == 'OpenStack'

    @pytest.mark.run(order=6)
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

    @pytest.mark.run(order=7)
    def test_validate_NIOS_EAs_Tenant_ID_Tenant_Name(self):
	proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
        session = util.utils()
        tenant_id = session.get_tenant_id(network)
	resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        EAs = json.loads(wapi_module.wapi_request('GET',object_type = ref_v + '?_return_fields=extattrs'))
        assert EAs['extattrs']['Tenant ID']['value'] == tenant_id and \
	       EAs['extattrs']['Tenant Name']['value'] == 'admin'

    @pytest.mark.run(order=8)
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

    @pytest.mark.run(order=9)
    def test_delete_net_subnet_openstack_side(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == None

    @pytest.mark.run(order=10)
    def test_validate_delete_network_on_NIOS(self):
        flag = True
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
        if (re.search(r""+subnet,proc)):
            flag = False
        assert flag, "Network didn't remove from NIOS "

    @pytest.mark.run(order=11)
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
        if (re.search(r""+grid_master_name,proc)):
            flag = True
        assert proc != "" and flag

    @pytest.mark.run(order=12)
    def test_create_network_DHCP_DNS_support_Domain_Name_TENANT_Name_openstack_side(self):
	proc = util.utils()
        proc.create_network(network)
	proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
	flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=13)
    def test_validate_member_assiged_network(self):
	resp = json.loads(wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet))
	ref_v = resp[0]['_ref']
	members = json.loads(wapi_module.wapi_request('GET',object_type = ref_v+'?_return_fields=members'))
	name = members['members'][0]['name']
	assert grid_master_name == name, "Member has not been assign to Netwrok"
	
    @pytest.mark.run(order=14)
    def test_validate_zone_name(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	zone_name = ref_v[0]['fqdn']
	assert tenant_name+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=15)
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
    @pytest.mark.run(order=16)
    def test_deploy_instnace_host_name_pattern_host_ip_address(self):
	proc = util.utils()
	proc.launch_instance(instance_name,network)
	instance = proc.get_server_name()
        status = proc.get_server_status()
	assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=17)
    def test_validate_a_record_for_instance(self):
	ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	zone_name = ref_v_zone[0]['fqdn']
	ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
	a_record_name = ref_v_a_record[0]['name']
	proc = util.utils()
	ip_add = proc.get_instance_ips(instance_name)
	ip_address = ip_add[network][0]['addr']
	fqdn = "host-"+'-'.join(ip_address.split('.'))+'.'+zone_name
	assert fqdn == a_record_name

    @pytest.mark.run(order=18)
    def test_validate_a_record_EAs(self):
        a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
        ref_v = a_record[0]['_ref']
        EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref_v+'?_return_fields=extattrs'))
        vm_name_nios = EAs['extattrs']['VM Name']['value']
        vm_id_nios = EAs['extattrs']['VM ID']['value']
        tenant_name_nios = EAs['extattrs']['Tenant Name']['value']
        tenant_id_nios = EAs['extattrs']['Tenant ID']['value']
        port_id_nios = EAs['extattrs']['Port ID']['value']
        ip_type_nios = EAs['extattrs']['IP Type']['value']
        device_id_nios = EAs['extattrs']['Port Attached Device - Device ID']['value']
        device_owner_nios = EAs['extattrs']['Port Attached Device - Device Owner']['value']
        cmp_type_nios = EAs['extattrs']['CMP Type']['value']
        cloud_api_owned = EAs['extattrs']['Cloud API Owned']['value']
        proc = util.utils()
        vm_id_openstack = proc.get_servers_id()
        vm_name_openstack = proc.get_server_name()
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[network][0]['addr']
        port_list_openstack = proc.list_ports()
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'compute:None':
            port_id_openstack = port_list_openstack['ports'][0]['id']
            device_id_openstack = port_list_openstack['ports'][0]['device_id']
	    device_owner_opstk = 'compute:None'
        else:
            port_id_openstack = port_list_openstack['ports'][1]['id']
            device_id_openstack = port_list_openstack['ports'][1]['device_id']
	    device_owner_opstk = 'compute:None'
        assert vm_name_nios == vm_name_openstack and \
               vm_id_nios == vm_id_openstack and \
               tenant_name_nios == tenant_name and \
               tenant_id_nios == vm_tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               ip_type_nios == 'Fixed' and \
               device_owner_opstk == device_owner_nios and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'True' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=19)
    def test_validate_host_record_entry(self):
	ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_name = host_records[0]['name']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'network:dhcp':
            ip_address = port_list_openstack['ports'][0]['fixed_ips'][0]['ip_address']
        else:
            ip_address = port_list_openstack['ports'][1]['fixed_ips'][0]['ip_address']

        host_record_openstack = "dhcp-port-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert host_record_name == host_record_openstack

    @pytest.mark.run(order=20)
    def test_validate_host_record_EAs(self):
	host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        ref_v = host_records[0]['_ref']
        EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref_v+'?_return_fields=extattrs'))
        tenant_id_nios = EAs['extattrs']['Tenant ID']['value']
        tenant_name_nios = EAs['extattrs']['Tenant Name']['value']
        port_id_nios = EAs['extattrs']['Port ID']['value']
        ip_type_nios = EAs['extattrs']['IP Type']['value']
        device_id_nios = EAs['extattrs']['Port Attached Device - Device ID']['value']
        device_owner_nios = EAs['extattrs']['Port Attached Device - Device Owner']['value']
        cmp_type_nios = EAs['extattrs']['CMP Type']['value']
        cloud_api_owned = EAs['extattrs']['Cloud API Owned']['value']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'network:dhcp':
             port_id_openstack = port_list_openstack['ports'][0]['id']
             tenant_id_openstack = port_list_openstack['ports'][0]['tenant_id']
             device_id_openstack = port_list_openstack['ports'][0]['device_id']
             device_owner_opstk = 'network:dhcp'
        else:
             port_id_openstack = port_list_openstack['ports'][1]['id']
             tenant_id_openstack = port_list_openstack['ports'][1]['tenant_id']
             device_id_openstack = port_list_openstack['ports'][1]['device_id']
             device_owner_opstk = 'network:dhcp'
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'True' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=21)
    def test_validate_host_record_mac_address(self):
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        mac_address_nios = host_records[0]['ipv4addrs'][0]['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'network:dhcp':
            mac_address_openstack = port_list_openstack['ports'][0]['mac_address']
        else:
            mac_address_openstack = port_list_openstack['ports'][1]['mac_address']

        assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=22)
    def test_validate_fixed_address_instance(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'compute:None':
            ip_address_opstk = port_list_openstack['ports'][0]['fixed_ips'][0]['ip_address']
	else: 
            ip_address_opstk = port_list_openstack['ports'][1]['fixed_ips'][0]['ip_address']

        assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=23)
    def test_validate_mac_address_fixed_address_instance(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        ref = ref_v[0]['_ref']
        mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=mac'))
        mac_add_nios = mac_add['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'compute:None':
            mac_address_openstack = port_list_openstack['ports'][0]['mac_address']
        else:
            mac_address_openstack = port_list_openstack['ports'][1]['mac_address']
        assert mac_add_nios == mac_address_openstack

    @pytest.mark.run(order=24)
    def test_validate_fixed_address_EAs(self):
        fixed_add = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        ref_v = fixed_add[0]['_ref']
        EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref_v+'?_return_fields=extattrs'))
        vm_name_nios = EAs['extattrs']['VM Name']['value']
        vm_id_nios = EAs['extattrs']['VM ID']['value']
        tenant_name_nios = EAs['extattrs']['Tenant Name']['value']
        tenant_id_nios = EAs['extattrs']['Tenant ID']['value']
        port_id_nios = EAs['extattrs']['Port ID']['value']
        ip_type_nios = EAs['extattrs']['IP Type']['value']
        device_id_nios = EAs['extattrs']['Port Attached Device - Device ID']['value']
        device_owner_nios = EAs['extattrs']['Port Attached Device - Device Owner']['value']
        cmp_type_nios = EAs['extattrs']['CMP Type']['value']
        cloud_api_owned = EAs['extattrs']['Cloud API Owned']['value']
        proc = util.utils()
        vm_id_openstack = proc.get_servers_id()
        vm_name_openstack = proc.get_server_name()
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[network][0]['addr']
        port_list_openstack = proc.list_ports()
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'compute:None':
            port_id_openstack = port_list_openstack['ports'][0]['id']
            device_id_openstack = port_list_openstack['ports'][0]['device_id']
            device_owner_opstk = 'compute:None'
        else:
            port_id_openstack = port_list_openstack['ports'][1]['id']
            device_id_openstack = port_list_openstack['ports'][1]['device_id']
            device_owner_opstk = 'compute:None'
        assert vm_name_nios == vm_name_openstack and \
               vm_id_nios == vm_id_openstack and \
               tenant_name_nios == tenant_name and \
               tenant_id_nios == vm_tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               ip_type_nios == 'Fixed' and \
               device_owner_opstk == device_owner_nios and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'True' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=25)
    def test_terminate_instance1(self):
        proc = util.utils()
        server = proc.terminate_instance()
        assert server == None

    @pytest.mark.run(order=26)
    def test_delete_net_subnet_openstack_side_Default_Host_Name_Pattern(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == None	

       # Default Domain Name Pattern : {network_name}.cloud.global.com
       # Default Host Name Pattern : host-{subnet_name}-{ip_address}
    @pytest.mark.run(order=27)
    def test_EAs_SubnetName_as_HostName_pattern_and_NetworkName_as_DomainName_pattern(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
	ref = ref_v[0]['_ref']
	data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value": "default"},\
                "Default Domain Name Pattern": {"value": "{network_name}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{subnet_name}-{ip_address}"},\
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
        if (re.search(r""+grid_master_name,proc)):
            flag = True
        assert proc != "" and flag

    @pytest.mark.run(order=28)
    def test_create_network_NetworkName_as_DomainName_Pattern_openstack_side(self):
	proc = util.utils()
        proc.create_network(network)
	proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
	flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=29)
    def test_validate_zone_name_NetworkName_as_DomainName_pattern(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	zone_name = ref_v[0]['fqdn']
	assert network+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=30)
    def test_deploy_instance_SubnetName_as_HostName_Pattern(self):
	proc = util.utils()
	proc.launch_instance(instance_name,network)
	instance = proc.get_server_name()
        status = proc.get_server_status()
	assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=31)
    def test_validate_A_Record_SubnetName_as_HostName_Pattern(self):
	ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	zone_name = ref_v_zone[0]['fqdn']
	ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
	a_record_name = ref_v_a_record[0]['name']
	proc = util.utils()
	ip_add = proc.get_instance_ips(instance_name)
	ip_address = ip_add[network][0]['addr']
	fqdn = "host-"+subnet_name+'-'+'-'.join(ip_address.split('.'))+'.'+zone_name
	assert fqdn == a_record_name

    @pytest.mark.run(order=32)
    def test_terminate_instance_used_SubnetName_as__HostName_pattern(self):
        proc = util.utils()
        server = proc.terminate_instance()
        assert server == None

    @pytest.mark.run(order=33)
    def test_delete_subnet_used_NetworkName_as_DomainName_pattern(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == None

    @pytest.mark.run(order=34)
    def test_EAs_NetworkID_as_DomainNamePattern_and_SubnetID_as_HostNamePattern(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        ref = ref_v[0]['_ref']
        data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value": "default"},\
                "Default Domain Name Pattern": {"value": "{network_id}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{subnet_id}-{ip_address}"},\
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
        if (re.search(r""+grid_master_name,proc)):
            flag = True
        assert proc != "" and flag

    @pytest.mark.run(order=35)
    def test_create_network_NetworkID_as_DomainNamePattern_and_SubnetID_as_HostNamePattern(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=36)
    def test_validate_zone_name_as_NetworkID_DomainNamePattern(self):
        proc = util.utils()
        network_id = proc.get_network_id(network)
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        assert network_id+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=37)
    def test_deploy_instance_SubnetID_as_HostNamePattern(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network)
        instance = proc.get_server_name()
        status = proc.get_server_status()
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=38)
    def test_validate_a_record_SubnetID_as_HostNamePattern(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
        a_record_name = ref_v_a_record[0]['name']
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        subnet_id = proc.get_subnet_id(subnet_name)
        fqdn = "host-"+subnet_id+'-'+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert fqdn == a_record_name

    @pytest.mark.run(order=39)
    def test_terminate_instance_used_NetworkID_as_DomainNamePattern_and_SubnetID_as_HostNamePattern(self):
        proc = util.utils()
        server = proc.terminate_instance()
        assert server == None

    @pytest.mark.run(order=40)
    def test_delete_subnet_used_NetworkID_as_DomainNamePattern(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == None

    #"Default Domain Name Pattern":"{subnet_name}.cloud.global.com"
    #"Default Host Name Pattern": "host-{network_name}-{ip_address}"
    @pytest.mark.run(order=41)
    def test_EAs_SubnetName_as_DomainNamePattern_and_NetworkName_as_HostNamePattern(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        ref = ref_v[0]['_ref']
        data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value": "default"},\
                "Default Domain Name Pattern": {"value": "{subnet_name}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{network_name}-{ip_address}"},\
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
        if (re.search(r""+grid_master_name,proc)):
            flag = True
        assert proc != "" and flag

    @pytest.mark.run(order=42)
    def test_create_network_SubnetName_as_DomainNamePattern_and_NetworkName_as_HostNamePattern(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=43)
    def test_validate_zone_name_as_SubnetName_DomainNamePattern(self):
        proc = util.utils()
        name_subnet = proc.get_subnet_name(subnet_name)
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        assert name_subnet+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=44)
    def test_deploy_instance_NetworkName_as_HostNamePattern(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network)
        instance = proc.get_server_name()
        status = proc.get_server_status()
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=45)
    def test_validate_a_record_NetworkName_as_HostNamePattern(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
        a_record_name = ref_v_a_record[0]['name']
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        network_name = proc.get_network(network)
        fqdn = "host-"+network_name+'-'+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert fqdn == a_record_name


