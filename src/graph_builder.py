"""
Budowanie grafu NetworkX na podstawie wyników zapytań SPARQL.
"""

from typing import List, Dict
import networkx as nx


def build_graph(core_results: List[Dict],
                expansion_results: Dict[str, List[Dict]] = None) -> nx.MultiDiGraph:
    G = nx.DiGraph()

    # rdzeń filmu
    for row in core_results:
        film = row["film"]["value"]
        director = row["director"]["value"]
        actor = row["actor"]["value"]

        G.add_node(film, type="Film")
        G.add_node(director, type="Person")
        G.add_node(actor, type="Person")
        G.add_edge(director, film, relation="directed")
        G.add_edge(actor, film, relation="acted_in")

    # opcjonalne rozszerzenie
    if expansion_results:
        for person_uri, movies in expansion_results.items():
            G.add_node(person_uri, type="Person")
            for m in movies:
                film_uri = m["film"]["value"]
                if not G.has_node(film_uri):
                    G.add_node(film_uri, type="Film")
                # zakładamy, że jeśli osoba była już reżyserem, to directed
                relation = "directed" if any(
                    e for e in G.edges(person_uri, data=True) if e[2].get("relation")=="directed"
                ) else "acted_in"
                G.add_edge(person_uri, film_uri, relation=relation)

    return G
