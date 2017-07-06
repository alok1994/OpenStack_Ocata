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
        proc.create_network(network_ipv6)
	flag = proc.get_network(network_ipv6)
	assert flag == network_ipv6

    @pytest.mark.run(order=3)
    def test_create_subnet_disable_EAs_DHCPSupport_and_DNSSupport_ipv6(self):
	proc = util.utils()
	proc.create_subnet(network_ipv6, subnet_name_ipv6, subnet_ipv6, ip_version = 6)
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
        net_name = session.get_network(network_ipv6)
        net_id = session.get_network_id(network_ipv6)
        sub_name = session.get_subnet_name(subnet_name_ipv6)
        snet_ID = session.get_subnet_id(subnet_name_ipv6)
        tenant_id = session.get_tenant_id(network_ipv6)
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

    @pytest.mark.run(order=6)
    def test_delete_net_subnet_disable_EAs_DHCPSupport_and_DNSSupport_ipv6(self):
        session = util.utils()
	delete_net = session.delete_network(network_ipv6)
	assert delete_net == None

    @pytest.mark.run(order=7)
    def test_select_True_DHCPSupport_DNSSupport_DomainNamePattern_as_TenantName_EAs_ipv6(self):
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

    @pytest.mark.run(order=8)
    def test_create_network_DefaultDomainNamePattern_as_TenantName_EAs_Ipv6(self):
	proc = util.utils()
        proc.create_network(network_ipv6)
	proc.create_subnet(network_ipv6, subnet_name_ipv6, subnet_ipv6,ip_version = 6)
        flag = proc.get_subnet_name(subnet_name_ipv6)
	flag = proc.get_subnet_name(subnet_name_ipv6)
        assert flag == subnet_name_ipv6

    @pytest.mark.run(order=9)
    def test_validate_member_assiged_network_DomainNamePattern_as_TenantName_EAs_IPv6(self):
	resp = json.loads(wapi_module.wapi_request('GET',object_type = 'ipv6network',params="?network="+subnet_ipv6))
	ref_v = resp[0]['_ref']
	members = json.loads(wapi_module.wapi_request('GET',object_type = ref_v+'?_return_fields=members'))
	name = members['members'][0]['name']
	assert grid_master_name == name, "Member has not been assign to Netwrok"

    @pytest.mark.run(order=10)
    def test_validate_zone_name_DomainNamePattern_as_TenantName_EAs_ipv6(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	zone_name = ref_v[0]['fqdn']
	assert tenant_name+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=11)
    def test_validate_zone_EAs_DomainNamePattern_as_TenantName_ipv6(self):
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

    @pytest.mark.run(order=12)
    def test_deploy_instnace_HostNamePattern_as_HostIPAddress_ipv6(self):
	proc = util.utils()
	proc.launch_instance(instance_name,network_ipv6)
	instance = proc.get_server_name()
        status = proc.get_server_status()
	assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=13)
    def test_validate_a_record_HostNamePattern_as_HostIPAddress_ipv6(self):
	ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	zone_name = ref_v_zone[0]['fqdn']
	ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:aaaa'))
	a_record_name = ref_v_a_record[0]['name']
	proc = util.utils()
	ip_add = proc.get_instance_ips(instance_name)
	ip_address = ip_add[network_ipv6][0]['addr']
	fqdn = "host-"+'--'.join(ip_address.split('::'))+'.'+zone_name
	assert fqdn == a_record_name

    @pytest.mark.run(order=14)
    def test_validate_a_record_EAs_HostNamePattern_as_HostIPAddress_ipv6(self):
        a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:aaaa'))
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
        inst_ip_address = ip_adds[network_ipv6][0]['addr']
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

    @pytest.mark.run(order=15)
    def test_validate_host_record_entry_ipv6(self):
	ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host_ipv6addr'))
        host_record_name = host_records[0]['host']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'network:dhcp':
            ip_address = port_list_openstack['ports'][0]['fixed_ips'][0]['ip_address']
        else:
            ip_address = port_list_openstack['ports'][1]['fixed_ips'][0]['ip_address']

        host_record_openstack = "dhcp-port-"+'--'.join(ip_address.split('::'))+'.'+zone_name
        assert host_record_name == host_record_openstack

    @pytest.mark.run(order=16)
    def test_validate_host_record_entry_mac_address_ipv6(self):
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host_ipv6addr'))
        mac_address_nios = host_records[0]['duid']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'network:dhcp':
            mac_address_openstack = port_list_openstack['ports'][0]['mac_address']
        else:
            mac_address_openstack = port_list_openstack['ports'][1]['mac_address']
	flag = False
	if (mac_address_nios.startswith(("00:")) and mac_address_nios.endswith((mac_address_openstack))):
	    flag = True
        assert flag

    @pytest.mark.run(order=17)
    def test_validate_fixed_address_HostNamePattern_as_HostIPAddress_ipv6(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='ipv6fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv6addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'compute:None':
            ip_address_opstk = port_list_openstack['ports'][0]['fixed_ips'][0]['ip_address']
	else: 
            ip_address_opstk = port_list_openstack['ports'][1]['fixed_ips'][0]['ip_address']
	assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=18)
    def test_validate_mac_address_fixed_address_instance_HostNamePattern_as_HostIPAddress_ipv6(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='ipv6fixedaddress'))
        ref = ref_v[0]['_ref']
        mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=duid'))
        mac_add_nios = mac_add['duid']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'compute:None':
            mac_address_openstack = port_list_openstack['ports'][0]['mac_address']
        else:
            mac_address_openstack = port_list_openstack['ports'][1]['mac_address']
        flag = False
        if (mac_add_nios.startswith(("00:")) and mac_add_nios.endswith((mac_address_openstack))):
            flag = True
        assert flag

    @pytest.mark.run(order=19)
    def test_validate_fixed_address_EAs_HostNamePattern_as_HostIPAddress_ipv6(self):
        fixed_add = json.loads(wapi_module.wapi_request('GET',object_type='ipv6fixedaddress'))
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
        inst_ip_address = ip_adds[network_ipv6][0]['addr']
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

    @pytest.mark.run(order=20)
    def test_terminate_instance_HostNamePattern_as_HostIPAddress_ipv6(self):
        proc = util.utils()
        server = proc.terminate_instance()
        assert server == None

    @pytest.mark.run(order=21)
    def test_delete_net_subnet_HostNamePattern_as_HostIPAddress_ipv6(self):
        session = util.utils()
	delete_net = session.delete_network(network_ipv6)
	assert delete_net == None
	
    @pytest.mark.run(order=22)
    def test_EAs_SubnetName_as_HostName_pattern_and_NetworkName_as_DomainName_pattern_ipv6(self):
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

    @pytest.mark.run(order=23)
    def test_create_network_NetworkName_as_DomainName_Pattern_openstack_side_ipv6(self):
	proc = util.utils()
        proc.create_network(network_ipv6)
	proc.create_subnet(network_ipv6, subnet_name_ipv6, subnet_ipv6,ip_version = 6)
        flag = proc.get_subnet_name(subnet_name_ipv6)
	flag = proc.get_subnet_name(subnet_name_ipv6)
        assert flag == subnet_name_ipv6

    @pytest.mark.run(order=24)
    def test_validate_zone_name_NetworkName_as_DomainName_pattern_ipv6(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	zone_name = ref_v[0]['fqdn']
	assert network_ipv6+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=25)
    def test_deploy_instance_SubnetName_as_HostName_Pattern_ipv6(self):
	proc = util.utils()
	proc.launch_instance(instance_name,network_ipv6)
	instance = proc.get_server_name()
        status = proc.get_server_status()
	assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=26)
    def test_validate_A_Record_SubnetName_as_HostName_Pattern_ipv6(self):
	ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	zone_name = ref_v_zone[0]['fqdn']
	ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:aaaa'))
	a_record_name = ref_v_a_record[0]['name']
	proc = util.utils()
	ip_add = proc.get_instance_ips(instance_name)
	ip_address = ip_add[network_ipv6][0]['addr']
	fqdn = "host-"+subnet_name_ipv6+'-'+'--'.join(ip_address.split('::'))+'.'+zone_name
	assert fqdn == a_record_name

    @pytest.mark.run(order=27)
    def test_terminate_instance_used_SubnetName_as__HostName_pattern_ipv6(self):
        proc = util.utils()
        server = proc.terminate_instance()
        assert server == None

    @pytest.mark.run(order=28)
    def test_delete_subnet_used_NetworkName_as_DomainName_pattern_ipv6(self):
        session = util.utils()
	delete_net = session.delete_network(network_ipv6)
	assert delete_net == None

    @pytest.mark.run(order=29)
    def test_EAs_NetworkID_as_DomainNamePattern_and_SubnetID_as_HostNamePattern_ipv6(self):
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

    @pytest.mark.run(order=30)
    def test_create_network_NetworkID_as_DomainNamePattern_and_SubnetID_as_HostNamePattern_ipv6(self):
        proc = util.utils()
        proc.create_network(network_ipv6)
        proc.create_subnet(network_ipv6, subnet_name_ipv6, subnet_ipv6,ip_version=6)
        flag = proc.get_subnet_name(subnet_name_ipv6)
        flag = proc.get_subnet_name(subnet_name_ipv6)
        assert flag == subnet_name_ipv6

    @pytest.mark.run(order=31)
    def test_validate_zone_name_as_NetworkID_DomainNamePattern_ipv6(self):
        proc = util.utils()
        network_id = proc.get_network_id(network_ipv6)
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        assert network_id+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=32)
    def test_deploy_instance_SubnetID_as_HostNamePattern_ipv6(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network_ipv6)
        instance = proc.get_server_name()
        status = proc.get_server_status()
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=33)
    def test_validate_aaaa_record_SubnetID_as_HostNamePattern_ipv6(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:aaaa'))
        a_record_name = ref_v_a_record[0]['name']
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network_ipv6][0]['addr']
        subnet_id = proc.get_subnet_id(subnet_name_ipv6)
        fqdn = "host-"+subnet_id+'-'+'--'.join(ip_address.split('::'))+'.'+zone_name
        assert fqdn == a_record_name

    @pytest.mark.run(order=34)
    def test_terminate_instance_used_NetworkID_as_DomainNamePattern_and_SubnetID_as_HostNamePattern_ipv6(self):
        proc = util.utils()
        server = proc.terminate_instance()
        assert server == None

    @pytest.mark.run(order=35)
    def test_delete_subnet_used_NetworkID_as_DomainNamePattern_ipv6(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == None

    @pytest.mark.run(order=36)
    def test_EAs_SubnetName_as_DomainNamePattern_and_NetworkName_as_HostNamePattern_ipv6(self):
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

    @pytest.mark.run(order=37)
    def test_create_network_SubnetName_as_DomainNamePattern_and_NetworkName_as_HostNamePattern_ipv6(self):
        proc = util.utils()
        proc.create_network(network_ipv6)
        proc.create_subnet(network_ipv6, subnet_name_ipv6, subnet_ipv6,ip_version=6)
        flag = proc.get_subnet_name(subnet_name_ipv6)
        flag = proc.get_subnet_name(subnet_name_ipv6)
        assert flag == subnet_name_ipv6

    @pytest.mark.run(order=38)
    def test_validate_zone_name_as_SubnetName_DomainNamePattern_ipv6(self):
        proc = util.utils()
        name_subnet = proc.get_subnet_name(subnet_name_ipv6)
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        assert name_subnet+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=39)
    def test_deploy_instance_NetworkName_as_HostNamePattern_ipv6(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network_ipv6)
        instance = proc.get_server_name()
        status = proc.get_server_status()
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=40)
    def test_validate_a_record_NetworkName_as_HostNamePattern(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:aaaa'))
        a_record_name = ref_v_a_record[0]['name']
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network_ipv6][0]['addr']
        network_name = proc.get_network(network_ipv6)
        fqdn = "host-"+network_name+'-'+'--'.join(ip_address.split('::'))+'.'+zone_name
        assert fqdn == a_record_name
