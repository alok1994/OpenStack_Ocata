import pytest
import unittest
import json
import wapi_module
import re
import time
import util
import os
from netaddr import IPNetwork
import ConfigParser



CONF="config.ini"
parser = ConfigParser.SafeConfigParser()
parser.read(CONF)
grid_ip = parser.get('Default', 'Grid_VIP')
grid_master_name = parser.get('Default', 'Master_Domain_Name')
tenant_name = 'admin'
network = 'net1'
subnet_name = "snet"
instance_name = 'inst'
subnet = "10.2.0.0/24"
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
    def test_EAs_disable_DHCPSupport_and_DNSSupport(self):
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
    def test_create_Network_disable_EAs_DHCPSupport_and_DNSSupport(self):
        proc = util.utils()
        proc.create_network(network)
	flag = proc.get_network(network)
	assert flag == network

    @pytest.mark.run(order=3)
    def test_create_subnet_disable_EAs_DHCPSupport_and_DNSSupport(self):
	proc = util.utils()
	proc.create_subnet(network, subnet_name, subnet)
	flag = proc.get_subnet_name(subnet_name)
	assert flag == subnet_name

    @pytest.mark.run(order=4)
    def test_validate_network_disable_EAs_DHCPSupport_and_DNSSupport(self):
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
	route_nios = ''
        route_list = ''
	proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
	resp = json.loads(proc)
        ref_v = resp[0]['_ref']
	options = json.loads(wapi_module.wapi_request('GET',object_type = ref_v + '?_return_fields=options'))
	route_list = options['options']
	for l in range(len(route_list)):
	     router  = route_list[l]
	     route_name = router['name']
	     if route_name == 'routers':	    
		route_nios = router['value']
	ip = IPNetwork(subnet).iter_hosts()
        route = str(ip.next())
	assert route_nios == route

    @pytest.mark.run(order=9)
    def test_delete_net_subnet_disable_EAs_DHCPSupport_and_DNSSupport(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == ()

    @pytest.mark.run(order=10)
    def test_validate_delete_network_disable_EAs_DHCPSupport_and_DNSSupport(self):
        flag = True
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
        if (re.search(r""+subnet,proc)):
            flag = False
        assert flag, "Network didn't remove from NIOS "

    @pytest.mark.run(order=11)
    def test_select_enable_DHCPSupport_DNSSupport_DomainNamePattern_as_TenantName_EAs(self):
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

    @pytest.mark.run(order=12)
    def test_create_network_DHCPSupport_DNSSupport_DomainNamePattern_as_TenantName_EAs(self):
	proc = util.utils()
        proc.create_network(network)
	proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
	flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=13)
    def test_validate_member_assiged_network_DHCPSupport_DNSSupport_DomainNamePattern_as_TenantName_EAs(self):
	resp = json.loads(wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet))
	ref_v = resp[0]['_ref']
	members = json.loads(wapi_module.wapi_request('GET',object_type = ref_v+'?_return_fields=members'))
	name = members['members'][0]['name']
	assert grid_master_name == name, "Member has not been assign to Netwrok"
	
    @pytest.mark.run(order=14)
    def test_validate_zone_name_DomainNamePattern_as_TenantName_EAs(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	zone_name = ref_v[0]['fqdn']
	assert tenant_name+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=15)
    def test_validate_zone_EAs_DomainNamePattern_as_TenantName(self):
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
    def test_deploy_instnace_HostNamePattern_as_HostIPAddress(self):
	proc = util.utils()
	proc.launch_instance(instance_name,network)
	instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
	assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=17)
    def test_validate_a_record_HostNamePattern_as_HostIPAddress(self):
	ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	zone_name = ref_v_zone[0]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
	proc = util.utils()
	ip_add = proc.get_instance_ips(instance_name)
	ip_address = ip_add[network][0]['addr']
	fqdn = "host-"+'-'.join(ip_address.split('.'))+'.'+zone_name
	assert fqdn == a_record_name

    @pytest.mark.run(order=18)
    def test_validate_a_record_EAs_HostNamePattern_as_HostIPAddress(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
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
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
            ip_address = ports_list[l]['fixed_ips'][0]['ip_address']

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
	ports_list = port_list_openstack['ports']
	for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
	     port_id_openstack = ports_list[l]['id']
	     tenant_id_openstack = ports_list[1]['tenant_id']
             device_id_openstack = ports_list[l]['device_id']
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
    def test_validate_host_record_entry_mac_address(self):
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        mac_address_nios = host_records[0]['ipv4addrs'][0]['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
	      mac_address_openstack = ports_list[l]['mac_address']	

        assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=22)
    def test_validate_fixed_address_HostNamePattern_as_HostIPAddress(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
            ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']

        assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=23)
    def test_validate_mac_address_fixed_address_instance_HostNamePattern_as_HostIPAddress(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        ref = ref_v[0]['_ref']
        mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=mac'))
        mac_add_nios = mac_add['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']

        assert mac_add_nios == mac_address_openstack

    @pytest.mark.run(order=24)
    def test_validate_fixed_address_EAs_HostNamePattern_as_HostIPAddress(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
	for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
	     port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
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
    def test_terminate_instance_HostNamePattern_as_HostIPAddress(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=26)
    def test_delete_net_subnet_HostNamePattern_as_HostIPAddress(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == ()	

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
	instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
	assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=31)
    def test_validate_A_Record_SubnetName_as_HostName_Pattern(self):
	a_record_name = ''
	ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	zone_name = ref_v_zone[0]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
	proc = util.utils()
	ip_add = proc.get_instance_ips(instance_name)
	ip_address = ip_add[network][0]['addr']
	fqdn = "host-"+subnet_name+'-'+'-'.join(ip_address.split('.'))+'.'+zone_name
	assert fqdn == a_record_name

    @pytest.mark.run(order=32)
    def test_terminate_instance_used_SubnetName_as__HostName_pattern(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=33)
    def test_delete_subnet_used_NetworkName_as_DomainName_pattern(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == ()

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
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=38)
    def test_validate_a_record_SubnetID_as_HostNamePattern(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        subnet_id = proc.get_subnet_id(subnet_name)
        fqdn = "host-"+subnet_id+'-'+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert fqdn == a_record_name

    @pytest.mark.run(order=39)
    def test_terminate_instance_used_NetworkID_as_DomainNamePattern_and_SubnetID_as_HostNamePattern(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=40)
    def test_delete_subnet_used_NetworkID_as_DomainNamePattern(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == ()

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
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=45)
    def test_validate_a_record_NetworkName_as_HostNamePattern(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        network_name = proc.get_network(network)
        fqdn = "host-"+network_name+'-'+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert fqdn == a_record_name

    @pytest.mark.run(order=46)
    def test_terminate_instance_used_SubnetName_as_DomainNamePattern_and_NetworkName_as_HostNamePattern(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=47)
    def test_delete_subnet_used_SubnetName_as_DomainNamePattern(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == ()

    @pytest.mark.run(order=48)
    def test_EAs_SubnetID_as_DomainNamePattern_and_NetworkID_as_HostNamePattern(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        ref = ref_v[0]['_ref']
        data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value": "default"},\
                "Default Domain Name Pattern": {"value": "{subnet_id}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{network_id}-{ip_address}"},\
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

    @pytest.mark.run(order=49)
    def test_create_network_SubnetID_as_DomainNamePattern_and_NetworkID_as_HostNamePattern(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=50)
    def test_validate_zone_name_as_SubnetID_DomainNamePattern(self):
        proc = util.utils()
        subnet_id = proc.get_subnet_id(subnet_name)
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        assert subnet_id+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=51)
    def test_deploy_instance_NetworkID_as_HostNamePattern(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=52)
    def test_validate_a_record_NetworkID_as_HostNamePattern(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        network_id = proc.get_network_id(network)
        fqdn = "host-"+network_id+'-'+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert fqdn == a_record_name

    @pytest.mark.run(order=53)
    def test_terminate_instance_used_SubnetID_as_DomainNamePattern_and_NetworkID_as_HostNamePattern(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=54)
    def test_delete_subnet_used_SubnetID_as_DomainNamePattern(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == () 

    @pytest.mark.run(order=55)
    def test_add_custom_network_view(self):
        data = {"name":custom_net_view,"extattrs": {"CMP Type":{"value":"OpenStack"},\
                "Cloud API Owned": {"value":"True"},"Cloud Adapter ID":{"value":"1"},\
                "Tenant ID":{"value":"N/A"}}}
        proc = wapi_module.wapi_request('POST',object_type='networkview',fields=json.dumps(data))
        flag = False
        if (re.search(r""+custom_net_view,proc)):
            flag = True
        assert proc != "" and flag

    @pytest.mark.run(order=56)
    def test_CustomNetworkView_as_DefaultNetworkView_EA(self):
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
                "Default Network View": {"value":custom_net_view},\
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
	time.sleep(20)

    @pytest.mark.run(order=57)
    def test_create_network_CustomNetworkView_as_DefaultNetworkView_EA(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=58)
    def test_validate_network_in_CustomNetworkView(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        assert network_nios == subnet and \
               network_view == custom_net_view

    @pytest.mark.run(order=59)
    def test_validate_network_EAs_CustomNetworkView(self):
        session = util.utils()
        net_name = session.get_network(network)
        net_id = session.get_network_id(network)
        sub_name = session.get_subnet_name(subnet_name)
        snet_ID = session.get_subnet_id(subnet_name)
        tenant_id = session.get_tenant_id(network)
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
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

    @pytest.mark.run(order=60)
    def test_validate_zone_in_custom_network_view(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        network_view = ref_v[0]['view']
        assert zone_name == tenant_name+'.cloud.global.com' and \
               network_view == 'default.'+custom_net_view

    @pytest.mark.run(order=61)
    def test_validate_zone_EAs_in_CustomNetworkView(self):
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

    @pytest.mark.run(order=62)
    def test_deploy_instnace_CustomNetworkView(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=63)
    def test_validate_a_record_in_CustomNetwork_View(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        fqdn = "host-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert fqdn == a_record_name

    @pytest.mark.run(order=64)
    def test_validate_a_record_EAs_in_CustomNetworkView(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
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

    @pytest.mark.run(order=65)
    def test_validate_host_record_entry_in_CustomNetworkView(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_name = host_records[0]['name']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
            ip_address = ports_list[l]['fixed_ips'][0]['ip_address']

        host_record_openstack = "dhcp-port-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert host_record_name == host_record_openstack

    @pytest.mark.run(order=66)
    def test_validate_host_record_EAs_in_CustomNetworkView(self):
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
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
	     tenant_id_openstack = ports_list[l]['tenant_id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'network:dhcp'
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'True' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=67)
    def test_validate_host_record_entry_mac_address_in_CustomNetworkView(self):
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        mac_address_nios = host_records[0]['ipv4addrs'][0]['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']

        assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=68)
    def test_validate_fixed_address_in_CustomNetworkView(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
            ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']
        assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=69)
    def test_validate_mac_address_fixed_address_in_CustomNetworkView(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        ref = ref_v[0]['_ref']
        mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=mac'))
        mac_add_nios = mac_add['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']
        assert mac_add_nios == mac_address_openstack

    @pytest.mark.run(order=70)
    def test_validate_fixed_address_EAs_in_CustomNetworkView(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
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

    @pytest.mark.run(order=71)
    def test_terminate_instance_CustomNetworkView(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=72)
    def test_delete_net_subnet_CustomNetworkView(self):
        session = util.utils()
        delete_net = session.delete_network(network)
        assert delete_net == ()

    @pytest.mark.run(order=73)
    def test_delete_CustomNetworkView(self):
        proc = wapi_module.wapi_request('GET',object_type='networkview',params='?name='+custom_net_view)
        response = json.loads(proc)
        ref_v = response[0]['_ref']
        delete = wapi_module.wapi_request('DELETE',object_type=ref_v)
        flag = False
        if (re.search(r''+custom_net_view,delete)):
            flag = True
        assert delete != '',flag

    @pytest.mark.run(order=74)
    def test_select_DefaultNetworkViewScope_as_Tenant(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        ref = ref_v[0]['_ref']
        data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value":"default"},\
                "Default Domain Name Pattern": {"value": "{tenant_name}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{ip_address}-{tenant_id}"},\
                "Default Network View": {"value":"default"},\
                "Default Network View Scope": {"value": "Tenant"},\
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

    @pytest.mark.run(order=75)
    def test_create_network_DefaultNetworkViewScope_as_Tenant(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=76)
    def test_validate_network_in_DefaultNetworkViewScope_as_Tenant(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        tenant_id = session.get_tenant_id(network)
        assert network_nios == subnet and \
               network_view == tenant_name+'-'+tenant_id

    @pytest.mark.run(order=77)
    def test_validate_network_EAs_DefaultNetworkViewScope_as_Tenant(self):
        session = util.utils()
        net_name = session.get_network(network)
        net_id = session.get_network_id(network)
        sub_name = session.get_subnet_name(subnet_name)
        snet_ID = session.get_subnet_id(subnet_name)
        tenant_id = session.get_tenant_id(network)
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
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

    @pytest.mark.run(order=78)
    def test_validate_zone_DefaultNetworkViewScope_as_Tenant(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        network_view = ref_v[0]['view']
        session = util.utils()
        tenant_id = session.get_tenant_id(network)
        assert zone_name == tenant_name+'.cloud.global.com' and \
               network_view == 'default.'+tenant_name+'-'+tenant_id

    @pytest.mark.run(order=79)
    def test_validate_zone_EAs_DefaultNetworkViewScope_as_Tenant(self):
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

    @pytest.mark.run(order=80)
    def test_deploy_instnace_DefaultNetworkViewScope_as_Tenant(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=81)
    def test_validate_a_record_DefaultNetworkViewScope_as_Tenant(self):
	a_record_name = ''
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        tenant_id_openstack = proc.get_tenant_id(network)
        fqdn = "host-"+'-'.join(ip_address.split('.'))+'-'+tenant_id_openstack+'.'+zone_name
        assert fqdn == a_record_name

    @pytest.mark.run(order=82)
    def test_validate_a_record_EAs_DefaultNetworkViewScope_as_Tenant(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
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

    @pytest.mark.run(order=83)
    def test_validate_host_record_entry_DefaultNetworkViewScope_as_Tenant(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_name = host_records[0]['name']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
            ip_address = ports_list[l]['fixed_ips'][0]['ip_address']

        host_record_openstack = "dhcp-port-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert host_record_name == host_record_openstack

    @pytest.mark.run(order=84)
    def test_validate_host_record_entry_EAs_DefaultNetworkViewScope_as_Tenant(self):
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
	ports_list = port_list_openstack['ports']
	for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
	     port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
	     tenant_id_openstack = ports_list[l]['tenant_id']
             device_owner_opstk = 'network:dhcp'
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'True' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=85)
    def test_validate_host_record_entry_mac_address_DefaultNetworkViewScope_as_Tenant(self):
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        mac_address_nios = host_records[0]['ipv4addrs'][0]['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
	      mac_address_openstack = ports_list[l]['mac_address']
        assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=86)
    def test_validate_fixed_address_DefaultNetworkViewScope_as_Tenant(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
            ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']
        assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=87)
    def test_validate_mac_address_fixed_address_DefaultNetworkViewScope_as_Tenant(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        ref = ref_v[0]['_ref']
        mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=mac'))
        mac_add_nios = mac_add['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']
        assert mac_add_nios == mac_address_openstack

    @pytest.mark.run(order=88)
    def test_validate_fixed_address_EAs_DefaultNetworkViewScope_as_Tenant(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
	for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
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

    @pytest.mark.run(order=89)
    def test_terminate_instance_DefaultNetworkViewScope_as_Tenant(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=90)
    def test_delete_net_subnet_DefaultNetworkViewScope_as_Tenant(self):
        session = util.utils()
        delete_net = session.delete_network(network)
        assert delete_net == ()

    @pytest.mark.run(order=91)
    def test_select_DefaultNetworkViewScope_as_Network(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        ref = ref_v[0]['_ref']
        data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value":"default"},\
                "Default Domain Name Pattern": {"value": "{tenant_name}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{ip_address}-{tenant_name}"},\
                "Default Network View": {"value":"default"},\
                "Default Network View Scope": {"value": "Network"},\
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

    @pytest.mark.run(order=92)
    def test_create_network_DefaultNetworkViewScope_as_Network(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=93)
    def test_validate_network_in_DefaultNetworkViewScope_as_Network(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        network_id = session.get_network_id(network)
        assert network_nios == subnet and \
               network_view == network+'-'+network_id

    @pytest.mark.run(order=94)
    def test_validate_network_EAs_DefaultNetworkViewScope_as_Network(self):
        session = util.utils()
        net_name = session.get_network(network)
        net_id = session.get_network_id(network)
        sub_name = session.get_subnet_name(subnet_name)
        snet_ID = session.get_subnet_id(subnet_name)
        tenant_id = session.get_tenant_id(network)
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
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

    @pytest.mark.run(order=95)
    def test_validate_zone_DefaultNetworkViewScope_as_Network(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        network_view = ref_v[0]['view']
        session = util.utils()
        network_id = session.get_network_id(network)
        assert zone_name == tenant_name+'.cloud.global.com' and \
               network_view == 'default.'+network+'-'+network_id

    @pytest.mark.run(order=96)
    def test_validate_zone_EAs_DefaultNetworkViewScope_as_Network(self):
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

    @pytest.mark.run(order=97)
    def test_deploy_instnace_DefaultNetworkViewScope_as_Network(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=98)
    def test_validate_a_record_DefaultNetworkViewScope_as_Network(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        fqdn = "host-"+'-'.join(ip_address.split('.'))+'-'+tenant_name+'.'+zone_name
        assert fqdn == a_record_name

    @pytest.mark.run(order=99)
    def test_validate_a_record_EAs_DefaultNetworkViewScope_as_Network(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
	for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
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

    @pytest.mark.run(order=100)
    def test_validate_host_record_entry_DefaultNetworkViewScope_as_Network(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_name = host_records[0]['name']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
            ip_address = ports_list[l]['fixed_ips'][0]['ip_address']

        host_record_openstack = "dhcp-port-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert host_record_name == host_record_openstack

    @pytest.mark.run(order=101)
    def test_validate_host_record_entry_EAs_DefaultNetworkViewScope_as_Network(self):
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
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
	     tenant_id_openstack = ports_list[l]['tenant_id']
             device_owner_opstk = 'network:dhcp'
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'True' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=102)
    def test_validate_host_record_entry_mac_address_DefaultNetworkViewScope_as_Network(self):
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        mac_address_nios = host_records[0]['ipv4addrs'][0]['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']
        assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=103)
    def test_validate_fixed_address_DefaultNetworkViewScope_as_Network(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
            ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']
        assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=104)
    def test_validate_mac_address_fixed_address_DefaultNetworkViewScope_as_Network(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        ref = ref_v[0]['_ref']
        mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=mac'))
        mac_add_nios = mac_add['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']
        assert mac_add_nios == mac_address_openstack

    @pytest.mark.run(order=105)
    def test_validate_fixed_address_EAs_DefaultNetworkViewScope_as_Network(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
              port_id_openstack = ports_list[l]['id']
              device_id_openstack = ports_list[l]['device_id']
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

    @pytest.mark.run(order=106)
    def test_terminate_instance_DefaultNetworkViewScope_as_Network(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=107)
    def test_delete_net_subnet_DefaultNetworkViewScope_as_Network(self):
        session = util.utils()
        delete_net = session.delete_network(network)
        assert delete_net == ()

    @pytest.mark.run(order=108)
    def test_select_DefaultNetworkViewScope_as_Subnet(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        ref = ref_v[0]['_ref']
        data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value":"default"},\
                "Default Domain Name Pattern": {"value": "{tenant_name}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{ip_address}-{tenant_name}"},\
                "Default Network View": {"value":"default"},\
                "Default Network View Scope": {"value": "Subnet"},\
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

    @pytest.mark.run(order=109)
    def test_create_network_DefaultNetworkViewScope_as_Subnet(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=110)
    def test_validate_network_in_DefaultNetworkViewScope_as_Subnet(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        subnet_id = session.get_subnet_id(subnet_name)
        assert network_nios == subnet and \
               network_view == subnet_name+'-'+subnet_id

    @pytest.mark.run(order=111)
    def test_validate_network_EAs_DefaultNetworkViewScope_as_Subnet(self):
        session = util.utils()
        net_name = session.get_network(network)
        net_id = session.get_network_id(network)
        sub_name = session.get_subnet_name(subnet_name)
        snet_ID = session.get_subnet_id(subnet_name)
        tenant_id = session.get_tenant_id(network)
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
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

    @pytest.mark.run(order=112)
    def test_validate_zone_DefaultNetworkViewScope_as_Subnet(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        network_view = ref_v[0]['view']
        session = util.utils()
        subnet_id = session.get_subnet_id(subnet_name)
        assert zone_name == tenant_name+'.cloud.global.com' and \
               network_view == 'default.'+subnet_name+'-'+subnet_id

    @pytest.mark.run(order=113)
    def test_validate_zone_EAs_DefaultNetworkViewScope_as_Subnet(self):
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

    @pytest.mark.run(order=114)
    def test_deploy_instnace_DefaultNetworkViewScope_as_Subnet(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=115)
    def test_validate_a_record_DefaultNetworkViewScope_as_Subnet(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        fqdn = "host-"+'-'.join(ip_address.split('.'))+'-'+tenant_name+'.'+zone_name
        assert fqdn == a_record_name

    @pytest.mark.run(order=116)
    def test_validate_a_record_EAs_DefaultNetworkViewScope_as_Subnet(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
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

    @pytest.mark.run(order=117)
    def test_validate_host_record_entry_DefaultNetworkViewScope_as_Subnet(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_name = host_records[0]['name']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
              ip_address = ports_list[l]['fixed_ips'][0]['ip_address']

        host_record_openstack = "dhcp-port-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert host_record_name == host_record_openstack

    @pytest.mark.run(order=118)
    def test_validate_host_record_entry_EAs_DefaultNetworkViewScope_as_Subnet(self):
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
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'network:dhcp'
             tenant_id_openstack = ports_list[l]['tenant_id']
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'True' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=119)
    def test_validate_host_record_entry_mac_address_DefaultNetworkViewScope_as_Subnet(self):
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        mac_address_nios = host_records[0]['ipv4addrs'][0]['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
	for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']

        assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=120)
    def test_validate_fixed_address_DefaultNetworkViewScope_as_Subnet(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
	for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
               ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']
  	
        assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=121)
    def test_validate_mac_address_fixed_address_DefaultNetworkViewScope_as_Subnet(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        ref = ref_v[0]['_ref']
        mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=mac'))
        mac_add_nios = mac_add['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']

        assert mac_add_nios == mac_address_openstack

    @pytest.mark.run(order=122)
    def test_validate_fixed_address_EAs_DefaultNetworkViewScope_as_Subnet(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
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

    @pytest.mark.run(order=123)
    def test_terminate_instance_DefaultNetworkViewScope_as_Subnet(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=124)
    def test_delete_net_subnet_DefaultNetworkViewScope_as_Subnet(self):
        session = util.utils()
        delete_net = session.delete_network(network)
        assert delete_net == ()

    @pytest.mark.run(order=125)
    def test_EAs_disable_DHCPSupport_and_DNSSupport_ExternalDomainNamePattern(self):
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

    @pytest.mark.run(order=126)
    def test_add_ExternalNetwork_disable_DHCPSupport_and_DNSSupport_ExternalNetwork(self):
        proc = util.utils()
        address=proc.create_network(ext_network, external=True, shared=True)
        ext_net = proc.create_subnet(ext_network,ext_subnet_name,ext_subnet)
        flag = proc.get_network(ext_network)
        assert flag == ext_network

    @pytest.mark.run(order=127)
    def test_validate_network_disable_EAs_DHCPSupport_and_DNSSupport_ExternalNetwork(self):
        flag = False
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+ext_subnet)
        if (re.search(r""+ext_subnet,proc)):
            flag = True
        assert flag, "External Network creation failed "

    @pytest.mark.run(order=128)
    def test_validate_network_EAs_ExternalNetwork(self):
        session = util.utils()
        ext_net_name = session.get_network(ext_network)
        ext_net_id = session.get_network_id(ext_network)
        ext_sub_name = session.get_subnet_name(ext_subnet_name)
        ext_snet_ID = session.get_subnet_id(ext_subnet_name)
        ext_tenant_id = session.get_tenant_id(ext_network)
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+ext_subnet)
        resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        EAs = json.loads(wapi_module.wapi_request('GET',object_type = ref_v + '?_return_fields=extattrs'))
        assert EAs['extattrs']['Network Name']['value'] == ext_net_name and \
               EAs['extattrs']['Network ID']['value'] == ext_net_id and \
               EAs['extattrs']['Subnet Name']['value'] == ext_sub_name and \
               EAs['extattrs']['Subnet ID']['value'] == ext_snet_ID and \
               EAs['extattrs']['Network Encap']['value'] == 'vxlan' and \
               EAs['extattrs']['Cloud API Owned']['value'] == 'False' and \
               EAs['extattrs']['Tenant Name']['value'] == tenant_name and \
               EAs['extattrs']['Is External']['value'] == 'True' and \
               EAs['extattrs']['Is Shared']['value'] == 'True'

    @pytest.mark.run(order=129)
    def test_validate_NIOS_Router_ExternalNetwork(self):
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+ext_subnet)
        resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        options = json.loads(wapi_module.wapi_request('GET',object_type = ref_v + '?_return_fields=options'))
        route_list = options['options']
        for l in range(len(route_list)):
             router  = route_list[l]
             route_name = router['name']
             if route_name == 'routers':
                route_nios = router['value']
        ip = IPNetwork(ext_subnet).iter_hosts()
        route = str(ip.next())
        assert route_nios == route

    @pytest.mark.run(order=130)
    def test_delete_net_subnet_disable_EAs_DHCPSupport_and_DNSSupport_ExternalNetwork(self):
        session = util.utils()
        delete_net = session.delete_network(ext_network)
        assert delete_net == () 

    @pytest.mark.run(order=131)
    def test_select_EAs_ExternalDomainNamePattern_as_SubnetID_and_ExternalHostNamePattern_as_InstanceName(self):
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

    @pytest.mark.run(order=132)
    def test_create_network_ExternalDomainNamePattern_as_SubnetID_and_ExternalHostNamePattern_as_InstanceName(self):
        proc = util.utils()
        proc.create_network(ext_network, external = True, shared = True)
        proc.create_subnet(ext_network, ext_subnet_name, ext_subnet)
        flag = proc.get_subnet_name(ext_subnet_name)
        flag = proc.get_subnet_name(ext_subnet_name)
        assert flag == ext_subnet_name

    @pytest.mark.run(order=133)
    def test_validate_member_assiged_network_ExternalNetwork(self):
        resp = json.loads(wapi_module.wapi_request('GET',object_type = 'network',params="?network="+ext_subnet))
        ref_v = resp[0]['_ref']
        members = json.loads(wapi_module.wapi_request('GET',object_type = ref_v+'?_return_fields=members'))
        name = members['members'][0]['name']
        assert grid_master_name == name, "Member has not been assign to Netwrok"

    @pytest.mark.run(order=134)
    def test_validate_zone_name_ExternalDomainNamePattern_as_SubnetID(self):
        session = util.utils()
        ext_snet_ID = session.get_subnet_id(ext_subnet_name)
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        assert ext_snet_ID+'.external.global.com' == zone_name

    @pytest.mark.run(order=135)
    def test_validate_zone_EAs_ExternalDomainNamePattern_as_SubnetID(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        ref = ref_v[0]['_ref']
        EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=extattrs'))
        tenant_name_nios = EAs['extattrs']['Tenant Name']['value']
        tenant_id_nios = EAs['extattrs']['Tenant ID']['value']
        cmp_type_nios = EAs['extattrs']['CMP Type']['value']
        cloud_api_owned_nios = EAs['extattrs']['Cloud API Owned']['value']
        session = util.utils()
        tenant_id_openstack = session.get_tenant_id(ext_network)
        assert tenant_id_openstack == tenant_id_nios and \
               tenant_name_nios == tenant_name and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned_nios == 'False'

    @pytest.mark.run(order=136)
    def test_deploy_instnace_ExternalHostNamePattern_as_InstanceName(self):
        proc = util.utils()
        proc.launch_instance(instance_name,ext_network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=137)
    def test_validate_a_record_ExternalHostNamePattern_as_InstanceName(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
        assert a_record_name == instance_name+'.'+zone_name

    @pytest.mark.run(order=138)
    def test_validate_a_record_EAs_ExternalHostNamePattern_as_InstanceName(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[ext_network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'compute:None'
        assert vm_name_nios == vm_name_openstack and \
               vm_id_nios == vm_id_openstack and \
               tenant_name_nios == tenant_name and \
               tenant_id_nios == vm_tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               ip_type_nios == 'Fixed' and \
               device_owner_opstk == device_owner_nios and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=139)
    def test_validate_host_record_entry_ExternalNetwork(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_name = host_records[0]['name']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
            ip_address = ports_list[l]['fixed_ips'][0]['ip_address']

        host_record_openstack = "dhcp-port-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert host_record_name == host_record_openstack

    @pytest.mark.run(order=140)
    def test_validate_host_record_entry_EAs_ExternalNetwork(self):
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
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'network:dhcp'
             tenant_id_openstack = ports_list[l]['tenant_id']
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=141)
    def test_validate_host_record_entry_MACAddress_ExternalNetwork(self):
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        mac_address_nios = host_records[0]['ipv4addrs'][0]['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']

        assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=142)
    def test_validate_fixed_address_ExternalHostNamePattern_InstanceName(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
            ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']

        assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=143)
    def test_validate_mac_address_fixed_address_instance_ExternalHostNamePattern_as_InstanceName(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        ref = ref_v[0]['_ref']
        mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=mac'))
        mac_add_nios = mac_add['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
	      mac_address_openstack = ports_list[l]['mac_address']

        assert mac_add_nios == mac_address_openstack

    @pytest.mark.run(order=144)
    def test_validate_fixed_address_EAs_ExternalHostNamePattern_as_InstaanceName(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[ext_network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'compute:None'

        assert vm_name_nios == vm_name_openstack and \
               vm_id_nios == vm_id_openstack and \
               tenant_name_nios == tenant_name and \
               tenant_id_nios == vm_tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               ip_type_nios == 'Fixed' and \
               device_owner_opstk == device_owner_nios and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=145)
    def test_terminate_instance_ExternalHostNamePattern_as_InstanceName(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=146)
    def test_delete_net_subnet_ExternalHostNamePattern_as_InstanceName(self):
        session = util.utils()
        delete_net = session.delete_network(ext_network)
        assert delete_net == ()

    @pytest.mark.run(order=147)
    def test_select_EAs_ExternalDomainNamePattern_as_SubnetName_and_ExternalHostNamePattern_as_InstanceNameInstanceID(self):
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
                "External Domain Name Pattern": {"value": "{subnet_name}.external.global.com"},\
                "External Host Name Pattern": {"value": "{instance_name}-{instance_id}"},\
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

    @pytest.mark.run(order=148)
    def test_create_network_ExternalDomainNamePattern_as_SubnetName_and_ExternalHostNamePattern_as_InstanceNameInstanceID(self):
        proc = util.utils()
        proc.create_network(ext_network, external = True, shared = True)
        proc.create_subnet(ext_network, ext_subnet_name, ext_subnet)
        flag = proc.get_subnet_name(ext_subnet_name)
        flag = proc.get_subnet_name(ext_subnet_name)
        assert flag == ext_subnet_name

    @pytest.mark.run(order=149)
    def test_validate_zone_name_ExternalDomainNamePattern_as_SubnetName(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        assert ext_subnet_name+'.external.global.com' == zone_name

    @pytest.mark.run(order=150)
    def test_validate_zone_EAs_ExternalDomainNamePattern_as_SubnetName(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        ref = ref_v[0]['_ref']
        EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=extattrs'))
        tenant_name_nios = EAs['extattrs']['Tenant Name']['value']
        tenant_id_nios = EAs['extattrs']['Tenant ID']['value']
        cmp_type_nios = EAs['extattrs']['CMP Type']['value']
        cloud_api_owned_nios = EAs['extattrs']['Cloud API Owned']['value']
        session = util.utils()
        tenant_id_openstack = session.get_tenant_id(ext_network)
        assert tenant_id_openstack == tenant_id_nios and \
               tenant_name_nios == tenant_name and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned_nios == 'False'

    @pytest.mark.run(order=151)
    def test_deploy_instance_ExternalHostNamePattern_as_InstanceNameInstanceID(self):
        proc = util.utils()
        proc.launch_instance(instance_name,ext_network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=152)
    def test_validate_a_record_ExternalHostNamePattern_as_InstanceNameInstanceID(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
        proc = util.utils()
        instance_id_openstack = proc.get_servers_id(instance_name)
        assert a_record_name == instance_name+'-' +instance_id_openstack+ '.' +zone_name

    @pytest.mark.run(order=153)
    def test_validate_a_record_EAs_ExternalHostNamePattern_as_InstanceNameInstanceID(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[ext_network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'compute:None'
        assert vm_name_nios == vm_name_openstack and \
               vm_id_nios == vm_id_openstack and \
               tenant_name_nios == tenant_name and \
               tenant_id_nios == vm_tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               ip_type_nios == 'Fixed' and \
               device_owner_opstk == device_owner_nios and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=154)
    def test_validate_host_record_entry_ExternalHostNamePattern_as_InstanceNameInstanceID(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_name = host_records[0]['name']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
            ip_address = ports_list[l]['fixed_ips'][0]['ip_address']

        host_record_openstack = "dhcp-port-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert host_record_name == host_record_openstack

    @pytest.mark.run(order=155)
    def test_validate_host_record_entry_EAs_ExternalHostNamePattern_as_InstanceNameInstanceID(self):
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
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
	     tenant_id_openstack = ports_list[l]['tenant_id']
             device_owner_opstk = 'network:dhcp'
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=156)
    def test_validate_host_record_entry_MACAddress_ExternalHostNamePattern_as_InstanceNameInstanceID(self):
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        mac_address_nios = host_records[0]['ipv4addrs'][0]['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']
        assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=157)
    def test_validate_fixed_address_ExternalHostNamePattern_InstanceNameInstanceID(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
              ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']

        assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=158)
    def test_validate_mac_address_fixed_address_instance_ExternalHostNamePattern_as_InstanceNameInstanceID(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        ref = ref_v[0]['_ref']
        mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=mac'))
        mac_add_nios = mac_add['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']
        assert mac_add_nios == mac_address_openstack

    @pytest.mark.run(order=159)
    def test_validate_fixed_address_EAs_ExternalHostNamePattern_as_InstaanceNameInstanceID(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[ext_network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'compute:None'
        assert vm_name_nios == vm_name_openstack and \
               vm_id_nios == vm_id_openstack and \
               tenant_name_nios == tenant_name and \
               tenant_id_nios == vm_tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               ip_type_nios == 'Fixed' and \
               device_owner_opstk == device_owner_nios and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=160)
    def test_terminate_instance_ExternalHostNamePattern_as_InstanceNameInstanceID(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=161)
    def test_delete_net_subnet_ExternalHostNamePattern_as_InstanceNameInstanceID(self):
        session = util.utils()
        delete_net = session.delete_network(ext_network)
        assert delete_net == ()

    @pytest.mark.run(order=162)
    def test_select_EAs_ExternalDomainNamePattern_as_NetworkName_and_ExternalHostNamePattern_as_TenantNameTenantID(self):
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
                "External Domain Name Pattern": {"value": "{network_name}.external.global.com"},\
                "External Host Name Pattern": {"value": "{tenant_name}-{tenant_id}"},\
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

    @pytest.mark.run(order=163)
    def test_create_network_ExternalDomainNamePattern_as_NetworkName_and_ExternalHostNamePattern_as_TenantNameTenantID(self):
        proc = util.utils()
        proc.create_network(ext_network, external = True, shared = True)
        proc.create_subnet(ext_network, ext_subnet_name, ext_subnet)
        flag = proc.get_subnet_name(ext_subnet_name)
        flag = proc.get_subnet_name(ext_subnet_name)
        assert flag == ext_subnet_name

    @pytest.mark.run(order=164)
    def test_validate_zone_name_ExternalDomainNamePattern_as_NetworkName(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        assert ext_network+'.external.global.com' == zone_name

    @pytest.mark.run(order=165)
    def test_validate_zone_EAs_ExternalDomainNamePattern_as_NetworkName(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        ref = ref_v[0]['_ref']
        EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=extattrs'))
        tenant_name_nios = EAs['extattrs']['Tenant Name']['value']
        tenant_id_nios = EAs['extattrs']['Tenant ID']['value']
        cmp_type_nios = EAs['extattrs']['CMP Type']['value']
        cloud_api_owned_nios = EAs['extattrs']['Cloud API Owned']['value']
        session = util.utils()
        tenant_id_openstack = session.get_tenant_id(ext_network)
        assert tenant_id_openstack == tenant_id_nios and \
               tenant_name_nios == tenant_name and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned_nios == 'False'

    @pytest.mark.run(order=166)
    def test_deploy_instance_ExternalHostNamePattern_as_TenantNameTenantID(self):
        proc = util.utils()
        proc.launch_instance(instance_name,ext_network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=167)
    def test_validate_a_record_ExternalHostNamePattern_as_TenantNameTenantID(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
        proc = util.utils()
        tenant_id_opstk = proc.get_tenant_id(ext_network)
        assert a_record_name == tenant_name+'-' +tenant_id_opstk+ '.' +zone_name

    @pytest.mark.run(order=168)
    def test_validate_a_record_EAs_ExternalHostNamePattern_as_TenantNameTenantID(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[ext_network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
	for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'compute:None'
        assert vm_name_nios == vm_name_openstack and \
               vm_id_nios == vm_id_openstack and \
               tenant_name_nios == tenant_name and \
               tenant_id_nios == vm_tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               ip_type_nios == 'Fixed' and \
               device_owner_opstk == device_owner_nios and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=169)
    def test_validate_host_record_entry_ExternalHostNamePattern_as_TenantNameTenantID(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_name = host_records[0]['name']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
            ip_address = ports_list[l]['fixed_ips'][0]['ip_address']

        host_record_openstack = "dhcp-port-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert host_record_name == host_record_openstack

    @pytest.mark.run(order=170)
    def test_validate_host_record_entry_EAs_ExternalHostNamePattern_as_TenantNameTenantID(self):
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
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'network:dhcp'
             tenant_id_openstack = ports_list[l]['tenant_id']
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=171)
    def test_validate_host_record_entry_MACAddress_ExternalHostNamePattern_as_TenantNameTenantID(self):
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        mac_address_nios = host_records[0]['ipv4addrs'][0]['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']

        assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=172)
    def test_validate_fixed_address_ExternalHostNamePattern_TenantNameTenantID(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
            ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']

        assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=173)
    def test_validate_mac_address_fixed_address_instance_ExternalHostNamePattern_as_TenantNameTenantID(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        ref = ref_v[0]['_ref']
        mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=mac'))
        mac_add_nios = mac_add['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']
        assert mac_add_nios == mac_address_openstack

    @pytest.mark.run(order=174)
    def test_validate_fixed_address_EAs_ExternalHostNamePattern_as_TenantNameTenantID(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[ext_network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'compute:None'
        assert vm_name_nios == vm_name_openstack and \
               vm_id_nios == vm_id_openstack and \
               tenant_name_nios == tenant_name and \
               tenant_id_nios == vm_tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               ip_type_nios == 'Fixed' and \
               device_owner_opstk == device_owner_nios and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=175)
    def test_terminate_instance_ExternalHostNamePattern_as_TenantNameTenantID(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=176)
    def test_delete_net_subnet_ExternalHostNamePattern_as_TenantNameTenantID(self):
        session = util.utils()
        delete_net = session.delete_network(ext_network)
        assert delete_net == ()

    @pytest.mark.run(order=177)
    def test_select_EAs_ExternalDomainNamePattern_as_NetworkID_and_ExternalHostNamePattern_as_SubnetNameTenantID(self):
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
                "External Domain Name Pattern": {"value": "{network_id}.external.global.com"},\
                "External Host Name Pattern": {"value": "{subnet_name}-{tenant_id}"},\
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

    @pytest.mark.run(order=178)
    def test_create_network_ExternalDomainNamePattern_as_NetworkID_and_ExternalHostNamePattern_as_SubnetNameTenantID(self):
        proc = util.utils()
        proc.create_network(ext_network, external = True, shared = True)
        proc.create_subnet(ext_network, ext_subnet_name, ext_subnet)
        flag = proc.get_subnet_name(ext_subnet_name)
        flag = proc.get_subnet_name(ext_subnet_name)
        assert flag == ext_subnet_name

    @pytest.mark.run(order=179)
    def test_validate_zone_name_ExternalDomainNamePattern_as_NetworkID(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        proc = util.utils()
        net_id = proc.get_network_id(ext_network)
        assert net_id+'.external.global.com' == zone_name

    @pytest.mark.run(order=180)
    def test_validate_zone_EAs_ExternalDomainNamePattern_as_NetworkID(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        ref = ref_v[0]['_ref']
        EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=extattrs'))
        tenant_name_nios = EAs['extattrs']['Tenant Name']['value']
        tenant_id_nios = EAs['extattrs']['Tenant ID']['value']
        cmp_type_nios = EAs['extattrs']['CMP Type']['value']
        cloud_api_owned_nios = EAs['extattrs']['Cloud API Owned']['value']
        session = util.utils()
        tenant_id_openstack = session.get_tenant_id(ext_network)
        assert tenant_id_openstack == tenant_id_nios and \
               tenant_name_nios == tenant_name and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned_nios == 'False'

    @pytest.mark.run(order=181)
    def test_deploy_instance_ExternalHostNamePattern_as_SubnetNameTenantID(self):
        proc = util.utils()
        proc.launch_instance(instance_name,ext_network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=182)
    def test_validate_a_record_ExternalHostNamePattern_as_SubnetNameTenantID(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
        proc = util.utils()
        tenant_id_opstk = proc.get_tenant_id(ext_network)
        assert a_record_name == ext_subnet_name+'-' +tenant_id_opstk+ '.' +zone_name

    @pytest.mark.run(order=183)
    def test_validate_a_record_EAs_ExternalHostNamePattern_as_SubnetNameTenantID(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[ext_network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'compute:None'
        assert vm_name_nios == vm_name_openstack and \
               vm_id_nios == vm_id_openstack and \
               tenant_name_nios == tenant_name and \
               tenant_id_nios == vm_tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               ip_type_nios == 'Fixed' and \
               device_owner_opstk == device_owner_nios and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=184)
    def test_validate_host_record_entry_ExternalHostNamePattern_as_SubnetNameTenantID(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_name = host_records[0]['name']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
            ip_address = ports_list[l]['fixed_ips'][0]['ip_address']
        host_record_openstack = "dhcp-port-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert host_record_name == host_record_openstack

    @pytest.mark.run(order=185)
    def test_validate_host_record_entry_EAs_ExternalHostNamePattern_as_SubnetNameTenantID(self):
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
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'network:dhcp'
             tenant_id_openstack = ports_list[l]['tenant_id']
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=186)
    def test_validate_host_record_entry_MACAddress_ExternalHostNamePattern_as_SubnetNameTenantID(self):
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        mac_address_nios = host_records[0]['ipv4addrs'][0]['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
        ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']

        assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=187)
    def test_validate_fixed_address_ExternalHostNamePattern_SubnetNameTenantID(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
            ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']

        assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=188)
    def test_validate_mac_address_fixed_address_instance_ExternalHostNamePattern_as_SubnetNameTenantID(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        ref = ref_v[0]['_ref']
        mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=mac'))
        mac_add_nios = mac_add['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']
        assert mac_add_nios == mac_address_openstack

    @pytest.mark.run(order=189)
    def test_validate_fixed_address_EAs_ExternalHostNamePattern_as_SubnetNameTenantID(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[ext_network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'compute:None'
        assert vm_name_nios == vm_name_openstack and \
               vm_id_nios == vm_id_openstack and \
               tenant_name_nios == tenant_name and \
               tenant_id_nios == vm_tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               ip_type_nios == 'Fixed' and \
               device_owner_opstk == device_owner_nios and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=190)
    def test_terminate_instance_ExternalHostNamePattern_as_SubnetNameTenantID(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=191)
    def test_delete_net_subnet_ExternalHostNamePattern_as_SubnetNameTenantID(self):
        session = util.utils()
        delete_net = session.delete_network(ext_network)
        assert delete_net == () 

    @pytest.mark.run(order=192)
    def test_select_EAs_ExternalDomainNamePattern_as_TenantNameTenantID_and_ExternalHostNamePattern_as_SubnetIDTenantName(self):
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
                "External Domain Name Pattern": {"value": "{tenant_name}-{tenant_id}.external.global.com"},\
                "External Host Name Pattern": {"value": "{subnet_id}-{tenant_name}"},\
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

    @pytest.mark.run(order=193)
    def test_create_network_ExternalDomainNamePattern_as_TenantNameTenantID_and_ExternalHostNamePattern_as_SubnetIDTenantName(self):
        proc = util.utils()
        proc.create_network(ext_network, external = True, shared = True)
        proc.create_subnet(ext_network, ext_subnet_name, ext_subnet)
        flag = proc.get_subnet_name(ext_subnet_name)
        flag = proc.get_subnet_name(ext_subnet_name)
        assert flag == ext_subnet_name

    @pytest.mark.run(order=194)
    def test_validate_zone_name_ExternalDomainNamePattern_as_TenantNameTenantID(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        proc = util.utils()
        tenant_id = proc.get_tenant_id(ext_network)
        assert tenant_name+ '-' +tenant_id+'.external.global.com' == zone_name

    @pytest.mark.run(order=195)
    def test_validate_zone_EAs_ExternalDomainNamePattern_as_TenantNameTenantID(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        ref = ref_v[0]['_ref']
        EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=extattrs'))
        tenant_name_nios = EAs['extattrs']['Tenant Name']['value']
        tenant_id_nios = EAs['extattrs']['Tenant ID']['value']
        cmp_type_nios = EAs['extattrs']['CMP Type']['value']
        cloud_api_owned_nios = EAs['extattrs']['Cloud API Owned']['value']
        session = util.utils()
        tenant_id_openstack = session.get_tenant_id(ext_network)
        assert tenant_id_openstack == tenant_id_nios and \
               tenant_name_nios == tenant_name and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned_nios == 'False'

    @pytest.mark.run(order=196)
    def test_deploy_instance_ExternalHostNamePattern_as_SubnetIDTenantName(self):
        proc = util.utils()
        proc.launch_instance(instance_name,ext_network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=197)
    def test_validate_a_record_ExternalHostNamePattern_as_SubnetIDTenantName(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
        proc = util.utils()
        subnet_id_opstk = proc.get_subnet_id(ext_subnet_name)
        assert a_record_name == subnet_id_opstk+'-' +tenant_name+ '.' +zone_name

    @pytest.mark.run(order=198)
    def test_validate_a_record_EAs_ExternalHostNamePattern_as_SubnetIDTenantName(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[ext_network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'compute:None'
        assert vm_name_nios == vm_name_openstack and \
               vm_id_nios == vm_id_openstack and \
               tenant_name_nios == tenant_name and \
               tenant_id_nios == vm_tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               ip_type_nios == 'Fixed' and \
               device_owner_opstk == device_owner_nios and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=199)
    def test_validate_host_record_entry_ExternalHostNamePattern_as_SubnetIDTenantName(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_name = host_records[0]['name']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
            ip_address = ports_list[l]['fixed_ips'][0]['ip_address']

        host_record_openstack = "dhcp-port-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert host_record_name == host_record_openstack

    @pytest.mark.run(order=200)
    def test_validate_host_record_entry_EAs_ExternalHostNamePattern_as_SubnetIDTenantName(self):
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
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
	     tenant_id_openstack = ports_list[l]['tenant_id']
             device_owner_opstk = 'network:dhcp'
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=201)
    def test_validate_host_record_entry_MACAddress_ExternalHostNamePattern_as_SubnetIDTenantName(self):
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        mac_address_nios = host_records[0]['ipv4addrs'][0]['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']

        assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=202)
    def test_validate_fixed_address_ExternalHostNamePattern_SubnetIDTenantName(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
            ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']
        assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=203)
    def test_validate_mac_address_fixed_address_instance_ExternalHostNamePattern_as_SubnetIDTenantName(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        ref = ref_v[0]['_ref']
        mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=mac'))
        mac_add_nios = mac_add['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']
        assert mac_add_nios == mac_address_openstack

    @pytest.mark.run(order=204)
    def test_validate_fixed_address_EAs_ExternalHostNamePattern_as_SubnetIDTenantName(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[ext_network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'compute:None'
        assert vm_name_nios == vm_name_openstack and \
               vm_id_nios == vm_id_openstack and \
               tenant_name_nios == tenant_name and \
               tenant_id_nios == vm_tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               ip_type_nios == 'Fixed' and \
               device_owner_opstk == device_owner_nios and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=205)
    def test_terminate_instance_ExternalHostNamePattern_as_SubnetIDTenantName(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=206)
    def test_delete_net_subnet_ExternalHostNamePattern_as_SubnetIDTenantName(self):
        session = util.utils()
        delete_net = session.delete_network(ext_network)
        assert delete_net == ()

    @pytest.mark.run(order=207)
    def test_select_DefaultNetworkViewScope_as_AddressScope(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        ref = ref_v[0]['_ref']
        data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value":"default"},\
                "Default Domain Name Pattern": {"value": "{network_name}-{subnet_name}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{ip_address}-{tenant_id}"},\
                "Default Network View": {"value":"default"},\
                "Default Network View Scope": {"value": "Address Scope"},\
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

    @pytest.mark.run(order=208)
    def test_add_AddressScope_DefaultNetworkViewScope_as_AddressScope(self):
        session = util.utils()
        session.add_address_scope(address_scope_name_ip4,"4")
        session.address_scopes_list(address_scope_name_ip4)
        session.add_address_scope_subnetpool(address_scope_name_ip4,address_scope_subnet_name_ipv4,\
                                             address_scope_pool_prefix,address_scope_prefixlen)
        session.subnetpool_list(address_scope_subnet_name_ipv4)
        subnet = session.add_subnet_address_scope(network,address_scope_subnet_name_ipv4,subnet_name)
        flag = session.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=209)
    def test_validate_network_in_DefaultNetworkViewScope_as_AddressScope(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        address_scope_ids = session.address_scopes_list(address_scope_name_ip4)
        address_id = address_scope_ids['address_scopes'][0]['id']
        assert network_nios == address_scope_pool_prefix and \
               network_view == address_scope_name_ip4+'-'+address_id

    @pytest.mark.run(order=210)
    def test_validate_network_EAs_DefaultNetworkViewScope_as_AddressScope(self):
        session = util.utils()
        net_name = session.get_network(network)
        net_id = session.get_network_id(network)
        sub_name = session.get_subnet_name(subnet_name)
        snet_ID = session.get_subnet_id(subnet_name)
        tenant_id = session.get_tenant_id(network)
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+address_scope_pool_prefix)
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

    @pytest.mark.run(order=211)
    def test_validate_zone_DefaultNetworkViewScope_as_AddressScope(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        network_view = ref_v[0]['view']
        session = util.utils()
        address_scope_ids = session.address_scopes_list(address_scope_name_ip4)
        address_id = address_scope_ids['address_scopes'][0]['id']
        assert zone_name == network+'-'+subnet_name+'.cloud.global.com' and \
               network_view == 'default.'+address_scope_name_ip4+'-'+address_id

    @pytest.mark.run(order=212)
    def test_validate_zone_EAs_DefaultNetworkViewScope_as_AddressScope(self):
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

    @pytest.mark.run(order=213)
    def test_deploy_instnace_DefaultNetworkViewScope_as_AddressScope(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=214)
    def test_validate_a_record_DefaultNetworkViewScope_as_AddressScope(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        tenant_id_openstack = proc.get_tenant_id(network)
        fqdn = "host-"+'-'.join(ip_address.split('.'))+'-'+tenant_id_openstack+'.'+zone_name
        assert fqdn == a_record_name

    @pytest.mark.run(order=215)
    def test_validate_a_record_EAs_DefaultNetworkViewScope_as_AddressScope(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
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

    @pytest.mark.run(order=216)
    def test_validate_host_record_entry_DefaultNetworkViewScope_as_AddressScope(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_name = host_records[0]['name']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
            ip_address = ports_list[l]['fixed_ips'][0]['ip_address']
	host_record_openstack = "dhcp-port-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert host_record_name == host_record_openstack

    @pytest.mark.run(order=217)
    def test_validate_host_record_entry_EAs_DefaultNetworkViewScope_as_AddressScope(self):
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
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
	     tenant_id_openstack = ports_list[l]['tenant_id']
             device_owner_opstk = 'network:dhcp'
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'True' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=218)
    def test_validate_host_record_entry_mac_address_DefaultNetworkViewScope_as_AddressScope(self):
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        mac_address_nios = host_records[0]['ipv4addrs'][0]['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']
        assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=219)
    def test_validate_fixed_address_DefaultNetworkViewScope_as_AddressScope(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
            ip_address = ports_list[l]['fixed_ips'][0]['ip_address']
        assert fixed_address_nios == ip_address

    @pytest.mark.run(order=220)
    def test_validate_mac_address_fixed_address_DefaultNetworkViewScope_as_AddressScope(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        ref = ref_v[0]['_ref']
        mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=mac'))
        mac_add_nios = mac_add['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']
        assert mac_add_nios == mac_address_openstack

    @pytest.mark.run(order=221)
    def test_validate_fixed_address_EAs_DefaultNetworkViewScope_as_AddressScope(self):
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
        vm_id_openstack = proc.get_servers_id(instance_name)
        vm_name_openstack = proc.get_server_name(instance_name)
        vm_tenant_id_openstack = proc.get_server_tenant_id()
        ip_adds = proc.get_instance_ips(instance_name)
        inst_ip_address = ip_adds[network][0]['addr']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
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

    @pytest.mark.run(order=222)
    def test_terminate_instance_DefaultNetworkViewScope_as_AddressScope(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=223)
    def test_delete_net_subnet_DefaultNetworkViewScope_as_AddressScope(self):
        session = util.utils()
        delete_net = session.delete_network(network)
        assert delete_net == ()

    @pytest.mark.run(order=224)
    def test_delete_SubnetPool(self):
        proc = util.utils()
        delete = proc.delete_subnetpool(address_scope_subnet_name_ipv4)
        assert delete == ()

    @pytest.mark.run(order=225)
    def test_delete_AddressScope(self):
        proc = util.utils()
        delete = proc.delete_address_scopes(address_scope_name_ip4)
        assert delete == ()
	time.sleep(10)

    @pytest.mark.run(order=226)
    def test_select_IPAllocationStrategy_as_HostReocrd(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        ref = ref_v[0]['_ref']
        data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value":"default"},\
                "Default Domain Name Pattern": {"value": "{tenant_name}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{ip_address}-{tenant_name}"},\
                "Default Network View": {"value":"default"},\
                "Default Network View Scope": {"value": "Subnet"},\
                "External Domain Name Pattern": {"value": "{subnet_id}.external.global.com"},\
                "External Host Name Pattern": {"value": "{instance_name}"},\
                "Grid Sync Maximum Wait Time": {"value": 10},\
                "Grid Sync Minimum Wait Time": {"value": 10},"Grid Sync Support": {"value": "True"},\
                "IP Allocation Strategy": {"value": "Host Record"},\
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
	time.sleep(10)
	
    @pytest.mark.run(order=227)
    def test_create_network_IPAllocationStrategy_as_HostReocrd(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=228)
    def test_validate_network_in_IPAllocationStrategy_as_HostReocrd(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        subnet_id = session.get_subnet_id(subnet_name)
        assert network_nios == subnet and \
               network_view == subnet_name+'-'+subnet_id

    @pytest.mark.run(order=229)
    def test_validate_network_EAs_IPAllocationStrategy_as_HostReocrd(self):
        session = util.utils()
        net_name = session.get_network(network)
        net_id = session.get_network_id(network)
        sub_name = session.get_subnet_name(subnet_name)
        snet_ID = session.get_subnet_id(subnet_name)
        tenant_id = session.get_tenant_id(network)
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
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

    @pytest.mark.run(order=230)
    def test_validate_zone_IPAllocationStrategy_as_HostReocrd(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        network_view = ref_v[0]['view']
        session = util.utils()
        subnet_id = session.get_subnet_id(subnet_name)
        assert zone_name == tenant_name+'.cloud.global.com' and \
               network_view == 'default.'+subnet_name+'-'+subnet_id

    @pytest.mark.run(order=231)
    def test_validate_zone_EAs_IPAllocationStrategy_as_HostReocrd(self):
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

    @pytest.mark.run(order=232)
    def test_deploy_instnace_IPAllocationStrategy_as_HostReocrd(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=233)
    def test_validate_Host_record_IPAllocationStrategy_as_HostReocrd(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
	proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        ref_v_host_record = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
	fqdn = "host-"+'-'.join(ip_address.split('.'))+'-'+tenant_name+'.'+zone_name
	for l in range(len(ref_v_host_record)):
		if ip_address == ref_v_host_record[l]['ipv4addrs'][0]['ipv4addr']:
		     host_record_name = ref_v_host_record[l]['name']
	assert fqdn == host_record_name

    @pytest.mark.run(order=234)
    def test_validate_host_record_EAs_IPAllocationStrategy_as_HostReocrd(self):
        ref_v_host_record = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_name = ref_v_host_record[0]['name']
        host_record_ipaddr = ref_v_host_record[0]['ipv4addrs'][0]['ipv4addr']
        host1_record_name = ref_v_host_record[1]['name']
        host1_record_ipaddr = ref_v_host_record[1]['ipv4addrs'][0]['ipv4addr']
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        if ip_address == host_record_ipaddr:
            ref_v = ref_v_host_record[0]['_ref']
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
            vm_id_openstack = proc.get_servers_id(instance_name)
            vm_name_openstack = proc.get_server_name(instance_name)
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
        else:
            ref_v = ref_v_host_record[1]['_ref']
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
            vm_id_openstack = proc.get_servers_id(instance_name)
            vm_name_openstack = proc.get_server_name(instance_name)
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


    @pytest.mark.run(order=235)
    def test_validate_host_record_entry_IPAllocationStrategy_as_HostReocrd(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        ref_v_host_record = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_ipaddr = ref_v_host_record[0]['ipv4addrs'][0]['ipv4addr']
        host1_record_ipaddr = ref_v_host_record[1]['ipv4addrs'][0]['ipv4addr']
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        if ip_address == host_record_ipaddr:
           host_record_name = ref_v_host_record[1]['name']
        else:
           host_record_name = ref_v_host_record[0]['name']
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
            ip_address = ports_list[l]['fixed_ips'][0]['ip_address']

        host_record_openstack = "dhcp-port-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert host_record_name == host_record_openstack

    @pytest.mark.run(order=236)
    def test_validate_host_record_entry_EAs_IPAllocationStrategy_as_HostReocrd(self):
        ref_v_host_record = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_ipaddr = ref_v_host_record[0]['ipv4addrs'][0]['ipv4addr']
        host1_record_ipaddr = ref_v_host_record[1]['ipv4addrs'][0]['ipv4addr']
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        if ip_address == host_record_ipaddr:
            ref_v = ref_v_host_record[1]['_ref']
            EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref_v+'?_return_fields=extattrs'))
            tenant_id_nios = EAs['extattrs']['Tenant ID']['value']
            tenant_name_nios = EAs['extattrs']['Tenant Name']['value']
            port_id_nios = EAs['extattrs']['Port ID']['value']
            ip_type_nios = EAs['extattrs']['IP Type']['value']
            device_id_nios = EAs['extattrs']['Port Attached Device - Device ID']['value']
            device_owner_nios = EAs['extattrs']['Port Attached Device - Device Owner']['value']
            cmp_type_nios = EAs['extattrs']['CMP Type']['value']
            cloud_api_owned = EAs['extattrs']['Cloud API Owned']['value']
            port_list_openstack = proc.list_ports()
	    ports_list = port_list_openstack['ports']
            for l in range(len(ports_list)):
                if ('network:dhcp' == ports_list[l]['device_owner']):
                   port_id_openstack = ports_list[l]['id']
                   device_id_openstack = ports_list[l]['device_id']
	           tenant_id_openstack = ports_list[l]['tenant_id']
                   device_owner_opstk = 'network:dhcp'	
            assert tenant_id_nios == tenant_id_openstack and \
                port_id_nios == port_id_openstack and \
                tenant_name_nios == tenant_name and \
                ip_type_nios == 'Fixed' and \
                device_owner_nios == device_owner_opstk and \
                cmp_type_nios == 'OpenStack' and \
                cloud_api_owned == 'True' and \
                device_id_nios == device_id_openstack

        else:
            ref_v = ref_v_host_record[0]['_ref']
            EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref_v+'?_return_fields=extattrs'))
            tenant_id_nios = EAs['extattrs']['Tenant ID']['value']
            tenant_name_nios = EAs['extattrs']['Tenant Name']['value']
            port_id_nios = EAs['extattrs']['Port ID']['value']
            ip_type_nios = EAs['extattrs']['IP Type']['value']
            device_id_nios = EAs['extattrs']['Port Attached Device - Device ID']['value']
            device_owner_nios = EAs['extattrs']['Port Attached Device - Device Owner']['value']
            cmp_type_nios = EAs['extattrs']['CMP Type']['value']
            cloud_api_owned = EAs['extattrs']['Cloud API Owned']['value']
            port_list_openstack = proc.list_ports()
	    ports_list = port_list_openstack['ports']
            for l in range(len(ports_list)):
                if ('network:dhcp' == ports_list[l]['device_owner']):
                   port_id_openstack = ports_list[l]['id']
                   device_id_openstack = ports_list[l]['device_id']
	           tenant_id_openstack = ports_list[l]['tenant_id']
                   device_owner_opstk = 'network:dhcp'
            assert tenant_id_nios == tenant_id_openstack and \
                port_id_nios == port_id_openstack and \
                tenant_name_nios == tenant_name and \
                ip_type_nios == 'Fixed' and \
                device_owner_nios == device_owner_opstk and \
                cmp_type_nios == 'OpenStack' and \
                cloud_api_owned == 'True' and \
                device_id_nios == device_id_openstack

    @pytest.mark.run(order=237)
    def test_validate_host_record_entry_mac_address_IPAllocationStrategy_as_HostReocrd(self):
        ref_v_host_record = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_ipaddr = ref_v_host_record[0]['ipv4addrs'][0]['ipv4addr']
        host1_record_ipaddr = ref_v_host_record[1]['ipv4addrs'][0]['ipv4addr']
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        if host_record_ipaddr == ip_address:
            mac_address_nios = ref_v_host_record[1]['ipv4addrs'][0]['mac']
            port_list_openstack = proc.list_ports()
	    ports_list = port_list_openstack['ports']
            for l in range(len(ports_list)):
               if ('network:dhcp' == ports_list[l]['device_owner']):
                   mac_address_openstack = ports_list[l]['mac_address']
            assert mac_address_nios == mac_address_openstack
        else:
            mac_address_nios = ref_v_host_record[0]['ipv4addrs'][0]['mac']
            port_list_openstack = proc.list_ports()
	    ports_list = port_list_openstack['ports']
            for l in range(len(ports_list)):
               if ('network:dhcp' == ports_list[l]['device_owner']):
                   mac_address_openstack = ports_list[l]['mac_address']
            assert mac_address_nios == mac_address_openstack


    @pytest.mark.run(order=238)
    def test_validate_host_record_mac_address_IPAllocationStrategy_as_HostReocrd(self):
        ref_v_host_record = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        host_record_ipaddr = ref_v_host_record[0]['ipv4addrs'][0]['ipv4addr']
        host1_record_ipaddr = ref_v_host_record[1]['ipv4addrs'][0]['ipv4addr']
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        if host_record_ipaddr == ip_address:
            mac_address_nios = ref_v_host_record[0]['ipv4addrs'][0]['mac']
            port_list_openstack = proc.list_ports()
	    ports_list = port_list_openstack['ports']
            for l in range(len(ports_list)):
                if ('compute:None' == ports_list[l]['device_owner']):
                    mac_address_openstack = ports_list[l]['mac_address']
            assert mac_address_nios == mac_address_openstack
        else:
            mac_address_nios = ref_v_host_record[1]['ipv4addrs'][0]['mac']
            port_list_openstack = proc.list_ports()
	    ports_list = port_list_openstack['ports']
            for l in range(len(ports_list)):
               if ('compute:None' == ports_list[l]['device_owner']):
                   mac_address_openstack = ports_list[l]['mac_address']
            assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=239)
    def test_validate_mac_address_HOSTIPv4Address_IPAllocationStrategy_as_HostReocrd(self):
        ref_v_host_address = json.loads(wapi_module.wapi_request('GET',object_type='record:host_ipv4addr'))
        host_record_ipaddr = ref_v_host_address[0]['ipv4addr']
        host1_record_ipaddr = ref_v_host_address[1]['ipv4addr']
        proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
        if ip_address == host_record_ipaddr:
            ref_v = ref_v_host_address[0]['_ref']
            mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref_v+'?_return_fields=mac'))
            mac_add_nios = mac_add['mac']
            port_list_openstack = proc.list_ports()
	    ports_list = port_list_openstack['ports']
            for l in range(len(ports_list)):
                if ('compute:None' == ports_list[l]['device_owner']):
                    mac_address_openstack = ports_list[l]['mac_address']
            assert mac_add_nios == mac_address_openstack
        else:
            ref_v = ref_v_host_address[1]['_ref']
            mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref_v+'?_return_fields=mac'))
            mac_add_nios = mac_add['mac']
            port_list_openstack = proc.list_ports()
	    ports_list = port_list_openstack['ports']
            for l in range(len(ports_list)):
                if ('compute:None' == ports_list[l]['device_owner']):
                    mac_address_openstack = ports_list[l]['mac_address']
            assert mac_add_nios == mac_address_openstack

    @pytest.mark.run(order=240)
    def test_terminate_instance_IPAllocationStrategy_as_HostReocrd(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=241)
    def test_delete_net_subnet_IPAllocationStrategy_as_HostReocrd(self):
        session = util.utils()
        delete_net = session.delete_network(network)
        assert delete_net == ()

