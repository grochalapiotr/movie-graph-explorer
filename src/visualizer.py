# visualizer.py
"""
Konwersja grafu NetworkX → interaktywne HTML (PyVis).
"""

import networkx as nx
from pyvis.network import Network


def show_graph(G: nx.DiGraph,
               path: list = None,
               height: str = "600px",
               width: str = "100%") -> str:
    net = Network(height=height, width=width, directed=True)
    net.barnes_hut()

    # Kolory dla węzłów/krawędzi domyślnych wg typu
    color_map = {"Film": "#ffc107", "Person": "#2196f3"}

    # Węzły do podświetlenia
    highlight_nodes = set(path) if path else set()
    # Krawędzie do podświetlenia (kierunkowo)
    highlight_edges = set()
    if path:
        for u, v in zip(path, path[1:]):
            if G.has_edge(u, v):
                highlight_edges.add((u, v))
            elif G.has_edge(v, u):
                highlight_edges.add((v, u))

    # Dodajemy wszystkie węzły (z podświetleniem tych ze ścieżki)
    for node, data in G.nodes(data=True):
        label = node.split("/")[-1].replace("_", " ")
        node_type = data.get("type", "Film")
        if node in highlight_nodes:
            net.add_node(
                node,
                label=label,
                title=node,
                color="red",
                shape="ellipse" if node_type == "Film" else "dot",
                size=25
            )
        else:
            net.add_node(
                node,
                label=label,
                title=node,
                color=color_map.get(node_type, "#cccccc"),
                shape="ellipse" if node_type == "Film" else "dot"
            )

    # Dodajemy wszystkie krawędzie – te na ścieżce czerwone+widmniejsze, pozostałe w kolorze wg typu źródła
    for src, dst, edata in G.edges(data=True):
        src_type = G.nodes[src].get("type", "Film")
        default_color = color_map.get(src_type, "#cccccc")
        if (src, dst) in highlight_edges:
            net.add_edge(
                src,
                dst,
                label=edata.get("relation", ""),
                color="red",
                width=3
            )
        else:
            net.add_edge(
                src,
                dst,
                label=edata.get("relation", ""),
                color=default_color,
                width=1
            )

    return net.generate_html()
