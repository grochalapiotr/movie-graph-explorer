"""
Konwersja grafu NetworkX → interaktywne HTML (PyVis).
"""

from typing import Union
import networkx as nx
from pyvis.network import Network


def show_graph(G: nx.MultiDiGraph,
               height: str = "600px",
               width: str = "100%") -> str:
    net = Network(height=height, width=width, directed=True)
    net.barnes_hut()

    color_map = {"Film": "#ffc107", "Person": "#2196f3"}

    for node, data in G.nodes(data=True):
        label = node.split("/")[-1].replace("_", " ")
        node_type = data.get("type", "Film")
        net.add_node(node,
                     label=label,
                     title=node,
                     color=color_map.get(node_type),
                     shape="ellipse" if node_type=="Film" else "dot")

    for src, dst, edata in G.edges(data=True):
        net.add_edge(src, dst, label=edata.get("relation", ""))

    return net.generate_html()
