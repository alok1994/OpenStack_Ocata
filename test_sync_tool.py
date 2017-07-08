import pytest
import unittest
import json
import wapi_module
import re
import time
import util
import os
from netaddr import IPNetwork
import commands
import os, subprocess as sp, json
import subprocess


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

def source(fileName = None, username = None, password = None, update = True):
    pipe = sp.Popen(". {fileName} {username} {password}; env".format(
        fileName=fileName,
        username=username,
        password=password
    ), stdout = subprocess.PIPE, shell = True)
    data = pipe.communicate()[0]
    env = dict((line.split("=", 1) for line in data.splitlines() if (len(line.split("=", 1)) == 2)))
    print env
    if update is True:
        os.environ.update(env)
    return(env)

class TestOpenStackCases(unittest.TestCase):
    @classmethod
    def setup_class(cls):
	source("/home/stack/keystone_admin")
   	pass


    @pytest.mark.run(order=1)
    def test_select_DefaultNetworkView_as_Default_EAs_sync_tool(self):
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
    def test_create_network_DefaultNetworkView_as_Default_EAs_sync_tool(self):
	proc = util.utils()
        proc.create_network(network)
	proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
	flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=3)
    def test_validate_network_DefaultNetworkView_as_Default_EAs_sync_tool(self):
	flag = False	
	proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
	if (re.search(r""+subnet,proc)):
	    flag = True
	assert flag, "Network creation failed "

    @pytest.mark.run(order=4)
    def test_delete_network_NIOS_DefaultNetworkView_as_Default_EAs_sync_tool(self):
        flag = False
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
	resp = json.loads(proc)
	ref_v = resp[0]['_ref']
	delete = wapi_module.wapi_request('DELETE',object_type = ref_v)
        if (re.search(r""+subnet,delete)):
            flag = True
        assert flag, "Network failed to delete"
	time.sleep(60)

    @pytest.mark.run(order=5)
    def test_RUNSYNCTool_network_DefaultNetworkView_as_Default_EAs_sync_tool(self):
        os.system('rm -rf log.txt')
        cmd = 'python /opt/stack/networking-infoblox/networking_infoblox/tools/sync_neutron_to_infoblox.py > log.txt'
        proc = commands.getoutput(cmd)
        a=open('log.txt','rb')
        lines = a.readlines()
        if lines:
           last_line = lines[-1]
        migration = last_line.find('Ending migration...')
        flag = True
        if migration < 1:
            flag = False
        assert flag

    @pytest.mark.run(order=6)
    def test_validate_network_after_synce_DefaultNetworkView_as_Default_EAs_sync_tool(self):
        flag = False
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
        if (re.search(r""+subnet,proc)):
            flag = True
        assert flag, "Network sync failed "

    @pytest.mark.run(order=7)
    def test_validate_network_EAs_after_sync_DefaultNetworkViewScope_as_Default(self):
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

    @pytest.mark.run(order=8)
    def test_delete_net_subnet_DefaultNetworkView_as_Default_EAs_sync_tool(self):
        session = util.utils()
	delete_net = session.delete_network(network)
	assert delete_net == ()

    @pytest.mark.run(order=9)
    def test_select_NetworkViewScope_as_TenantEAs_sync_tool(self):
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
                "Default Network View Scope": {"value": "Tenant"},\
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

    @pytest.mark.run(order=10)
    def test_create_network_DefaultNetworkViewScope_as_Tenant_EAs_sync_tool(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name

    @pytest.mark.run(order=11)
    def test_validate_network_in_DefaultNetworkViewScope_as_Tenant_sync_tool(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        tenant_id = session.get_tenant_id(network)
        assert network_nios == subnet and \
               network_view == tenant_name+'-'+tenant_id

    @pytest.mark.run(order=12)
    def test_delete_network_NIOS_DefaultNetworkViewScope_as_Tenant_sync_tool(self):
        flag = False
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
        resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        delete = wapi_module.wapi_request('DELETE',object_type = ref_v)
        if (re.search(r""+subnet,delete)):
            flag = True
        assert flag, "Network failed to delete"
	time.sleep(60)

    @pytest.mark.run(order=13)
    def test_RUNSYNCTool_DefaultNetworkViewScope_as_Tenant_EAs_sync_tool(self):
        os.system('rm -rf log.txt')
        cmd = 'python /opt/stack/networking-infoblox/networking_infoblox/tools/sync_neutron_to_infoblox.py > log.txt'
        proc = commands.getoutput(cmd)
        a=open('log.txt','rb')
        lines = a.readlines()
        if lines:
           last_line = lines[-1]
        migration = last_line.find('Ending migration...')
        flag = True
        if migration < 1:
            flag = False
        assert flag

    @pytest.mark.run(order=14)
    def test_validate_network_after_SYNC_DefaultNetworkViewScope_as_Tenant_sync_tool(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        tenant_id = session.get_tenant_id(network)
        assert network_nios == subnet and \
               network_view == tenant_name+'-'+tenant_id

    @pytest.mark.run(order=15)
    def test_validate_network_EAs_after_sync_DefaultNetworkViewScope_as_Tenant(self):
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

    @pytest.mark.run(order=16)
    def test_delete_NetworkViewTenant_DefaultNetworkViewScope_as_Tenant_sync_tool(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_view = networks[0]['network_view']
        flag = False
        proc = wapi_module.wapi_request('GET',object_type = 'networkview',params="?name="+network_view)
        resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        delete = wapi_module.wapi_request('DELETE',object_type = ref_v)
        if (re.search(r""+network_view,delete)):
            flag = True
        assert flag, "Network View failed to delete"
        time.sleep(60)

    @pytest.mark.run(order=17)
    def test_RUNSYNCTool_NetworkView_DefaultNetworkView_as_Tenant_EAs_sync_tool(self):
        os.system('rm -rf log.txt')
        cmd = 'python /opt/stack/networking-infoblox/networking_infoblox/tools/sync_neutron_to_infoblox.py > log.txt'
        proc = commands.getoutput(cmd)
        a=open('log.txt','rb')
        lines = a.readlines()
        if lines:
           last_line = lines[-1]
        migration = last_line.find('Ending migration...')
        flag = True
        if migration < 1:
            flag = False
        assert flag

    @pytest.mark.run(order=18)
    def test_validate_NetworkNetworkView_after_SYNC_DefaultNetworkViewScope_as_Tenant(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        tenant_id = session.get_tenant_id(network)
        assert network_nios == subnet and \
               network_view == tenant_name+'-'+tenant_id

    @pytest.mark.run(order=19)
    def test_validate_NetworkNetworkView_EAs_after_sync_DefaultNetworkViewScope_as_Tenant(self):
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

    @pytest.mark.run(order=20)
    def test_delete_net_subnet_DefaultNetworkViewScope_as_Tenant_EAs_sync_tool(self):
        session = util.utils()
        delete_net = session.delete_network(network)
        assert delete_net == ()

    @pytest.mark.run(order=21)
    def test_delete_NetworkViewTenant_DefaultNetworkViewScope_as_Tenant_sync_tool_OpenStack_922(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_view = networks[0]['network_view']
        flag = False
        proc = wapi_module.wapi_request('GET',object_type = 'networkview',params="?name="+network_view)
        resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        delete = wapi_module.wapi_request('DELETE',object_type = ref_v)
        if (re.search(r""+network_view,delete)):
            flag = True
        assert flag, "Network View failed to delete"
        time.sleep(20)

    @pytest.mark.run(order=22)
    def test_select_NetworkViewScope_as_Network_EAs_sync_tool(self):
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
                "Default Network View Scope": {"value": "Network"},\
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
                                              
    @pytest.mark.run(order=23)
    def test_create_network_DefaultNetworkViewScope_as_Network_EAs_sync_tool(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name

    @pytest.mark.run(order=24)
    def test_validate_network_in_DefaultNetworkViewScope_as_Network_EAs_SYNC_Tool(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        network_id = session.get_network_id(network)
        assert network_nios == subnet and \
               network_view == network+'-'+network_id

    @pytest.mark.run(order=25)
    def test_delete_network_NIOS_DefaultNetworkViewScope_as_Network_sync_tool(self):
        flag = False
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
        resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        delete = wapi_module.wapi_request('DELETE',object_type = ref_v)
        if (re.search(r""+subnet,delete)):
            flag = True
        assert flag, "Network failed to delete"
        time.sleep(60)

    @pytest.mark.run(order=26)
    def test_RUNSYNCTool_DefaultNetworkViewScope_as_Network_EAs_sync_tool(self):
        os.system('rm -rf log.txt')
        cmd = 'python /opt/stack/networking-infoblox/networking_infoblox/tools/sync_neutron_to_infoblox.py > log.txt'
        proc = commands.getoutput(cmd)
        a=open('log.txt','rb')
        lines = a.readlines()
        if lines:
           last_line = lines[-1]
        migration = last_line.find('Ending migration...')
        flag = True
        if migration < 1:
            flag = False
        assert flag

    @pytest.mark.run(order=27)
    def test_validate_network_after_sync_DefaultNetworkViewScope_as_Network_EAs_SYNC_Tool(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        network_id = session.get_network_id(network)
        assert network_nios == subnet and \
               network_view == network+'-'+network_id

    @pytest.mark.run(order=28)
    def test_validate_network_EAs_after_sync_DefaultNetworkViewScope_as_Network(self):
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

    @pytest.mark.run(order=29)
    def test_delete_NetworkViewNetwork_DefaultNetworkViewScope_as_Network_sync_tool(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_view = networks[0]['network_view']
        flag = False
        proc = wapi_module.wapi_request('GET',object_type = 'networkview',params="?name="+network_view)
        resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        delete = wapi_module.wapi_request('DELETE',object_type = ref_v)
        if (re.search(r""+network_view,delete)):
            flag = True
        assert flag, "Network View failed to delete"
        time.sleep(60)

    @pytest.mark.run(order=30)
    def test_RUNSYNCTool_NetworkView_DefaultNetworkView_as_Network_EAs_sync_tool(self):
        os.system('rm -rf log.txt')
        cmd = 'python /opt/stack/networking-infoblox/networking_infoblox/tools/sync_neutron_to_infoblox.py > log.txt'
        proc = commands.getoutput(cmd)
        a=open('log.txt','rb')
        lines = a.readlines()
        if lines:
           last_line = lines[-1]
        migration = last_line.find('Ending migration...')
        flag = True
        if migration < 1:
            flag = False
        assert flag

    @pytest.mark.run(order=31)
    def test_validate_NetworkNetworkView_in_DefaultNetworkViewScope_as_Network_EAs_SYNC_Tool(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        network_id = session.get_network_id(network)
        assert network_nios == subnet and \
               network_view == network+'-'+network_id

    @pytest.mark.run(order=32)
    def test_validate_network_EAs_after_NetworkView_Sync_DefaultNetworkViewScope_as_Network(self):
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

    @pytest.mark.run(order=33)
    def test_delete_net_subnet_DefaultNetworkViewScope_as_Network_EAs_sync_tool(self):
        session = util.utils()
        delete_net = session.delete_network(network)
        assert delete_net == ()
 
    @pytest.mark.run(order=34)
    def test_delete_NetworkView_as_Network_DefaultNetworkViewScope_as_Network_sync_tool_OpenStack_922(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_view = networks[0]['network_view']
        flag = False
        proc = wapi_module.wapi_request('GET',object_type = 'networkview',params="?name="+network_view)
        resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        delete = wapi_module.wapi_request('DELETE',object_type = ref_v)
        if (re.search(r""+network_view,delete)):
            flag = True
        assert flag, "Network View failed to delete"
        time.sleep(20)

    @pytest.mark.run(order=35)
    def test_select_DefaultNetworkViewScope_as_Subnet_Sync_tool(self):
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

    @pytest.mark.run(order=36)
    def test_create_network_DefaultNetworkViewScope_as_Subnet_sync_tool(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=37)
    def test_validate_network_DefaultNetworkViewScope_as_Subnet_sync_tool(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        subnet_id = session.get_subnet_id(network)
        assert network_nios == subnet and \
               network_view == subnet_name+'-'+subnet_id

    @pytest.mark.run(order=38)
    def test_delete_network_NIOS_DefaultNetworkViewScope_as_Subnet_sync_tool(self):
        flag = False
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
        resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        delete = wapi_module.wapi_request('DELETE',object_type = ref_v)
        if (re.search(r""+subnet,delete)):
            flag = True
        assert flag, "Network failed to delete"
        time.sleep(60)

    @pytest.mark.run(order=39)
    def test_RUNSYNCTool_DefaultNetworkViewScope_as_Subnet_EAs_sync_tool(self):
        os.system('rm -rf log.txt')
        cmd = 'python /opt/stack/networking-infoblox/networking_infoblox/tools/sync_neutron_to_infoblox.py > log.txt'
        proc = commands.getoutput(cmd)
        a=open('log.txt','rb')
        lines = a.readlines()
        if lines:
           last_line = lines[-1]
        migration = last_line.find('Ending migration...')
        flag = True
        if migration < 1:
            flag = False
        assert flag

    @pytest.mark.run(order=40)
    def test_validate_network_after_sync_DefaultNetworkViewScope_as_Subnet_sync_tool(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        subnet_id = session.get_subnet_id(network)
        assert network_nios == subnet and \
               network_view == subnet_name+'-'+subnet_id

    @pytest.mark.run(order=41)
    def test_validate_network_EAs_after_sync_DefaultNetworkViewScope_as_Subnet(self):
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

    @pytest.mark.run(order=42)
    def test_delete_NetworkView_as_Subnet_DefaultNetworkViewScope_as_Subnet_sync_tool(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_view = networks[0]['network_view']
        flag = False
        proc = wapi_module.wapi_request('GET',object_type = 'networkview',params="?name="+network_view)
        resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        delete = wapi_module.wapi_request('DELETE',object_type = ref_v)
        if (re.search(r""+network_view,delete)):
            flag = True
        assert flag, "Network View failed to delete"
        time.sleep(60)

    @pytest.mark.run(order=43)
    def test_RUNSYNCTool_NetworkView_DefaultNetworkViewScope_as_Subnet_EAs_sync_tool(self):
        os.system('rm -rf log.txt')
        cmd = 'python /opt/stack/networking-infoblox/networking_infoblox/tools/sync_neutron_to_infoblox.py > log.txt'
        proc = commands.getoutput(cmd)
        a=open('log.txt','rb')
        lines = a.readlines()
        if lines:
           last_line = lines[-1]
        migration = last_line.find('Ending migration...')
        flag = True
        if migration < 1:
            flag = False
        assert flag

    @pytest.mark.run(order=44)
    def test_validate_Network_after_NetworkView_sync_DefaultNetworkViewScope_as_Subnet_sync_tool(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        session = util.utils()
        subnet_id = session.get_subnet_id(network)
        assert network_nios == subnet and \
               network_view == subnet_name+'-'+subnet_id

    @pytest.mark.run(order=45)
    def test_validate_Network_EAs_after_NetworkView_sync_DefaultNetworkViewScope_as_Subnet(self):
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

    @pytest.mark.run(order=46)
    def test_delete_net_subnet_DefaultNetworkViewScope_as_Subnet_EAs_sync_tool(self):
        session = util.utils()
        delete_net = session.delete_network(network)
        assert delete_net == ()

    @pytest.mark.run(order=47)
    def test_delete_NetworkView_as_Subnet_DefaultNetworkViewScope_as_Subnet_sync_tool_OpenStack_922(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_view = networks[0]['network_view']
        flag = False
        proc = wapi_module.wapi_request('GET',object_type = 'networkview',params="?name="+network_view)
        resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        delete = wapi_module.wapi_request('DELETE',object_type = ref_v)
        if (re.search(r""+network_view,delete)):
            flag = True
        assert flag, "Network View failed to delete"
        time.sleep(20)

    @pytest.mark.run(order=48)
    def test_add_custom_network_view_sync_tool(self):
        data = {"name":custom_net_view,"extattrs": {"CMP Type":{"value":"OpenStack"},\
                "Cloud API Owned": {"value":"True"},"Cloud Adapter ID":{"value":"1"},\
                "Tenant ID":{"value":"N/A"}}}
        proc = wapi_module.wapi_request('POST',object_type='networkview',fields=json.dumps(data))
        flag = False
        if (re.search(r""+custom_net_view,proc)):
            flag = True
        assert proc != "" and flag

    @pytest.mark.run(order=49)
    def test_select_DefaultNetworkView_as_CustomNetworkView_sync_tool(self):
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

    @pytest.mark.run(order=50)
    def test_create_network_DefaultNetworkView_as_CustomNetworkView_sync_tool(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=51)
    def test_validate_network_DefaultNetworkView_CustomNetwork_sync_tool(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        assert network_nios == subnet and \
               network_view == custom_net_view

    @pytest.mark.run(order=52)
    def test_delete_network_NIOS_DefaultNetworkView_as_CustomNetworkView_sync_tool(self):
        flag = False
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
        resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        delete = wapi_module.wapi_request('DELETE',object_type = ref_v)
        if (re.search(r""+subnet,delete)):
            flag = True
        assert flag, "Network failed to delete"
        time.sleep(60)

    @pytest.mark.run(order=53)
    def test_RUNSYNCTool_DefaultNetworkView_as_CustomNetworkView_EAs_sync_tool(self):
        os.system('rm -rf log.txt')
        cmd = 'python /opt/stack/networking-infoblox/networking_infoblox/tools/sync_neutron_to_infoblox.py > log.txt'
        proc = commands.getoutput(cmd)
        a=open('log.txt','rb')
        lines = a.readlines()
        if lines:
           last_line = lines[-1]
        migration = last_line.find('Ending migration...')
        flag = True
        if migration < 1:
            flag = False
        assert flag

    @pytest.mark.run(order=54)
    def test_validate_network_after_sync_DefaultNetworkView_CustomNetwork_sync_tool(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        assert network_nios == subnet and \
               network_view == custom_net_view

    @pytest.mark.run(order=55)
    def test_validate_network_EAs_DefaultNetworkView_as_CustomNetworkView_sync_tool(self):
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

    @pytest.mark.run(order=56)
    def test_delete_net_subnet_DefaultNetworkView_as_CustomNetworkView_EAs_sync_tool(self):
        session = util.utils()
        delete_net = session.delete_network(network)
        assert delete_net == ()

    @pytest.mark.run(order=57)
    def test_delete_NetworkView_as_CustomNetworkView_DefaultNetworkViewScope_as_CustomNetworkView_sync_tool(self):
        flag = False
        proc = wapi_module.wapi_request('GET',object_type = 'networkview',params="?name="+custom_net_view)
        resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        delete = wapi_module.wapi_request('DELETE',object_type = ref_v)
        if (re.search(r""+custom_net_view,delete)):
            flag = True
        assert flag, "Network View failed to delete"

    @pytest.mark.run(order=58)
    def test_select_TenantName_as_DefaultDomainNamePattern_Update_sync_tool(self):
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
                "Use Grid Master for DHCP": {"value": "True"},\
                "Zone Creation Strategy": {"value": ["Forward","Reverse"]}}}
        proc = wapi_module.wapi_request('PUT',object_type=ref,fields=json.dumps(data))
        flag = False
        if (re.search(r""+grid_master_name,proc)):
            flag = True
        assert proc != "" and flag
        time.sleep(20)

    @pytest.mark.run(order=59)
    def test_create_network_DefaultDomainNamePattern_as_TenantName_update_sync_tool(self):
        proc = util.utils()
        proc.create_network(network)
        proc.create_subnet(network, subnet_name, subnet)
        flag = proc.get_subnet_name(subnet_name)
        flag = proc.get_subnet_name(subnet_name)
        assert flag == subnet_name

    @pytest.mark.run(order=60)
    def test_validate_network_DefaultDomainNamePattern_TenantName_update_sync_tool(self):
        networks = json.loads(wapi_module.wapi_request('GET',object_type='network'))
        network_nios = networks[0]['network']
        network_view = networks[0]['network_view']
        assert network_nios == subnet and \
               network_view == "default"

    @pytest.mark.run(order=61)
    def test_validate_zone_name_DomainNamePattern_as_TenantName_EAs(self):
	ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
	zone_name = ref_v[0]['fqdn']
	assert tenant_name+'.cloud.global.com' == zone_name

    @pytest.mark.run(order=62)
    def test_delete_network_NIOS_DefaultDomainNamePattern_as_TenantName_update_sync_tool(self):
        flag = False
        proc = wapi_module.wapi_request('GET',object_type = 'network',params="?network="+subnet)
        resp = json.loads(proc)
        ref_v = resp[0]['_ref']
        delete = wapi_module.wapi_request('DELETE',object_type = ref_v)
        if (re.search(r""+subnet,delete)):
            flag = True
        assert flag, "Network failed to delete"
        time.sleep(60)

    @pytest.mark.run(order=63)
    def test_select_updated_TenantID_as_DefaultDomainNamePattern_Update_sync_tool(self):
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='member'))
        ref = ref_v[0]['_ref']
        data = {"extattrs":{"Admin Network Deletion": {"value": "True"},\
                "Allow Service Restart": {"value": "True"},\
                "Allow Static Zone Deletion":{"value": "True"},"DHCP Support": {"value": "True"},\
                "DNS Record Binding Types": {"value":["record:a","record:aaaa","record:ptr"]},\
                "DNS Record Removable Types": {"value": ["record:a","record:aaaa","record:ptr","record:txt"]},\
                "DNS Record Unbinding Types": {"value": ["record:a","record:aaaa","record:ptr"]},\
                "DNS Support": {"value": "True"},"DNS View": {"value": "default"},\
                "Default Domain Name Pattern": {"value": "{tenant_id}.cloud.global.com"},\
                "Default Host Name Pattern": {"value": "host-{ip_address}"},\
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
                "Use Grid Master for DHCP": {"value": "True"},\
                "Zone Creation Strategy": {"value": ["Forward","Reverse"]}}}
        proc = wapi_module.wapi_request('PUT',object_type=ref,fields=json.dumps(data))
        flag = False
        if (re.search(r""+grid_master_name,proc)):
            flag = True
        assert proc != "" and flag
        time.sleep(20)

    @pytest.mark.run(order=64)
    def test_RUNSYNCTool_after_update_TenantName_to_TenantID_EAs_sync_tool(self):
        os.system('rm -rf log.txt')
        cmd = 'python /opt/stack/networking-infoblox/networking_infoblox/tools/sync_neutron_to_infoblox.py > log.txt'
        proc = commands.getoutput(cmd)
        a=open('log.txt','rb')
        lines = a.readlines()
        if lines:
           last_line = lines[-1]
        migration = last_line.find('Ending migration...')
        flag = True
        if migration < 1:
            flag = False
        assert flag

    @pytest.mark.run(order=65)
    def test_validate_zone_name_after_update_DomainNamePattern_as_TenantID_EAs(self):
	import pdb;pdb.set_trace()
	session = util.utils()
        tenant_id = session.get_tenant_id(network)
        ref_v = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v[0]['fqdn']
	zone_name1 = ref_v[1]['fqdn']
	flag = False
	if zone_name == tenant_id+'.cloud.global.com':
	    flag = True
	elif zone_name1 == tenant_id+'.cloud.global.com':
	    flag = True
        assert flag

    @pytest.mark.run(order=66)
    def test_validate_host_record_entry_after_update_DomainNamePattern(self):
	session = util.utils()
        tenant_id = session.get_tenant_id(network)
	ref_v_zone = json.loads(wapi_module.wapi_request('GET',object_type='zone_auth'))
        zone_name = ref_v_zone[0]['fqdn']
	zone_name1 = ref_v_zone[1]['fqdn']
	if zone_name == tenant_id+'.cloud.global.com':
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
	else:
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

            host_record_openstack = "dhcp-port-"+'-'.join(ip_address.split('.'))+'.'+zone_name1

        assert host_record_name == host_record_openstack
