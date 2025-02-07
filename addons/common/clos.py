import os
import pydot
import matplotlib.pyplot as plt
import networkx as nx
from PIL import Image
from nstopology import NSTopology as nstopo

subset_color = [
    "lightgreen",
    "lightblue",
    "pink",
    "darkorange",
]

class CLOS(nstopo):
    pe_routers = {}
    p_routers = {}
    servers = {}
    def __init__(self, nspines=1, nleaves=2, nservers_pe=1, delns=False):
        super(CLOS, self).__init__(tname="CLOS", delns=delns)
        self.nspines = nspines
        self.nleaves = nleaves
        self.nsvrs = nservers_pe
        self.launch_nesttopology(nspines, nleaves, nservers_pe)

        self.out_folder = "./output"
        # Create the directory if it doesn't exist
        os.makedirs(self.out_folder, exist_ok=True)

    def launch_nesttopology(self, nsp, npe, nservers_pe):
        # create spine routers
        for i in range(nsp):
            p_key = "P" + str(i)
            self.p_routers[p_key] = self.add_router(p_key, None, "Spine")
            self.p_routers[p_key].ports = npe

        # number of pe
        for i in range(npe):
            p_key = "PE" + str(i)
            self.pe_routers[p_key] = self.add_router(p_key, None, "Leaf")
            self.pe_routers[p_key].ports = nsp + nservers_pe

            # number of servers per pe
            for j in range(nservers_pe):
                hname = "h" + str(i) + str(j)
                self.servers[hname] = self.add_host(hname, "Server")
                self.servers[hname].ports = 1

        # k is router name and v is Gnode of it.
        for p, k in enumerate(self.p_routers.keys()):
            p_port = 0
            for pe, pe_k in enumerate(self.pe_routers.keys()):
                ifname1 = "Gi" + str(p_port)
                ifname2 = "Gi" + str(p)
                subnet = self.create_network("10.10.1.0", 24, p_port)
                self.add_link(k, pe_k, ifname1, ifname2, subnet)

                p_port += 1
            print("New Spine---", list(self.networks.keys()))

        for pe, (pe_k, pe_v) in enumerate(self.pe_routers.items()):
            pe_port = 0
            for j in range(self.nsvrs):
                hname = "h" + str(pe) + str(j)
                ifname1 = "eth" + str(pe_port+1)
                ifname2 = "eth" + str(0)

                subnet = self.create_network("192.168.128.0", 30, pe_port)
                self.add_link(pe_k, hname,
                            ifname1, ifname2, subnet)
                pe_port += 1

    def multilayered_graph(self):
        spines = list(self.p_routers.keys())
        leaves = list(self.pe_routers.keys())
        servers = list(self.servers.keys())

        layers = [servers, leaves, spines]
        sizes = [500, 700, 800]
        G = nx.DiGraph()
        for i, layr in enumerate(layers):
            G.add_nodes_from(layr, color=subset_color[i], size=sizes[i], layer= i)

        for i in range(0, len(leaves)):
            for j in range(0, len(spines)):
                G.add_edge(layers[1][i], layers[2][j])

        for j in range(0, len(leaves)):
            for k in range(0, self.nsvrs):
                index = j * self.nsvrs + k
                G.add_edge(layers[1][j], layers[0][index])

        return G

    def plot_topo2(self):

        G = self.multilayered_graph()
        color = [subset_color[data["layer"]] for v, data in G.nodes(data=True)]
        pos   = nx.multipartite_layout(G,
                                        subset_key="layer",
                                        align="horizontal")
        plt.figure(figsize=(14, 14))
        nx.draw(G, pos, edge_color='gray',
                with_labels=True,
                node_color=color,
                node_size=800)
        plt.axis("equal")
        fname = os.path.join(self.out_folder, "spine-leaf.png")
        plt.savefig(fname)
        print(fname)  # Output:
        nx.drawing.nx_pydot.write_dot(G, fname + ".dot")

    def plot_topo(self):

        # Step 1: get nodes and edges graph
        G = self.multilayered_graph()

        # Step 2: Define positions for nodes in a horizontal line
        pos   = nx.multipartite_layout(G,
                                        subset_key="layer",
                                        align="horizontal")
        # Step 3: Draw the graph
        node_clrs = [data['color'] for _, data in G.nodes(data=True)]
        node_szs  = [data['size'] for _, data in G.nodes(data=True)]
        plt.figure(figsize=(8, 8))  # Adjust figure size for horizontal alignment
        nx.draw(G, pos, with_labels=True,
                node_color=node_clrs,
                node_size=node_szs,
                edge_color='gray')

        plt.title("Custom Spine Leaf layered Layout")
        fname = os.path.join(self.out_folder, "spine-leaf.png")
        print(fname)  # Output:

        plt.savefig(fname)
        plt.close()
        nx.drawing.nx_pydot.write_dot(G, fname + ".dot")

    def do_auto_routing_daemons(self):
        for pk in self.pe_routers.keys():
            self.start_bgpd(pk)

        for pk in self.p_routers.keys():
            self.start_bgpd(pk)


clos = CLOS(2, 2, 1, False)
clos.show_ns_addr()
clos.do_auto_routing_daemons()

#clos.plot_topo()
