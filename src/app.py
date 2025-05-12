"""
Aplikacja Streamlit uruchamiająca cały pipeline.
"""

import streamlit as st
import networkx as nx
from fetcher import get_movie_core, get_other_movies
# from fetcher_google import get_movie_core, get_other_movies
from graph_builder import build_graph
from visualizer import show_graph

# Konfiguracja strony
st.set_page_config(page_title="Movie-Graph Explorer", layout="wide")
st.sidebar.title("🔍 Ustawienia wyszukiwania")

# Kontrolki
title = st.sidebar.text_input("Tytuł filmu (angielski):", "Inception")
depth = st.sidebar.toggle("Rozszerzenie grafu", value=True)
run = st.sidebar.button("Generuj graf")
film_a = st.sidebar.text_input("Film A (angielski):", "Inception")
film_b = st.sidebar.text_input("Film B (angielski):", "Titanic")
path_btn = st.sidebar.button("Pokaż ścieżkę")

def build_and_store_graph():
    """Buduje graf i zapisuje go wraz z wygenerowanym HTML w session_state."""
    core = get_movie_core(title)
    expansion = {}
    if depth == 1:
        persons = {r["director"]["value"] for r in core} | {r["actor"]["value"] for r in core}
        for p in persons:
            expansion[p] = get_other_movies(p)
    G = build_graph(core, expansion if depth else None)
    st.session_state.G = G
    st.session_state.html = show_graph(G)
    print(st.session_state.G)

def find_film_uri(G, title):
    """
    Szuka w G węzła typu Film mającego etykietę równą podanemu title.
    Zwraca pełne URI lub None.
    """
    title = title.strip().lower()
    for node, data in G.nodes(data=True):
        if data.get("type") == "Film":
            label = node.rsplit("/", 1)[-1].replace("_", " ").lower()
            if label == title:
                return node
    return None

# Jeśli któryś przycisk został wciśnięty, (re)budujemy graf
if run or path_btn:
    with st.spinner("Pobieram dane i buduję graf…"):
        build_and_store_graph()

# Gdy graf jest dostępny – wyświetlamy go i obsługujemy ścieżki
if "G" in st.session_state:
    G = st.session_state.G
    html = st.session_state.html

    col1, col2 = st.columns([3, 1])
    with col2:
        st.metric("Węzły", len(G.nodes))
        st.metric("Krawędzi", len(G.edges))

        if path_btn:
            uri_a = find_film_uri(G, film_a)
            uri_b = find_film_uri(G, film_b)
            if not uri_a or not uri_b:
                missing = film_a if not uri_a else film_b
                st.error(f"Film „{missing}” nie jest w grafie.")
            else:
                try:
                    # 1. rzutujemy na nieskierowany
                    UG = G.to_undirected()
                    p = nx.shortest_path(UG, uri_a, uri_b)

                    st.write(f"Najkrótsza ścieżka ({len(p)-1} kroków):")
                    for n in p:
                        st.write("–", n.split("/")[-1].replace("_", " "))
                except nx.NetworkXNoPath:
                    st.error("Brak połączenia między wybranymi filmami.")
                except Exception as e:
                    st.error(f"Błąd podczas wyznaczania ścieżki: {e}")

    with col1:
        st.components.v1.html(html, height=650, scrolling=True)

else:
    # Ekran powitalny
    st.header("🎬 Movie-Graph Explorer")
    st.write("Wpisz tytuł filmu, wybierz poziom rozszerzenia i zobacz relacje.")
