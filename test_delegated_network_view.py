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
cp_member_ip=parser.get('Default','CP_Member_IP')
cp_member_name = parser.get('Default','CP_Member_Domain_Name')
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
delegated_net_view='delegated_net_view'

class TestOpenStackCases(unittest.TestCase):
    @classmethod
    def setup_class(cls):
	pass

    @pytest.mark.run(order=1)
    def test_add_delegated_network_view(self):
        data = {"name":delegated_net_view,\
                "cloud_info": {"delegated_member": {"_struct": "dhcpmember","ipv4addr": cp_member_ip,\
                "name": cp_member_name}\
                },"extattrs": {"CMP Type":{"value":"OpenStack"},\
                "Cloud API Owned": {"value":"True"},"Cloud Adapter ID":{"value":"1"},\
                "Tenant ID":{"value":"N/A"}}}
        proc = wapi_module.wapi_request('POST',object_type='networkview',fields=json.dumps(data))
        flag = False
        if (re.search(r""+delegated_net_view,proc)):
            flag = True
        assert proc != "" and flag

    @pytest.mark.run(order=2)
    def test_EAs_disable_DHCPSupport_and_DNSSupport(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
	for i in range(len(ref_v)):
          if ref_v[i]['host_name'] == grid_master_name:
            ref = ref_v[i]['_ref']
            data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "False"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "False"},"DNS View": {"value": "default"},\
                "Default Domain Name Pattern": {"value": "{tenant_name}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{ip_address}"},\
                "Default Network View": {"value": delegated_net_view},\
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
	    time.sleep(20)

    @pytest.mark.run(order=3)	
    def test_create_Network_disable_EAs_DHCPSupport_and_DNSSupport(self):
        proc = util.utils()
        proc.create_network(network)
	flag = proc.get_network(network)
	assert flag == network

    @pytest.mark.run(order=4)
    def test_create_subnet_disable_EAs_DHCPSupport_and_DNSSupport(self):
	proc = util.utils()
	proc.create_subnet(network, subnet_name, subnet)
	flag = proc.get_subnet_name(subnet_name)
	assert flag == subnet_name

    @pytest.mark.run(order=5)
    def test_validate_network_in_DelegatedNetworkView(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        assert network_nios == subnet and \
               network_view == delegated_net_view

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
               EAs['extattrs']['Network Encap']['value'] == 'vxlan' and \
               EAs['extattrs']['Cloud API Owned']['value'] == 'True' and \
	       EAs['extattrs']['CMP Type']['value'] == 'OpenStack'

    @pytest.mark.run(order=7)
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

    @pytest.mark.run(order=8)
    def test_delete_net_subnet_disable_EAs_DHCPSupport_and_DNSSupport(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == ()
	time.sleep(2)

    @pytest.mark.run(order=9)
    def test_validate_delete_network_disable_EAs_DHCPSupport_and_DNSSupport(self):
        flag = True
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
        if (re.search(r""+subnet,proc)):
            flag = False
        assert flag, "Network didn't remove from NIOS "

    @pytest.mark.run(order=10)
    def test_select_enable_DHCPSupport_DNSSupport_DomainNamePattern_as_TenantName_EAs(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        for i in range(len(ref_v)):
          if ref_v[i]['host_name'] == grid_master_name:
            ref = ref_v[i]['_ref']
	    data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value": "default"},\
                "Default Domain Name Pattern": {"value": "{tenant_name}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{ip_address}"},\
                "Default Network View": {"value": delegated_net_view},\
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

    @pytest.mark.run(order=11)
    def test_create_network_DHCPSupport_DNSSupport_DomainNamePattern_as_TenantName_EAs(self):
	proc = util.utils()
        proc.create_network(network)
	proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
	flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=12)
    def test_validate_member_assiged_network_DHCPSupport_DNSSupport_DomainNamePattern_as_TenantName_EAs(self):
	resp = json.loads(wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet))
	ref_v = resp[0]['_ref']
	members = json.loads(wapi_module.wapi_request('GET',object_type = ref_v+'?_return_fields=members'))
	name = members['members'][0]['name']
	assert cp_member_name == name, "Member has not been assign to Netwrok"
	
    @pytest.mark.run(order=13)
    def test_validate_zone_name_DomainNamePattern_as_TenantName_EAs(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	zone_name = ref_v[0]['fqdn']
	assert tenant_name+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=14)
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
    @pytest.mark.run(order=15)
    def test_deploy_instnace_HostNamePattern_as_HostIPAddress(self):
	proc = util.utils()
	proc.launch_instance(instance_name,network)
	instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
	assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=16)
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

    @pytest.mark.run(order=17)
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

    @pytest.mark.run(order=18)
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

    @pytest.mark.run(order=19)
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

    @pytest.mark.run(order=20)
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

    @pytest.mark.run(order=21)
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

    @pytest.mark.run(order=22)
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

    @pytest.mark.run(order=23)
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

    @pytest.mark.run(order=24)
    def test_terminate_instance_HostNamePattern_as_HostIPAddress(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=25)
    def test_delete_net_subnet_HostNamePattern_as_HostIPAddress(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == ()	

       # Default Domain Name Pattern : {network_name}.cloud.global.com
       # Default Host Name Pattern : host-{subnet_name}-{ip_address}
    @pytest.mark.run(order=26)
    def test_EAs_SubnetName_as_HostName_pattern_and_NetworkName_as_DomainName_pattern(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        for i in range(len(ref_v)):
          if ref_v[i]['host_name'] == grid_master_name:
            ref = ref_v[i]['_ref']
	    data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value": "default"},\
                "Default Domain Name Pattern": {"value": "{network_name}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{subnet_name}-{ip_address}"},\
                "Default Network View": {"value": delegated_net_view},\
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

    @pytest.mark.run(order=27)
    def test_create_network_NetworkName_as_DomainName_Pattern_openstack_side(self):
	proc = util.utils()
        proc.create_network(network)
	proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
	flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=28)
    def test_validate_zone_name_NetworkName_as_DomainName_pattern(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	zone_name = ref_v[0]['fqdn']
	assert network+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=29)
    def test_deploy_instance_SubnetName_as_HostName_Pattern(self):
	proc = util.utils()
	proc.launch_instance(instance_name,network)
	instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
	assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=30)
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

    @pytest.mark.run(order=31)
    def test_terminate_instance_used_SubnetName_as__HostName_pattern(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=32)
    def test_delete_subnet_used_NetworkName_as_DomainName_pattern(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == ()

    @pytest.mark.run(order=33)
    def test_EAs_NetworkID_as_DomainNamePattern_and_SubnetID_as_HostNamePattern(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
   	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        for i in range(len(ref_v)):
          if ref_v[i]['host_name'] == grid_master_name:
            ref = ref_v[i]['_ref']
            data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value": "default"},\
                "Default Domain Name Pattern": {"value": "{network_id}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{subnet_id}-{ip_address}"},\
                "Default Network View": {"value": delegated_net_view},\
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

    @pytest.mark.run(order=34)
    def test_create_network_NetworkID_as_DomainNamePattern_and_SubnetID_as_HostNamePattern(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=35)
    def test_validate_zone_name_as_NetworkID_DomainNamePattern(self):
        proc = util.utils()
        network_id = proc.get_network_id(network)
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        assert network_id+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=36)
    def test_deploy_instance_SubnetID_as_HostNamePattern(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=37)
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

    @pytest.mark.run(order=38)
    def test_terminate_instance_used_NetworkID_as_DomainNamePattern_and_SubnetID_as_HostNamePattern(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=39)
    def test_delete_subnet_used_NetworkID_as_DomainNamePattern(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == ()

    #"Default Domain Name Pattern":"{subnet_name}.cloud.global.com"
    #"Default Host Name Pattern": "host-{network_name}-{ip_address}"
    @pytest.mark.run(order=40)
    def test_EAs_SubnetName_as_DomainNamePattern_and_NetworkName_as_HostNamePattern(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
  	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        for i in range(len(ref_v)):
          if ref_v[i]['host_name'] == grid_master_name:
            ref = ref_v[i]['_ref']
            data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value": "default"},\
                "Default Domain Name Pattern": {"value": "{subnet_name}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{network_name}-{ip_address}"},\
                "Default Network View": {"value": delegated_net_view},\
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

    @pytest.mark.run(order=41)
    def test_create_network_SubnetName_as_DomainNamePattern_and_NetworkName_as_HostNamePattern(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=42)
    def test_validate_zone_name_as_SubnetName_DomainNamePattern(self):
        proc = util.utils()
        name_subnet = proc.get_subnet_name(subnet_name)
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        assert name_subnet+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=43)
    def test_deploy_instance_NetworkName_as_HostNamePattern(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=44)
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

    @pytest.mark.run(order=45)
    def test_terminate_instance_used_SubnetName_as_DomainNamePattern_and_NetworkName_as_HostNamePattern(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=46)
    def test_delete_subnet_used_SubnetName_as_DomainNamePattern(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == ()

    @pytest.mark.run(order=47)
    def test_EAs_SubnetID_as_DomainNamePattern_and_NetworkID_as_HostNamePattern(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
  	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        for i in range(len(ref_v)):
          if ref_v[i]['host_name'] == grid_master_name:
            ref = ref_v[i]['_ref']
            data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value": "default"},\
                "Default Domain Name Pattern": {"value": "{subnet_id}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{network_id}-{ip_address}"},\
                "Default Network View": {"value": delegated_net_view},\
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

    @pytest.mark.run(order=48)
    def test_create_network_SubnetID_as_DomainNamePattern_and_NetworkID_as_HostNamePattern(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=49)
    def test_validate_zone_name_as_SubnetID_DomainNamePattern(self):
        proc = util.utils()
        subnet_id = proc.get_subnet_id(subnet_name)
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        assert subnet_id+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=50)
    def test_deploy_instance_NetworkID_as_HostNamePattern(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=51)
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

    @pytest.mark.run(order=52)
    def test_terminate_instance_used_SubnetID_as_DomainNamePattern_and_NetworkID_as_HostNamePattern(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=53)
    def test_delete_subnet_used_SubnetID_as_DomainNamePattern(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == ()