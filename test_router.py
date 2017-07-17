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
                "External Domain Name Pattern": {"value": "{subnet_name}.external.global.com"},\
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
    def test_validate_zone_name_ExternalDomainNamePattern_as_SubnetName_router(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
        assert ext_subnet_name+'.external.global.com' == zone_name

    @pytest.mark.run(order=5)
    def test_validate_a_record_for_router(self):
	ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        a_records = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
        a_record_name = a_records[0]['name']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'network:router_gateway':
            ip_address = port_list_openstack['ports'][0]['fixed_ips'][0]['ip_address']
        else:
            ip_address = port_list_openstack['ports'][1]['fixed_ips'][0]['ip_address']

        a_record_openstack = "router-gw-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert a_record_name == a_record_openstack

    @pytest.mark.run(order=6)
    def test_validate_a_record_EAs_router(self):
	host_records = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
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
	tenant_id_openstack = proc.get_tenant_id(ext_network)
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'network:router_gateway':
             port_id_openstack = port_list_openstack['ports'][0]['id']
             device_id_openstack = port_list_openstack['ports'][0]['device_id']
             device_owner_opstk = 'network:router_gateway'
        else:
             port_id_openstack = port_list_openstack['ports'][1]['id']
             device_id_openstack = port_list_openstack['ports'][1]['device_id']
             device_owner_opstk = 'network:router_gateway'
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=7)
    def test_validate_fixed_address_for_router(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        fixed_address_nios = ref_v[0]['ipv4addr']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'network:router_gateway':
            ip_address_opstk = port_list_openstack['ports'][0]['fixed_ips'][0]['ip_address']
	else: 
            ip_address_opstk = port_list_openstack['ports'][1]['fixed_ips'][0]['ip_address']

        assert fixed_address_nios == ip_address_opstk

    @pytest.mark.run(order=8)
    def test_validate_mac_address_fixed_address_for_router(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
        ref = ref_v[0]['_ref']
        mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=mac'))
        mac_add_nios = mac_add['mac']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'network:router_gateway':
            mac_address_openstack = port_list_openstack['ports'][0]['mac_address']
        else:
            mac_address_openstack = port_list_openstack['ports'][1]['mac_address']
        assert mac_add_nios == mac_address_openstack

    @pytest.mark.run(order=9)
    def test_validate_fixed_address_EAs_router(self):
        host_records = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress'))
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
        tenant_id_openstack = proc.get_tenant_id(ext_network)
        device_owner_openstack = port_list_openstack['ports'][0]['device_owner']
        device_owner1_openstack = port_list_openstack['ports'][1]['device_owner']
        if device_owner_openstack == 'network:router_gateway':
             port_id_openstack = port_list_openstack['ports'][0]['id']
             device_id_openstack = port_list_openstack['ports'][0]['device_id']
             device_owner_opstk = 'network:router_gateway'
        else:
             port_id_openstack = port_list_openstack['ports'][1]['id']
             device_id_openstack = port_list_openstack['ports'][1]['device_id']
             device_owner_opstk = 'network:router_gateway'
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'False' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=10)
    def test_create_network_for_router(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=11)
    def test_validate_zone_name_DomainNamePattern_as_TenantName_EAs_router(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	flag = False
	for l in range(len(ref_v)):
	    zone_name = ref_v[l]['fqdn']
            if (zone_name.startswith((tenant_name)) and zone_name.endswith(('.cloud.global.com'))):
	        flag = True
	assert flag

    @pytest.mark.run(order=12)
    def test_add_InternalNetwork_to_router_interface(self):
	proc = util.utils()
	proc.add_router_interface(interface_name,router_name,subnet_name)
	router_opstk = proc.get_routers_name(router_name)
	assert router_opstk == router_name

    @pytest.mark.run(order=13)
    def test_validate_a_record_from_internal_network_for_router(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        for l in range(len(ref_v_zone)):
           zone_names = ref_v_zone[l]['fqdn']
           if zone_names.startswith((tenant_name)) and zone_names.endswith(('.cloud.global.com')):
	       zone_name = ref_v_zone[l]['fqdn']
        a_records = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
	for l in range(len(a_records)):
	   ref_v = a_records[l]['_ref']
	   if (ref_v.endswith((tenant_name+'.cloud.global.com/default'))):
	       a_record_name = a_records[l]['name']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
	for l in range(len(ports_list)):
           if ('network:router_interface' == ports_list[l]['device_owner']):
	       ip_address = ports_list[l]['fixed_ips'][0]['ip_address']

        a_record_openstack = "router-iface-"+'-'.join(ip_address.split('.'))+'.'+zone_name
        assert a_record_name == a_record_openstack

    @pytest.mark.run(order=14)
    def test_validate_fixed_address_for_router_of_internal_Network(self):
        proc = util.utils()
        port_list_openstack = proc.list_ports()
	ports_list = port_list_openstack['ports']
	for l in range(len(ports_list)):
           if ('network:router_interface' == ports_list[l]['device_owner']):
               ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress',params="?ipv4addr="+ip_address_opstk))
	fixed_address_nios = ref_v[0]['ipv4addr']
        assert fixed_address_nios == ip_address_opstk
    
    @pytest.mark.run(order=15)
    def test_validate_fixed_address_EAs_router_for_internal_network(self):
	proc = util.utils()
        port_list_openstack = proc.list_ports()
        ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:router_interface' == ports_list[l]['device_owner']):
               ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']
	       port_id_openstack = ports_list[l]['id']
	       device_id_openstack = ports_list[l]['device_id']
	       device_owner_opstk = 'network:router_interface'
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress',params="?ipv4addr="+ip_address_opstk))
        ref_v_fixaddr = ref_v[0]['_ref']
        EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref_v_fixaddr+'?_return_fields=extattrs'))
        tenant_id_nios = EAs['extattrs']['Tenant ID']['value']
        tenant_name_nios = EAs['extattrs']['Tenant Name']['value']
        port_id_nios = EAs['extattrs']['Port ID']['value']
        ip_type_nios = EAs['extattrs']['IP Type']['value']
        device_id_nios = EAs['extattrs']['Port Attached Device - Device ID']['value']
        device_owner_nios = EAs['extattrs']['Port Attached Device - Device Owner']['value']
        cmp_type_nios = EAs['extattrs']['CMP Type']['value']
        cloud_api_owned = EAs['extattrs']['Cloud API Owned']['value']
        tenant_id_openstack = proc.get_tenant_id(network)
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'True' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=16)
    def test_validate_mac_address_fixed_address_for_router_of_internal_network(self):
	proc = util.utils()
        port_list_openstack = proc.list_ports()
        ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:router_interface' == ports_list[l]['device_owner']):
               ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']
	       mac_address_openstack = ports_list[l]['mac_address']
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress',params="?ipv4addr="+ip_address_opstk))
        ref = ref_v[0]['_ref']
        mac_add = json.loads(wapi_module.wapi_request('GET',object_type=ref+'?_return_fields=mac'))
        mac_add_nios = mac_add['mac']
	
        assert mac_add_nios == mac_address_openstack

    @pytest.mark.run(order=17)
    def test_validate_a_record_EAs_InternalNetwrok_Interface_router(self):
	a_records = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
        for l in range(len(a_records)):
           ref_v = a_records[l]['_ref']
           if (ref_v.endswith((tenant_name+'.cloud.global.com/default'))):
	       ref_v_a = a_records[l]['_ref']
	EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref_v_a+'?_return_fields=extattrs'))
	tenant_id_nios = EAs['extattrs']['Tenant ID']['value']
        tenant_name_nios = EAs['extattrs']['Tenant Name']['value']
        port_id_nios = EAs['extattrs']['Port ID']['value']
        ip_type_nios = EAs['extattrs']['IP Type']['value']
        device_id_nios = EAs['extattrs']['Port Attached Device - Device ID']['value']
        device_owner_nios = EAs['extattrs']['Port Attached Device - Device Owner']['value']
        cmp_type_nios = EAs['extattrs']['CMP Type']['value']
	cloud_api_owned = EAs['extattrs']['Cloud API Owned']['value']
	proc = util.utils()
	tenant_id_openstack = proc.get_tenant_id(ext_network)
        port_list_openstack = proc.list_ports()
        ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('network:router_interface' == ports_list[l]['device_owner']):
               port_id_openstack = ports_list[l]['id']
               device_id_openstack = ports_list[l]['device_id']
               device_owner_opstk = 'network:router_interface'
        assert tenant_id_nios == tenant_id_openstack and \
               port_id_nios == port_id_openstack and \
               tenant_name_nios == tenant_name and \
               ip_type_nios == 'Fixed' and \
               device_owner_nios == device_owner_opstk and \
               cmp_type_nios == 'OpenStack' and \
               cloud_api_owned == 'True' and \
               device_id_nios == device_id_openstack

    @pytest.mark.run(order=18)
    def test_deploy_instnace_with_internal_network_router(self):
	proc = util.utils()
	proc.launch_instance(instance_name,network)
	instance = proc.get_server_name()
        status = proc.get_server_status()
	assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=19)
    def test_validate_a_record_of_instance_from_internal_network(self):
        a_records = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
        for l in range(len(a_records)):
           record_name = a_records[l]['name']
           if (record_name.startswith(('host-'))):
               fqdn_nios = a_records[l]['name']
	ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        for l in range(len(ref_v_zone)):
           zone_names = ref_v_zone[l]['fqdn']
           if zone_names.startswith((tenant_name)) and zone_names.endswith(('.cloud.global.com')):
               zone_name = ref_v_zone[l]['fqdn']
        proc = util.utils()
        port_list_openstack = proc.list_ports()
        ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
               ip_address = ports_list[l]['fixed_ips'][0]['ip_address']
	       fqdn = "host-"+'-'.join(ip_address.split('.'))+'.'+zone_name
	assert fqdn_nios == fqdn

    @pytest.mark.run(order=20)
    def test_validate_a_record_EAs_of_instance_from_internal_network(self):
        a_records = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
        for l in range(len(a_records)):
           record_name = a_records[l]['name']
           if (record_name.startswith(('host-'))):
               fqdn_nios = a_records[l]['name']
        records = json.loads(wapi_module.wapi_request('GET',object_type='record:a',params="?name="+fqdn_nios))
	ref_v_a = records[0]['_ref']
        EAs = json.loads(wapi_module.wapi_request('GET',object_type=ref_v_a+'?_return_fields=extattrs'))
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

    @pytest.mark.run(order=21)
    def test_validate_fixed_address_for_instance_using_internal_network(self):
        proc = util.utils()
        port_list_openstack = proc.list_ports()
        ports_list = port_list_openstack['ports']
        for l in range(len(ports_list)):
           if ('compute:None' == ports_list[l]['device_owner']):
	       ip_address_opstk = ports_list[l]['fixed_ips'][0]['ip_address']

	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='fixedaddress',params="?ipv4addr="+ip_address_opstk))
        fixed_address_nios = ref_v[0]['ipv4addr']
	
        assert fixed_address_nios == ip_address_opstk


'''
    @pytest.mark.run(order=7)
    def test_attach_floating_ip(self):
	proc = util.utils()
	proc.add_floating_ip(interface_name,instance_name,ext_network,ext_subnet_name)
'''

	
