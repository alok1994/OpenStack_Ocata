from keystoneauth1 import identity
from keystoneauth1 import session
from neutronclient.v2_0 import client
import os,sys
from novaclient.client import Client
import time
import commands
import ConfigParser

CONF="config.ini"
parser = ConfigParser.SafeConfigParser()
parser.read(CONF)
Host_IP =  parser.get('Local-Host', 'Host_IP')
User_Name = parser.get('Local-Host', 'User_Name')
Password =  parser.get('Local-Host', 'Password')
Tenant =  parser.get('Local-Host', 'Tenant')
Project_Name =  parser.get('Local-Host', 'Project_Name')
Project_Domain_ID = parser.get('Local-Host', 'Project_Domain_ID')
User_Domain_ID = parser.get('Local-Host', 'User_Domain_ID')
Keysstone_Version = parser.get('Local-Host', 'Keysstone_Version')

class utils:
	def __init__(self):
            username=User_Name
            password=Password
	    tenant_name=Tenant
            project_name=Project_Name
            project_domain_id=User_Domain_ID
            user_domain_id=User_Domain_ID
	    keystone_version = Keysstone_Version
	    if keystone_version == 'v3':
               auth_url='http://'+Host_IP+':5000/v3'
	       VERSION = '2'
               auth = identity.Password(auth_url=auth_url,
                             username=username,
                             password=password,
                             project_name=project_name,
                             project_domain_id=project_domain_id,
                             user_domain_id=user_domain_id)
               sess = session.Session(auth = auth)
               self.neutron = client.Client(session=sess)
	       self.nova_client = Client(VERSION,session=sess)
	    else:
	       auth_url='http://'+Host_IP+':5000/v2.0'
	       VERSION = '2'
	       auth = identity.Password(auth_url=auth_url,
		             tenant_name=tenant_name,
                             username=username,
                             password=password)
               sess = session.Session(auth = auth)
               self.neutron = client.Client(session=sess)
               self.nova_client = Client(VERSION,session=sess)

	def create_network(self,name, external=False, shared=False):
	    ''''
	    Add a Network OpenStack Side
	      Pass the Network Name as Arg
	    '''
            network_details = {'network': {'name': name, 'admin_state_up': True, 'router:external' : external, 'shared': shared}}
            networks_body = self.neutron.create_network(body=network_details)
	    network = networks_body['network']['name']
            return network
	
	def get_network(self,name):
	    networks_list = self.neutron.list_networks(name)
            qa_networks = networks_list['networks']
            for l in range(len(qa_networks)):
                if name == qa_networks[l]['name']:
                   return qa_networks[l]['name']

	def get_network_id(self,name):
	    networks_list = self.neutron.list_networks(name)
	    qa_networks = networks_list['networks']
	    for l in range(len(qa_networks)):
                if name == qa_networks[l]['name']:
                   return qa_networks[l]['id']

	def get_tenant_id(self,name):
	    tenant = self.neutron.list_networks(name)
            tenant_id = tenant['networks'][0]['tenant_id']
            return tenant_id

	def delete_network(self,name):
            network_id = self.get_network_id(name)
	    delete_net = self.neutron.delete_network(network_id)
            return delete_net
	
	def update_network(self,network_name,update_network_name):
            network = self.get_network_id(network_name)
	    network_details = {'network': {'name': update_network_name}}
	    updated_network = self.neutron.update_network(network,body=network_details)
	    modified_network = updated_network['network']['name']
            return modified_network
	
	def create_subnet(self, network_name, subnet_name, subnet,ip_version = 4):
            """
               Creates a Subnet
               It takes Network Name, Subnet Name and Subnet as arguments.
               For Example:-
               project.create_subnet("Network1", "Subnet-1-1", "45.0.0.0/24")
            """
            net_id = self.get_network_id(network_name)
	    tenant_id = self.get_tenant_id(network_name)
            body_create_subnet = {'subnets': [{'name': subnet_name, 'cidr': subnet, 'ip_version': ip_version,\
                                  'tenant_id': tenant_id, 'network_id': net_id}]}
            subnet = self.neutron.create_subnet(body=body_create_subnet)

	def get_subnet_name(self,subnet_name):
            subnets_list = self.neutron.list_subnets(subnet_name)
	    qa_subnets = subnets_list['subnets']
	    for l in range(len(qa_subnets)):
	        if subnet_name == qa_subnets[l]['name']:
                   return subnet_name
	  
        def get_subnet_id(self,subnet_name):
	    subnets_list = self.neutron.list_subnets(subnet_name)
            qa_subnets = subnets_list['subnets']
            for l in range(len(qa_subnets)):
                if subnet_name == qa_subnets[l]['name']:
                   return qa_subnets[l]['id']

	def delete_subnet(self,subnet_name):
	    sub_id = self.get_subnet_id(subnet_name)
	    delete_sub = self.neutron.delete_subnets(sub_id)
	    return None	    

	def update_subnet(self,subnet_name,update_subnet_name):
            subnet_id = self.get_subnet_id(subnet_name)
            subnet_details = {'subnet': {'name': update_subnet_name}}
            updated_subnet = self.neutron.update_subnet(subnet_id,body=subnet_details)
            modified_subnet = updated_subnet['subnet']['name']
            return modified_subnet

        def launch_instance(self, name, net_name):
            """
              Return Server Object if the instance is launched successfully
        
              It takes Instance Name and the Network Name it should be associated with as arguments.
            """
            image = self.nova_client.images.find(name="cirros-0.3.3-x86_64-disk")
            flavor = self.nova_client.flavors.find(name="m1.nano")
            net_id  = self.get_network_id(net_name)
	    nic_id = [{'net-id': net_id}]
            instance = self.nova_client.servers.create(name=name, image=image,\
                                                       flavor=flavor, nics=nic_id)
	    count = 60
            while True:
		instances = self.nova_client.servers.list()
		for instance in range(len(instances)):
                  if name == instances[instance].name:
                     status = instances[instance].status
		if status != 'ACTIVE' or count <= 0:
		    time.sleep(1)
		    count = count - 1
                    continue
                break

        def get_servers_list(self):
            """i
              Return List of Servers
            """
            return self.nova_client.servers.list()

	def get_servers_id(self,instance_name):
            """
              Return server id
            """ 
            instances = self.nova_client.servers.list()
	    for instance in range(len(instances)):
                if instance_name == instances[instance].name:
                    return instances[instance].id

	def get_server_status(self,instance_name):
	    instances = self.nova_client.servers.list()
	    for instance in range(len(instances)):
                if instance_name == instances[instance].name:
                    return instances[instance].status

	def get_server_name(self,instance_name):
            """
              Return Server Object for a given instance name
            """
	    instances = self.nova_client.servers.list()
            for instance in range(len(instances)):
                if instance_name == instances[instance].name:
		    return instances[instance].name
		
        def get_server_tenant_id(self):
            instances = self.nova_client.servers.list()
            for instance in instances:
                return instance.tenant_id
	
	def get_server_tenant_name(self):
            instances = self.nova_client.servers.list()
            for instance in instances:
                return instance.tenant_name

	def terminate_instance(self,instance_name):
            """
              Terminates an instance
              It takes Instance Name as argument.
            """
            server = self.get_servers_id(instance_name)
            servers = self.nova_client.servers.delete(server)
            count = 60
            while True:
                check_del=self.get_server_name(instance_name)
                if check_del != None and count != 0:
		      time.sleep(1)
                      count = count - 1
                      continue
                else:
                    break

	def update_instance(self,instance_name,updated_server_name):
	    server_id = self.get_servers_id(instance_name)
            updated_instance = self.nova_client.servers.update(server_id,name=updated_server_name)
	    return updated_instance

	def list_ports(self, retrieve_all=True):
            """
               Fetches a list of all ports for a project.
            """
            ports = self.neutron.list_ports()
	    return ports

    	def create_router(self, router_name, network_name):
            net_id = self.get_network_id(network_name)
            route = {'router': {'name': router_name, 'admin_state_up': True, 'external_gateway_info': {'network_id': net_id}}}
            router = self.neutron.create_router(body=route)

	def get_routers_name(self,router_name):
            routers = self.neutron.list_routers(router_name)
	    router = routers['routers'][0]['name']
            return router

    	def get_router_id(self, route_name):
	    routers = self.neutron.list_routers()
	    router_id = routers['routers'][0]['id']
	    return router_id

        def delete_router(self, router_name):
            router_id = self.get_router_id(router_name)
            return self.neutron.delete_router(router=router_id)

    	def create_port(self, interface_name, network_name):
            net_id = self.get_network_id(network_name)
            port = {'port': {'name': interface_name, 'admin_state_up': True, 'network_id': net_id}}
            port_info = self.neutron.create_port(body=port)
	    return port_info

    	def get_ports(self,interface_name):
            ports = self.neutron.list_ports(interface_name)
            port_name = ports['ports'][0]['name']
	    return port_name

    	def get_port_id(self):
	    ports = self.neutron.list_ports()
            port_id = ports['ports'][0]['id']
	    return port_id

    	def add_router_interface(self, interface_name, router_name,subnet_name):
            router_id = self.get_router_id(router_name)
	    sub_id = self.get_subnet_id(subnet_name)
            body = {'subnet_id':sub_id}
            router = self.neutron.add_interface_router(router=router_id, body=body)

    	def remove_router_interface(self,router_name,port_id):
            router_id = self.get_router_id(router_name)
            body = {'port_id':port_id}
            router = self.neutron.remove_interface_router(router=router_id, body=body)

    	def add_floating_ip(self, interface_name,instance_name,ext_net,ext_subnet):
	    ports = self.create_port(interface_name,ext_net)
            floating_ip = self.nova_client.floating_ips.create(self.nova_client.floating_ip_pools.list()[0].name)
            instance = self.nova_client.servers.find(name=instance_name)
            instance.add_floating_ip(floating_ip)

    	def delete_floating_ip(self, instance_name):
            fip_list = self.nova_client.floating_ips.list()
            floating_ip = fip_list[0].ip
            floating_ip_id = fip_list[0].id
            instance = self.nova_client.servers.find(name=instance_name)
            instance.remove_floating_ip(floating_ip)
            self.nova_client.floating_ips.delete(floating_ip_id)

	def get_instance_name(self, instance):
            name = instance.name
            return name

    	def get_instance_ips(self, instance_name):
            instance = self.nova_client.servers.find(name=instance_name)
            ips_add = self.nova_client.servers.ips(instance.id)
            return ips_add

    	def interface_attach(self, server, network):
            net_id = self.get_network_id(network)
            iface = self.nova_client.servers.interface_attach(port_id='',fixed_ip='',server=server,net_id=net_id,)
            return iface

    	def interface_detach(self, server, port_id):
            self.nova_client.servers.interface_detach(server=server, port_id=port_id) 

        def address_scopes_list(self,name,retrieve_all=True):
            """Fetches a list of all address scopes for a project."""
            names = self.neutron.list_address_scopes(name)
	    return names

        #def show_address_scope(self, address_scope, **_params):
        #    """Fetches information of a certain address scope."""
        #    return self.get(self.address_scope_path % (address_scope),
        #                params=_params)

        def add_address_scope(self,name,ip_version):
            """Creates a new address scope."""
            body = {'address_scope': {'ip_version': ip_version, 'name': name}}
	    addressScope = self.neutron.create_address_scope(body=body)
	    return addressScope

        #def update_address_scope(self, address_scope, body=None):
        #    """Updates a address scope."""
        #    return self.put(self.address_scope_path % (address_scope), body=body)

        def delete_address_scopes(self, address_scope):
            """Deletes the specified address scope."""
	    address_list = self.address_scopes_list(address_scope)
            address_id = address_list['address_scopes'][0]['id']
	    delete = self.neutron.delete_address_scope(address_id)
            return delete

	def add_address_scope_subnetpool(self,address_network,add_sub_name,subnet,prefixlen): 
            address_list = self.address_scopes_list(address_network)
	    address_id = address_list['address_scopes'][0]['id']
            tenant_id = address_list['address_scopes'][0]['tenant_id']
            body_create_subnet = {'subnetpool': {'name': add_sub_name,'address_scope_id':address_id,\
                                  'tenant_id': tenant_id,'prefixes':[subnet],'default_prefixlen':prefixlen}}
            subnetpool = self.neutron.create_subnetpool(body=body_create_subnet)
	    return subnetpool

	def subnetpool_list(self,name,retrieve_all=True):
	    names = self.neutron.list_subnetpools(name)
	    return names

	def add_subnet_address_scope(self,networkName,address_pool_name,subnetName):
	    subnetpools_id = self.subnetpool_list(address_pool_name)
	    subnetpool_id = subnetpools_id['subnetpools'][0]['id']
            tenant_id = subnetpools_id['subnetpools'][0]['tenant_id']
	    self.create_network(networkName)
            net_id = self.get_network_id(networkName)	
            body_create_subnet = {'subnets': [{'name': subnetName,'ip_version':4,\
                                  'tenant_id': tenant_id, 'subnetpool_id': subnetpool_id,'network_id':net_id}]}
            subnet = self.neutron.create_subnet(body=body_create_subnet)
	    return subnet 

	def delete_subnetpool(self,subnetpool_name):
	    subnetpools = self.subnetpool_list(subnetpool_name)
	    subnetpool_id = subnetpools['subnetpools'][0]['id']
	    delete = self.neutron.delete_subnetpool(subnetpool_id)
	    return delete

	def delete_port(self, port_id):
            """Deletes the specified port."""
            return self.neutron.delete_port(port_id)
	
	def flavor_create(self,flavor_name,CPU,RAM,DISK):
	    flavor = self.nova_client.flavors.create(name=flavor_name,ram=RAM,vcpus=CPU,disk=DISK)
	    return flavor

	def flavor_get(self,flavor_name):
            flavors = self.nova_client.flavors.find(name=flavor_name)
            return flavors
	
	def flavor_list(self):
            flavors = self.nova_client.flavors.list()
            return flavors

