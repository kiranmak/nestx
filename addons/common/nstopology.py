import pprint
from nest.topology import Router, Node, Switch, connect
from nest.topology.network import Network

from nest.routing.routing_helper import RoutingHelper
from nest.topology.address_helper import AddressHelper
from nest.routing.zebra import Zebra
from nest import config
#from nsrouting import NSRoutingDaemon

import networkx as nx
import matplotlib.pyplot as plt 
from pyroute2 import NetNS
import socket
import os

from enum import Enum

import importlib
"""
To set up a network, we need to create
   a. some nodes that could be routers (core, edge, spine, leaf, access etc.)
   b. ifs: connections b/w nodes (based on structure, eg clos, butterfly etc.)
   c. address assignment. Provide prefix and let AddressHelper do the thing
   d. features and daemons.
"""

class TopoByName(Enum):
    CLOS = "clos"
    DUMBELL = "dumbell"
    BUTTERFLY = "butterfly"

class FeatureByName(Enum):
    EVPN = "evpn"
    BGP_PEER = "bgp_peer"

'''
This class is meant to hold topology info as a dictionary/graph.
'''
class GDevice:
    def __init__(self, name, ports, role):
        self.name = name
        self.ports = ports
        self.role = role
        self.connections = {}
        self.ns_node_ref = None

    def add_ifinfo(self, dest, srcif, destif):
        self.connections[dest] = [srcif, destif]

    def add_ns_ref(self, ns_ref):
        self.ns_node_ref = ns_ref

    def ns_ref(self):
        return self.ns_node_ref

    def set_role(self, role):
        self.role = role

    def show(self):
        print("Node: %s ports#: %s type %s" %
                (self.name,self.ports, self.role))
        #print(" connections:")
        for k,v in self.connections.items():
            print(f"   %s.%s--> %s.%s" %
                (self.name, v[0], k, v[1]))

