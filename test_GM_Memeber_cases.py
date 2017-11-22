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
grid_member_ip=parser.get('Default','Grid_Member_IP')
grid_member_name = parser.get('Default','Grid_Member_Name')
tenant_name = 'admin'
network = 'net1'
network1 = 'network'
Modify_Network_name = 'Updated_Network_Name'
subnet_name = "snet"
subnet_name1 = 'subnet'
updated_subnet_name = 'updated_subnet_name'
instance_name = 'inst'
updated_instance_name = 'updated_instance_name'
subnet = "10.2.0.0/24"
subnet1 = '10.1.0.0/24'
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
    def test_select_DefaultNetworkViewScope_as_default(self):
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
                "DNS Support": {"value": "True"},"DNS View": {"value":"default"},\
                "Default Domain Name Pattern": {"value": "{tenant_name}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{ip_address}-{tenant_name}"},\
                "Default Network View": {"value":"default"},\
                "Default Network View Scope": {"value": "Single"},\
                "External Domain Name Pattern": {"value": "{subnet_id}.external.global.com"},\
                "External Host Name Pattern": {"value": "{instance_name}"},\
                "Grid Sync Maximum Wait Time": {"value": 10},\
                "Grid Sync Minimum Wait Time": {"value": 10},"Grid Sync Support": {"value": "True"},\
                "IP Allocation Strategy": {"value": "Fixed Address"},\
                "Relay Support": {"value": "False"},\
                "Report Grid Sync Time": {"value": "True"},\
                "Tenant Name Persistence": {"value": "False"},\
                "Use Grid Master for DHCP": {"value": "False"},\
		"Is Cloud Member":{"value":"False"},\
                "Zone Creation Strategy": {"value": ["Forward","Reverse"]}}}
          proc = wapi_module.wapi_request('PUT',object_type=ref,fields=json.dumps(data))
          flag = False
          if (re.search(r""+grid_master_name,proc)):
            flag = True
          assert proc != "" and flag

    @pytest.mark.run(order=2)
    def test_select_IsCloudMember_EA_Member(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        for i in range(len(ref_v)):
         if ref_v[i]['host_name'] == grid_member_name:
          ref = ref_v[i]['_ref']
          data = {"extattrs":{"Is Cloud Member": {"value": "True"}}}
          proc = wapi_module.wapi_request('PUT',object_type=ref,fields=json.dumps(data))
          flag = False
          if (re.search(r""+grid_member_name,proc)):
            flag = True
          assert proc != "" and flag

    @pytest.mark.run(order=3)
    def test_create_Network__Member(self):
        proc = util.utils()
        proc.create_network(network)
        flag = proc.get_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag1 = proc.get_subnet_name(subnet_name)
        assert flag == network and flag1 == subnet_name

    @pytest.mark.run(order=4)
    def test_validate_network_assign_to_Member(self):
	flag = False	
	proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
	if (re.search(r""+subnet,proc)):
	    flag = True
	assert flag, "Network creation failed "

    @pytest.mark.run(order=5)
    def test_validate_network_EAs_DefaultNetworkViewScope_as_default_Member(self):
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

    @pytest.mark.run(order=6)
    def test_validate_zone_DefaultNetworkViewScope_as_default_Member(self):
	session = util.utils()
        subnet_id = session.get_subnet_id(subnet_name)
        network_view = 'default.'+subnet_name+'-'+subnet_id
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	for i in range(len(ref_v)):
		   zone = ref_v[i]['fqdn']
        	   if zone.startswith(tenant_name):
			zone_name = ref_v[i]['fqdn']
        assert zone_name == tenant_name+'.cloud.global.com' and \
               network_view == 'default.'+subnet_name+'-'+subnet_id

    @pytest.mark.run(order=7)
    def test_validate_zone_EAs_DefaultNetworkViewScope_as_default_Member(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        for i in range(len(ref_v)):
                   zone = ref_v[i]['fqdn']
                   if zone.startswith(tenant_name):
                        zone_name = ref_v[i]['fqdn']
        		ref = ref_v[i]['_ref']
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

    @pytest.mark.run(order=8)
    def test_deploy_instnace_DefaultNetworkViewScope_as_default_Member(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=9)
    def test_validate_a_record_DefaultNetworkViewScope_as_default_Member(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        for i in range(len(ref_v)):
                   zone = ref_v[i]['fqdn']
                   if zone.startswith(tenant_name):
                        zone_name = ref_v[i]['fqdn']
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

    @pytest.mark.run(order=10)
    def test_validate_a_record_EAs_DefaultNetworkViewScope_as_default_Member(self):
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

    @pytest.mark.run(order=11)
    def test_validate_host_record_entry_DefaultNetworkViewScope_as_default_Member(self):
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

    @pytest.mark.run(order=12)
    def test_validate_host_record_entry_EAs_DefaultNetworkViewScope_as_default_Member(self):
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

    @pytest.mark.run(order=13)
    def test_validate_host_record_entry_mac_address_DefaultNetworkViewScope_as_default_Member(self):
	host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        mac_address_nios = host_records[0]['ipv4addrs'][0]['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
	      mac_address_openstack = ports_list[l]['mac_address']	

        assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=14)
    def test_validate_fixed_address_DefaultNetworkViewScope_as_default_Member(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
            ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']

        assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=15)
    def test_validate_mac_address_fixed_address_DefaultNetworkViewScope_as_default_Member(self):
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

    @pytest.mark.run(order=16)
    def test_validate_fixed_address_EAs_DefaultNetworkViewScope_as_default_Member(self):
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

    @pytest.mark.run(order=17)
    def test_terminate_instance_DefaultNetworkViewScope_as_default_Member(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=18)
    def test_delete_net_subnet_DefaultNetworkViewScope_as_default_Member(self):
        session = util.utils()
        delete_net = session.delete_network(network)
        assert delete_net == ()

    @pytest.mark.run(order=19)
    def test_select_DefaultNetworkViewScope_as_Network(self):
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
                "DNS Support": {"value": "True"},"DNS View": {"value":"default"},\
                "Default Domain Name Pattern": {"value": "{subnet_name}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{ip_address}-{network_name}"},\
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
                "Use Grid Master for DHCP": {"value": "False"},\
		"Is Cloud Member":{"value":"False"},\
                "Zone Creation Strategy": {"value": ["Forward","Reverse"]}}}
          proc = wapi_module.wapi_request('PUT',object_type=ref,fields=json.dumps(data))
          flag = False
          if (re.search(r""+grid_master_name,proc)):
            flag = True
          assert proc != "" and flag
	  time.sleep(5)

    @pytest.mark.run(order=24)
    def test_create_Network_DefaultNetworkViewScope_as_Network_Member(self):
        proc = util.utils()
        proc.create_network(network)
        flag = proc.get_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag1 = proc.get_subnet_name(subnet_name)
        assert flag == network and flag1 == subnet_name

    @pytest.mark.run(order=25)
    def test_validate_network_in_DefaultNetworkViewScope_as_Network_Member(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network',params="?network="+subnet))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        network_id = session.get_network_id(network)
        assert network_nios == subnet and \
               network_view == network+'-'+network_id

    @pytest.mark.run(order=26)
    def test_validate_network_EAs_DefaultNetworkViewScope_as_Network_Member(self):
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

    @pytest.mark.run(order=27)
    def test_validate_zone_DefaultNetworkViewScope_as_Network_Member(self):
	session = util.utils()
        network_id = session.get_network_id(network)
        network_view = 'default.'+network+'-'+network_id
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	for i in range(len(ref_v)):
		   zone = ref_v[i]['fqdn']
        	   if zone.startswith(subnet_name):
			zone_name = ref_v[i]['fqdn']
        assert zone_name == subnet_name+'.cloud.global.com' and \
               network_view == 'default.'+network+'-'+network_id

    @pytest.mark.run(order=28)
    def test_validate_zone_EAs_DefaultNetworkViewScope_as_Network_Member(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        for i in range(len(ref_v)):
                   zone = ref_v[i]['fqdn']
                   if zone.startswith(subnet_name):
                        zone_name = ref_v[i]['fqdn']
        		ref = ref_v[i]['_ref']
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

    @pytest.mark.run(order=29)
    def test_deploy_instnace_DefaultNetworkViewScope_as_Network_Member(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=30)
    def test_validate_a_record_DefaultNetworkViewScope_as_Network_Member(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        for i in range(len(ref_v)):
                   zone = ref_v[i]['fqdn']
                   if zone.startswith(subnet_name):
                        zone_name = ref_v[i]['fqdn']
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
        fqdn = "host-"+'-'.join(ip_address.split('.'))+'-'+network+'.'+zone_name
        assert fqdn == a_record_name

    @pytest.mark.run(order=31)
    def test_validate_a_record_EAs_DefaultNetworkViewScope_as_Network_Member(self):
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

    @pytest.mark.run(order=32)
    def test_validate_host_record_entry_DefaultNetworkViewScope_as_Network_Member(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        for i in range(len(ref_v)):
                   zone = ref_v[i]['fqdn']
                   if zone.startswith(subnet_name):
                        zone_name = ref_v[i]['fqdn']
	host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
	for i in range(len(host_records)):
		host = host_records[i]['name']
		if host.endswith(zone_name):
		     host_record_name = host_records[i]['name']	
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
              ip_address = ports_list[l]['fixed_ips'][0]['ip_address']
        host_record_openstack = "dhcp-port-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert host_record_name == host_record_openstack

    @pytest.mark.run(order=33)
    def test_validate_host_record_entry_EAs_DefaultNetworkViewScope_as_Network__Member(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        for i in range(len(ref_v)):
                   zone = ref_v[i]['fqdn']
                   if zone.startswith(subnet_name):
                        zone_name = ref_v[i]['fqdn']
	host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        for i in range(len(host_records)):
                host = host_records[i]['name']
                if host.endswith(zone_name):
                     	host_record_name = host_records[i]['name']
        	     	ref_v = host_records[i]['_ref']
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

    @pytest.mark.run(order=34)
    def test_validate_host_record_entry_mac_address_DefaultNetworkViewScope_as_Network_Member(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        for i in range(len(ref_v)):
                   zone = ref_v[i]['fqdn']
                   if zone.startswith(subnet_name):
                        zone_name = ref_v[i]['fqdn']
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        for i in range(len(host_records)):
                host = host_records[i]['name']
                if host.endswith(zone_name):
        		mac_address_nios = host_records[i]['ipv4addrs'][0]['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
	for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']
        assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=35)
    def test_validate_fixed_address_DefaultNetworkViewScope_as_Network_Member(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
	for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
               ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']
  	
        assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=36)
    def test_validate_mac_address_fixed_address_DefaultNetworkViewScope_as_Network_Member(self):
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

    @pytest.mark.run(order=37)
    def test_validate_fixed_address_EAs_DefaultNetworkViewScope_as_Network_Member(self):
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

    @pytest.mark.run(order=38)
    def test_terminate_instance_DefaultNetworkViewScope_as_Network_Member(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=39)
    def test_delete_net_subnet_DefaultNetworkViewScope_as_Network_Member(self):
        session = util.utils()
        delete_net = session.delete_network(network)
        assert delete_net == ()

    @pytest.mark.run(order=40)
    def test_select_DefaultNetworkViewScope_as_Subnet(self):
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
                "DNS Support": {"value": "True"},"DNS View": {"value":"default"},\
                "Default Domain Name Pattern": {"value": "{subnet_id}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{ip_address}-{subnet_name}"},\
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
                "Use Grid Master for DHCP": {"value": "False"},\
		"Is Cloud Member":{"value":"False"},\
                "Zone Creation Strategy": {"value": ["Forward","Reverse"]}}}
          proc = wapi_module.wapi_request('PUT',object_type=ref,fields=json.dumps(data))
          flag = False
          if (re.search(r""+grid_master_name,proc)):
            flag = True
          assert proc != "" and flag
	  time.sleep(5)

    @pytest.mark.run(order=41)
    def test_create_Network_DefaultNetworkViewScope_as_Subnet_Member(self):
        proc = util.utils()
        proc.create_network(network)
        flag = proc.get_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag1 = proc.get_subnet_name(subnet_name)
        assert flag == network and flag1 == subnet_name

    @pytest.mark.run(order=42)
    def test_validate_network_in_DefaultNetworkViewScope_as_Subnet_Member(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network',params="?network="+subnet))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        subnet_id = session.get_subnet_id(subnet_name)
        assert network_nios == subnet and \
               network_view == subnet_name+'-'+subnet_id

    @pytest.mark.run(order=43)
    def test_validate_network_EAs_DefaultNetworkViewScope_as_Subnet_Member(self):
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

    @pytest.mark.run(order=44)
    def test_validate_zone_DefaultNetworkViewScope_as_Subnet_Member(self):
	session = util.utils()
        subnet_id = session.get_subnet_id(subnet_name)
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	for i in range(len(ref_v)):
		   zone = ref_v[i]['fqdn']
        	   if zone.startswith(subnet_id):
			zone_name = ref_v[i]['fqdn']
			network_view = ref_v[i]['view']
        assert zone_name == subnet_id+'.cloud.global.com' and \
               network_view == 'default.'+subnet_name+'-'+subnet_id

    @pytest.mark.run(order=45)
    def test_validate_zone_EAs_DefaultNetworkViewScope_as_Subnet_Member(self):
	session = util.utils()
        subnet_id = session.get_subnet_id(subnet_name)
	tenant_id_openstack = session.get_tenant_id(network)
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        for i in range(len(ref_v)):
                   zone = ref_v[i]['fqdn']
                   if zone.startswith(subnet_id):
                        zone_name = ref_v[i]['fqdn']
        		ref = ref_v[i]['_ref']
        		EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=extattrs'))
        		tenant_name_nios = EAs['extattrs']['Tenant Name']['value']
        		tenant_id_nios = EAs['extattrs']['Tenant ID']['value']
        		cmp_type_nios = EAs['extattrs']['CMP Type']['value']
        		cloud_api_owned_nios = EAs['extattrs']['Cloud API Owned']['value']
        assert tenant_id_openstack == tenant_id_nios and \
               tenant_name_nios == tenant_name and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned_nios == 'True'

    @pytest.mark.run(order=46)
    def test_deploy_instnace_DefaultNetworkViewScope_as_Subnet_Member(self):
        proc = util.utils()
        proc.launch_instance(instance_name,network)
        instance = proc.get_server_name(instance_name)
        status = proc.get_server_status(instance_name)
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=47)
    def test_validate_a_record_DefaultNetworkViewScope_as_Subnet_Member(self):
	proc = util.utils()
        ip_add = proc.get_instance_ips(instance_name)
        ip_address = ip_add[network][0]['addr']
	subnet_id=proc.get_subnet_id(subnet_name)
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        for i in range(len(ref_v)):
                   zone = ref_v[i]['fqdn']
                   if zone.startswith(subnet_id):
                        zone_name = ref_v[i]['fqdn']
	count = 1
        while count<=10:
            ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
            if ref_v_a_record == []:
                count = count + 1
                time.sleep(1)
                continue
            a_record_name = ref_v_a_record[0]['name']
            break
	fqdn = "host-"+'-'.join(ip_address.split('.'))+'-'+subnet_name+'.'+zone_name
        assert fqdn == a_record_name

    @pytest.mark.run(order=48)
    def test_validate_a_record_EAs_DefaultNetworkViewScope_as_Subnet_Member(self):
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

    @pytest.mark.run(order=49)
    def test_validate_host_record_entry_DefaultNetworkViewScope_as_Subnet_Member(self):
	proc = util.utils()
        port_list_openstack = proc.list_ports()
        ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
              ip_address = ports_list[l]['fixed_ips'][0]['ip_address']
	subnet_id=proc.get_subnet_id(subnet_name)
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        for i in range(len(ref_v)):
                   zone = ref_v[i]['fqdn']
                   if zone.startswith(subnet_id):
                        zone_name = ref_v[i]['fqdn']
	host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
	for i in range(len(host_records)):
		host = host_records[i]['name']
		if host.endswith(zone_name):
		     host_record_name = host_records[i]['name']	
	host_record_openstack = "dhcp-port-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert host_record_name == host_record_openstack

    @pytest.mark.run(order=50)
    def test_validate_host_record_entry_EAs_DefaultNetworkViewScope_as_Subnet__Member(self):
	proc = util.utils()
	subnet_id=proc.get_subnet_id(subnet_name)
        port_list_openstack = proc.list_ports()
        ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
             port_id_openstack = ports_list[l]['id']
             device_id_openstack = ports_list[l]['device_id']
             device_owner_opstk = 'network:dhcp'
             tenant_id_openstack = ports_list[l]['tenant_id']
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        for i in range(len(ref_v)):
                   zone = ref_v[i]['fqdn']
                   if zone.startswith(subnet_id):
                        zone_name = ref_v[i]['fqdn']
	host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        for i in range(len(host_records)):
                host = host_records[i]['name']
                if host.endswith(zone_name):
                     	host_record_name = host_records[i]['name']
        	     	ref_v = host_records[i]['_ref']
        		EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref_v+'?_return_fields=extattrs'))
        		tenant_id_nios = EAs['extattrs']['Tenant ID']['value']
        		tenant_name_nios = EAs['extattrs']['Tenant Name']['value']
        		port_id_nios = EAs['extattrs']['Port ID']['value']
        		ip_type_nios = EAs['extattrs']['IP Type']['value']
        		device_id_nios = EAs['extattrs']['Port Attached Device - Device ID']['value']
        		device_owner_nios = EAs['extattrs']['Port Attached Device - Device Owner']['value']
        		cmp_type_nios = EAs['extattrs']['CMP Type']['value']
        		cloud_api_owned = EAs['extattrs']['Cloud API Owned']['value']
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'True' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=51)
    def test_validate_host_record_entry_mac_address_DefaultNetworkViewScope_as_Subnet_Member(self):
	proc = util.utils()
	subnet_id=proc.get_subnet_id(subnet_name)
        port_list_openstack = proc.list_ports()
        ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:dhcp' == ports_list[l]['device_owner']):
              mac_address_openstack = ports_list[l]['mac_address']
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        for i in range(len(ref_v)):
                   zone = ref_v[i]['fqdn']
                   if zone.startswith(subnet_id):
                        zone_name = ref_v[i]['fqdn']
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:host'))
        for i in range(len(host_records)):
                host = host_records[i]['name']
                if host.endswith(zone_name):
        		mac_address_nios = host_records[i]['ipv4addrs'][0]['mac']
        assert mac_address_nios == mac_address_openstack

    @pytest.mark.run(order=52)
    def test_validate_fixed_address_DefaultNetworkViewScope_as_Subnet_Member(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
	for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
               ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']
  	
        assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=53)
    def test_validate_mac_address_fixed_address_DefaultNetworkViewScope_as_Subnet_Member(self):
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

    @pytest.mark.run(order=54)
    def test_validate_fixed_address_EAs_DefaultNetworkViewScope_as_Subnet_Member(self):
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

    @pytest.mark.run(order=55)
    def test_terminate_instance_DefaultNetworkViewScope_as_Subnet_Member(self):
        proc = util.utils()
	proc.terminate_instance(instance_name)
	instance = proc.get_server_name(instance_name)
        assert instance == None

    @pytest.mark.run(order=56)
    def test_delete_net_subnet_DefaultNetworkViewScope_as_Subnet_Member(self):
        session = util.utils()
        delete_net = session.delete_network(network)
        assert delete_net == ()



