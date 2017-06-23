from keystoneauth1 import identity
from keystoneauth1 import session
from neutronclient.v2_0 import client
import os,sys
from novaclient.client import Client
import time
#os.system('export OS_USERNAME=admin')
#os.system('export OS_PASSWORD=admin')
#os.system('export OS_TENANT_NAME=admin')
#os.system('export OS_AUTH_URL=http://10.39.12.231:35357/v3')
class utils:
	def __init__(self):
            username='admin'
            password='admin'
            project_name='admin'
            project_domain_id='default'
            user_domain_id='default'
            auth_url='http://10.39.12.121:5000/v3'
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

	def create_network(self,name, external=False):
	    ''''
	    Add a Network OpenStack Side
	      Pass the Network Name as Arg
	    '''
            network = {'network': {'name': name, 'admin_state_up': True, 'router:external' : external}}
            netw = self.neutron.create_network(body=network)
	
	def get_network(self,name):
	    networks = self.neutron.list_networks(name)
	    net_name = networks['networks'][0]['name']
	    return net_name

	def get_network_id(self,name):
	    networks = self.neutron.list_networks(name)
	    network_id = networks['networks'][0]['id']
	    return network_id

	def get_tenant_id(self,name):
	    tenant = self.neutron.list_networks(name)
            tenant_id = tenant['networks'][0]['tenant_id']
            return tenant_id

	def delete_network(self,name):
            networks = self.neutron.list_networks(name)
            network_id = networks['networks'][0]['id']
	    delete_net = self.neutron.delete_network(network_id)
            return None
	
	def create_subnet(self, network_name, subnet_name, subnet):
            """
               Creates a Subnet
               It takes Network Name, Subnet Name and Subnet as arguments.
               For Example:-
               project.create_subnet("Network1", "Subnet-1-1", "45.0.0.0/24")
            """
            net_id = self.get_network_id(network_name)
	    tenant_id = self.get_tenant_id(network_name)
            body_create_subnet = {'subnets': [{'name': subnet_name, 'cidr': subnet, 'ip_version': 4,\
                                  'tenant_id': tenant_id, 'network_id': net_id}]}
            subnet = self.neutron.create_subnet(body=body_create_subnet)

	def get_subnet_name(self,subnet_name):
            subnets = self.neutron.list_subnets(subnet_name)
            sub_name = subnets['subnets'][0]['name']
            return sub_name

        def get_subnet_id(self,subnet_name):
            subnets = self.neutron.list_subnets(subnet_name)
            sub_id = subnets['subnets'][0]['id']
            return sub_id

	def delete_subnet(self,subnet_name):
 	    subnets = self.neutron.list_subnets(subnet_name)
            sub_id = subnets['subnets'][0]['id']
	    delete_sub = self.neutron.delete_subnets(sub_id)
	    return None	    

        def launch_instance(self, name, net_name):
            """
              Return Server Object if the instance is launched successfully
        
              It takes Instance Name and the Network Name it should be associated with as arguments.
            """
            image = self.nova_client.images.find(name="cirros-0.3.4-x86_64-uec")
            flavor = self.nova_client.flavors.find(name="m1.tiny")
            net_id  = self.get_network_id(net_name)
	    nic_id = [{'net-id': net_id}]
            instance = self.nova_client.servers.create(name=name, image=image,\
                                                       flavor=flavor, nics=nic_id)
            time.sleep(30)
            #return instance

        def get_servers_list(self):
            """
              Return List of Servers
            """
            return self.nova_client.servers.list()

	def get_servers_id(self):
            """
              Return server id
            """ 
            instances = self.nova_client.servers.list()
	    for instance in instances:
	        return instance.id

	def get_server_status(self):
	    instances = self.nova_client.servers.list()
            for instance in instances:
                return instance.status

	def get_server_name(self):
            """
              Return Server Object for a given instance name
            """
	    instances = self.nova_client.servers.list()
            for instance in instances:
                return instance.name

        def get_server_tenant_id(self):
            instances = self.nova_client.servers.list()
            for instance in instances:
                return instance.tenant_id
	
	def get_server_tenant_name(self):
            instances = self.nova_client.servers.list()
            for instance in instances:
                return instance.tenant_name

	def terminate_instance(self):
            """
              Terminates an instance
              It takes Instance Name as argument.
            """
            server = self.get_servers_id()
            if server:
                self.nova_client.servers.delete(server)
                time.sleep(30)
		return None
	    else:
		server = self.get_servers_id()
		return server

	def list_ports(self, retrieve_all=True):
            """
               Fetches a list of all ports for a project.
            """
            # Pass filters in "params" argument to do_request
            ports = self.neutron.list_ports()
	    return ports

    	def create_router(self, router_name, network_name):
            net_id = self.get_network_id(network_name)
            route = {'router': {'name': router_name, 'admin_state_up': True, 'external_gateway_info': {'network_id': net_id1}}}
            router = self.neutron.create_router(body=route)

	def get_routers_name(self,router_name):
            routers = self.neutron.list_routers(router_name)
	    router = routers['routers'][0]['name']
            return router

    	def get_router_id(self, route_name):
	    routers = self.neutron.list_router()
	    router_id = routers['routers'][0]['id']
	    return router_id

        def delete_router(self, router_name):
            router_id = self.get_router_id(router_name)
            self.neutron.delete_router(router=router_id)

    	def create_port(self, interface_name, network_name):
            net_id = self.get_network_id(network_name)
            port = {'port': {'name': interface_name, 'admin_state_up': True, 'network_id': net_id}}
            port_info = self.neutron.create_port(body=port)

    	def get_ports(self,interface_name):
            ports = self.neutron.list_ports(interface_name)
            port_name = ports['ports'][0]['name']
	    return port_name

    	def get_port_id(self, interface_name):
	    ports = self.neutron.list_ports(interface_name)
            port_id = ports['ports'][0]['id']
	    return port_id

    	def add_router_interface(self, interface_name, router_name):
            router_id = self.get_router_id(router_name)
            port_id = self.get_port_id(interface_name)
            body = {'port_id':port_id}
            router = self.neutron.add_interface_router(router=router_id, body=body)

    	def remove_router_interface(self, interface_name, router_name):
            router_id = self.get_router_id(router_name)
            port_id = self.get_port_id(interface_name)
            body = {'port_id':port_id}
            router = self.neutron_client.remove_interface_router(router=router_id, body=body)

    	def add_floating_ip(self, instance_name):
            floating_ip = self.nova_client.floating_ips.create()
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