class NSTopology:
    def __init__(self, tname=None, delns=True):
        self.topoId = tname
        self.tgraph = {}  # maintain interfaces and node connection
        self.interfaces = []
        self.daemons = {}
        self.autoconfig_db = {} # TODO 
        self.networks = {}
        self.auto_config_addresses()

        self.conf_dir = None
        config.set_value("assign_random_names", False)
        config.set_value("routing_suite", "frr")
        config.set_value("routing_logs", True)
        config.set_value('delete_namespaces_on_termination', delns)

    def set_config_dir(self, folder):
        current_dir = os.getcwd()
        self.conf_dir = os.path.join(current_dir, folder)



    # TODO
    def auto_config_addresses(self):
        from copy import deepcopy
        addr_params = {
        "address_types": ["ipv4", "ipv6"],
        "ipv4base": "10.0.0.0",
        "ipv4mask": 30,
        "ipv6base": "fd00::",
        "ipv6mask": 64}
        addr_params["lo_prefix"] = {
                "ipv4": "1.0.",
                "v4mask": 32,
                "ipv6": "2001:db8:f::",
                "v6mask": 128}
        addr_params["link_ip_start"] = {
                "ipv4": "10.0.0.0",
                "v4mask": 30,
                "ipv6": "fd00::",
                "v6mask": 64}

        # Perform a deep copy
        self.autoconfig_db["links"] = deepcopy(addr_params)

    def plot(self):

        G = nx.Graph()
        color_map = []
        for node, neig  in self.tgraph.items():
            G.add_node(node, color = 'red', )
            if node == "Spine":
                color_map.append('blue')
                G.nodes[node]["layer"] = 1
            elif node == "Leaf":
                color_map.append('green')  
                G.nodes[node]["layer"] = 2
            else:
                color_map.append('grey')  
                G.nodes[node]["layer"] = 3

            for k,v in neig.connections.items():
                G.add_edge(node, k)
        nx.draw_spring(G, node_color=color_map,
                        with_labels = True)
        plt.savefig('plot.png')

    def add_router(self, rtrname="rtr", rid=None, role="router"):
        if rid != None:
            rname = rtrname + str(rid)
        else:
            rname = rtrname

        new_node = GDevice(rname, 0, role)
        self.tgraph[rname] = new_node
        ns_ref = Router(rname)
        new_node.add_ns_ref(ns_ref)
        return new_node

    def add_switch(self, swname="sw", rid = None):
        if rid != None:
            rname = swname + str(rid)
        else:
            rname = swname

        new_node = GDevice(swname, 0, 'switch')
        self.tgraph[swname] = new_node
        ns_ref = Router(rname)
        new_node.add_ns_ref(ns_ref)
        return new_node

    def add_host(self, hname, role):
        new_node = GDevice(hname, 0, role)
        self.tgraph[hname] = new_node
        ns_ref = Node(hname)
        new_node.add_ns_ref(ns_ref)
        return new_node

    def add_link(self, ep1, ep2,
                 ep1_ep2_ifname, ep2_ep1_ifname,
                 subnet):

        r1 = self.get_ns_ref(ep1)
        r2 = self.get_ns_ref(ep2)
        #subnet = self.create_network(prefix, mask, ctr)
        with subnet:
            #Create interfaces
            (if1, if2) = connect(r1, r2,
                                 ep1_ep2_ifname,
                                 ep2_ep1_ifname)

            AddressHelper.assign_addresses()


        self.interfaces.append({"src": ep1, "dst": ep2, "if": if1})
        self.interfaces.append({"src": ep2, "dst": ep1, "if": if2})

        # i could maintain a DB and provide helpers for clean look
        src_node = self.get_node(ep1)
        dst_node = self.get_node(ep2)
        src_node.add_ifinfo(ep2, ep1_ep2_ifname, ep2_ep1_ifname)
        dst_node.add_ifinfo(ep1, ep2_ep1_ifname, ep1_ep2_ifname)

    def create_network(self, prefix, mask, ctr):

        a_prefix = list(map(int, prefix.split(".")))

        # compute the block size based on cidr mask
        block = 1
        for bit in range(32-mask):
            block = block + (1 << bit)
        pos = mask//8

        width = ctr * block
        if (a_prefix[pos] + width ) > 254:
            a_prefix[pos - 1] += width//256
            a_prefix[pos] = width%256
        else:
            a_prefix[pos] += width

        # revert back to string format
        result = ".".join([str(num) for num in a_prefix])

        self.networks[result] = Network(result + "/" + str(mask))

        return self.networks[result]

    def get_node(self, nname):
        gnode = None
        if nname in self.tgraph:
            gnode = self.tgraph[nname]
        return gnode

    def get_ns_ref(self, nname):
        ns_ref = None
        if nname in self.tgraph.keys():
            ns_ref = self.tgraph[nname].ns_node_ref
        else:
            print("NS_REF not found for node ", nname)
        return ns_ref

    def show_nodes(self):
        for v in self.tgraph.values():
            v.show()

    def show_ifs(self):
        for index, entry in enumerate(self.interfaces):
            print(f"{index} - {entry['if'].node_id}.{entry['if'].id}")


    def get_ipv4_addresses(self, namespace_name):
        try:
            # Open the specified network namespace
            with NetNS(namespace_name) as ns:
                print(f"Node: {namespace_name}")
                # Get all links (interfaces) in the namespace
                links = ns.get_links()

                # Iterate over each interface and retrieve its IPv4 address
                for link in links:
                    ifname = link.get_attr('IFLA_IFNAME')  # Interface name
                    index = link['index']  # Interface index

                    # Get the IP addresses for this interface
                    addresses = ns.get_addr(index=index)
                    for addr in addresses:
                        family = addr['family']
                        if family == socket.AF_INET:  # IPv4 address
                            ipv4 = addr.get_attr('IFA_ADDRESS')
                            print(f"  {ifname}: {ipv4}")
        except Exception as e:
            print(f"Error: {e}")


    def show_ns_addr(self):
        for node_name in self.tgraph.keys():
            self.get_ipv4_addresses(node_name)

    def start_bgpd(self, rtr_nodes, h_nodes):
        proto = "bgp"
        bgp_rtrs = []
        hosts = []

        for inst in rtr_nodes:
            bgp_rtrs.append(inst.ns_ref())

        #I have to add this hack because RoutingHelper
        # needs either both host and routers not one.
        # see line 115 in routing_helper.py
        # TODO make it one daemon per router API.
        for inst in h_nodes:
            hosts.append(inst.ns_ref())

        ri = RoutingHelper(routers=bgp_rtrs,
                           hosts=hosts,
                           protocol=proto)

        self.daemons[proto] = ri

        # the conf file name will be of format r0_frr.conf
        ri.create_conf_dir(self.conf_dir)
        ri.populate_routing_tables()
