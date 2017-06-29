import pytest
import unittest
import json
import wapi_module
import re
import time
import util
import create_address_scope
import os
from netaddr import IPNetwork
import commands

tenant_name = 'admin'
network = 'net1'
subnet_name = "snet"
instance_name = 'inst'
subnet = "10.2.0.0/24"
grid_ip = "10.39.12.121"
grid_master_name = "infoblox.localdomain"
custom_net_view = "openstack_view"
custom_DNS_view = "dns_view"
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
        instance = proc.get_server_name()
        status = proc.get_server_status()
        assert instance_name == instance and status == 'ACTIVE'

    @pytest.mark.run(order=214)
    def test_validate_a_record_DefaultNetworkViewScope_as_AddressScope(self):
        ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
        ref_v_a_record = json.loads(wapi_module.wapi_request('GET',object_type='record:a'))
        a_record_name = ref_v_a_record[0]['name']
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

    @pytest.mark.run(order=216)
    def test_validate_host_record_entry_DefaultNetworkViewScope_as_AddressScope(self):
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

    @pytest.mark.run(order=218)
    def test_validate_host_record_entry_mac_address_DefaultNetworkViewScope_as_AddressScope(self):
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

    @pytest.mark.run(order=219)
    def test_validate_fixed_address_DefaultNetworkViewScope_as_AddressScope(self):
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

    @pytest.mark.run(order=220)
    def test_validate_mac_address_fixed_address_DefaultNetworkViewScope_as_AddressScope(self):
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

    @pytest.mark.run(order=222)
    def test_terminate_instance_DefaultNetworkViewScope_as_Tenant(self):
        proc = util.utils()
        server = proc.terminate_instance()
        assert server == None

    @pytest.mark.run(order=223)
    def test_delete_net_subnet_DefaultNetworkViewScope_as_Tenant(self):
        session = util.utils()
        delete_net = session.delete_network(network)
        assert delete_net == None

