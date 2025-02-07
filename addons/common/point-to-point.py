import os
import matplotlib.pyplot as plt
import networkx as nx
import pydot
from PIL import Image
from addons.common.nstopology import NSTopology as nstopo

subset_color = [
    "lightgreen",
    "lightblue",
    "pink",
    "darkorange",
]

class P2P(nstopo):
    routers = {}
    servers = {}
    def __init__(self, nrouters=1, nservers=1, delns=False):
        super(P2P, self).__init__(tname="P2P", delns=delns)
        self.nrouters = nrouters
        self.nsvrs = nservers

        self.set_config_dir("output")

        self.launch_ns(nrouters, nservers)
        print(f"Namespace environment launched!")

    def launch_ns(self, nrouters, nservers):
        # create routers
        for i in range(nrouters):
            p_key = "r" + str(i)
            self.routers[p_key] = super().add_router(p_key, None, "Core")
            self.routers[p_key].ports = nservers


        # number of servers per edge-router
        for j in range(nservers):
            left_edge  = "h" + str(0) + str(j)
            right_edge = "h" + str(nrouters-1) + str(j)
            self.servers[left_edge] = self.add_host(left_edge, "Server")
            if nrouters > 1:
                self.servers[right_edge] = self.add_host(right_edge, "Server")

            self.servers[left_edge].ports = 1
            self.servers[right_edge].ports = 1

        print("nodes = ", self.routers.keys(), self.servers.keys())
        print("Make links")
        self.make_p2p_links()

    def make_p2p_links(self):

        rnames = list(self.routers.keys())
        nrouters = self.nrouters
        # point to point: port-0 this router to previous's 1. if one router, skip
        if nrouters > 1:
            for index in range(1, nrouters):
                left, right = 0, 1
                ifname1 = "Gi" + str(right)
                ifname2 = "Gi" + str(left)

                subnet = self.create_network("10.10.1.0", 30, index)
                self.add_link(rnames[index],
                              rnames[index-1],
                              ifname1, ifname2,subnet)

        # only need to connect to first and last router.
        # number of servers per edge-router
        for j in range(self.nsvrs):
            lhost = "h" + str(0) + str(j)

            ifname2 = "eth" + str(j+1)
            subnet = self.create_network("192.168.10.0", 30, j)
            self.add_link(rnames[0], lhost,
                            ifname2, "eth0", subnet)

            if nrouters == 1:
                continue

            rhost = "h" + str(nrouters-1) + str(j)
            subnet = self.create_network("192.168.10.0", 30, j)
            self.add_link(rnames[nrouters -1], rhost, 
                          ifname2, "eth0", subnet)

    def get_edges(self):

        nodes = [d.get('src') for d in self.interfaces]
        other_nodes = [d.get('dst') for d in self.interfaces]
        return nodes, other_nodes

    def multilayered_graph(self):

        rnames = list(self.routers.keys())
        snames = list(self.servers.keys())
        layers = [rnames, snames]
        sizes = [500, 700]
        G = nx.Graph()

        for i, node in enumerate(layers):
            G.add_nodes_from(node, color=subset_color[i], size=sizes[i])

        from_nodes, to_nodes = self.get_edges()
        for i, from_node in enumerate(from_nodes):
            G.add_edge(from_node, to_nodes[i])

        # Analyze the graph
        print("Nodes:", G.nodes)
        print("Edges:", G.edges)
        return G

    def plot_topo(self):

        # Step 1: get nodes and edges graph
        G = self.multilayered_graph()

        # Step 2: Define positions for nodes in a horizontal line
        positions = nx.spring_layout(G)


        # Print the positions of each node
        print("Node Positions:")
        for node, pos in positions.items():
            pos[1] = 0
            #print(f"Node {node}: {pos}")

        # Step 3: Draw the graph
        node_clrs = [data['color'] for _, data in G.nodes(data=True)]
        node_szs = [data['size'] for _, data in G.nodes(data=True)]
        plt.figure(figsize=(8, 2))  # Adjust figure size for horizontal alignment
        nx.draw(G, positions, with_labels=True, node_color=node_clrs, node_size=node_szs, edge_color='gray')
        #plt.show()

        plt.title("Custom Straight Line Layout")
        fname = self.out_folder + "point-to-point.png"
        # Join paths
        fname = os.path.join(self.out_folder, "point-to-point.png")
        print(fname)  # Output:

        plt.savefig(fname)
        plt.close()
        nx.drawing.nx_pydot.write_dot(G, fname + ".dot")

        # Display the saved image
        #img = Image.open(fname)
        #img.show()


    def plot_topo2(self):

        G = self.multilayered_graph()
        color = [data["color"] for v, data in G.nodes(data=True)]

        pos   = nx.multipartite_layout(G,
                                        subset_key="layer",
                                        align="horizontal")
        # Draw the graph with the custom layout
        nx.draw(G, pos, with_labels=True,
                arrows=True, node_color=color, node_size=800)
        plt.title("Custom Straight Line Layout")

        plt.savefig(self.out_folder + 'point-to-point.png')
        nx.drawing.nx_pydot.write_dot(
                G, self.out_folder  + "point-to-point.dot")
        #plt.show()

    def do_auto_routing_daemons(self):
        r_nodes = []
        h_nodes = []
        for k in self.routers.keys():
            r_nodes.append(self.routers[k])

        for k in self.servers.keys():
            h_nodes.append(self.servers[k])

        self.start_bgpd(r_nodes, h_nodes)

p2p = P2P(2, 1, False)
p2p.show_ns_addr()
#p2p.do_auto_routing_daemons()

#p2p.plot_topo()
