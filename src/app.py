"""
Aplikacja Streamlit uruchamiająca cały pipeline.
"""

import streamlit as st
import networkx as nx
from fetcher import get_movie_suggestions, get_movie_core, get_other_movies
# from fetcher_google import get_movie_core, get_other_movies
from graph_builder import build_graph
from visualizer import show_graph

# Konfiguracja strony
st.set_page_config(page_title="Movie-Graph Explorer", layout="wide")
st.sidebar.title("🔍 Ustawienia wyszukiwania")

# 1) Pole tekstowe do wpisania fragmentu tytułu
input_title = st.sidebar.text_input("Tytuł filmu (angielski):", "Toy Story")

# 2) Pobieramy listę sugestii (label i URI)
suggestions = []
if input_title:
    suggestions = get_movie_suggestions(input_title, limit=10)  # zwraca listę dict: {"film": uri, "label": lbl}

if not suggestions:
    st.sidebar.write("Brak propozycji dla tego fragmentu.")
else:
    # 3) Pokazujemy dropdown z sugestiami
    labels = [s["label"] for s in suggestions]
    chosen_label = st.sidebar.selectbox("Wybierz film:", labels)
    # 4) Zaemapujemy wybrany label na URI
    uri_map = {s["label"]: s["film"] for s in suggestions}
    chosen_uri = uri_map[chosen_label]

# 5) Reszta parametrów
depth = st.sidebar.toggle("Rozszerzenie grafu", value=True)
limit = st.sidebar.number_input("Limit innych filmów na osobę:", value=5, min_value=1)
run = st.sidebar.button("Generuj graf")


def build_and_store_graph(uri: str):
    """Buduje graf i zapisuje go wraz z wygenerowanym HTML w session_state."""
    core = get_movie_core(uri)
    expansion = {}
    if depth:
        persons = {r["director"]["value"] for r in core} | {r["actor"]["value"] for r in core}
        for p in persons:
            expansion[p] = get_other_movies(p, limit=limit)
    G = build_graph(core, expansion if depth else None)
    st.session_state.G = G
    st.session_state.html = show_graph(G)


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


# Jeśli przycisk został wciśnięty, (re)budujemy graf
if run:
    if suggestions:
        with st.spinner("Pobieram dane i buduję graf…"):
            build_and_store_graph(chosen_uri)
    else:
        st.error("Nie wybrano poprawnego filmu z listy propozycji.")

# Gdy graf jest dostępny - pokazujemy dropdowny i wykres
if "G" in st.session_state:
    G = st.session_state.G

    # Lista filmów (URI) w grafie
    films = [node for node, data in G.nodes(data=True) if data.get("type") == "Film"]
    if not films:
        st.warning("Nie znaleziono żadnych filmów w grafie. Spróbuj ponownie z innym tytułem.")
    else:
        # Mapa URI->etykieta
        film_labels = {
            f: f.rsplit("/", 1)[-1].replace("_", " ")
            for f in films
        }
        # Lista posortowanych etykiet
        labels_sorted = sorted(film_labels.values())

        # Dropdowny z domyślnym wyborem pierwszego elementu
        film_a_label = st.sidebar.selectbox("Film A:", labels_sorted, index=0)
        film_b_label = st.sidebar.selectbox("Film B:", labels_sorted, index=0)

        # Odwrotna mapa etykieta->URI
        label_to_uri = {label: uri for uri, label in film_labels.items()}

        # Bezpieczne pobieranie URI
        uri_a = label_to_uri.get(film_a_label)
        uri_b = label_to_uri.get(film_b_label)
        if uri_a is None or uri_b is None:
            st.error("Nie udało się odnaleźć URI dla wybranych filmów.")
        else:
            path = None

            # Rysujemy graf
            html = show_graph(G)
            col1, col2 = st.columns([8, 1])
            with col2:
                st.metric("Węzły", len(G.nodes))
                st.metric("Krawędzi", len(G.edges))
                if st.sidebar.button("Pokaż ścieżkę"):
                    try:
                        UG = G.to_undirected()
                        path = nx.shortest_path(UG, uri_a, uri_b)
                        st.write(f"Najkrótsza ścieżka ({len(path)-1} kroków):")
                        for i, n in enumerate(path):
                            title_readable = n.rsplit("/", 1)[-1].replace("_", " ")
                            st.write(f"**{title_readable}**")
                            if i < len(path) - 1:
                                st.markdown(
                                    "<div style='text-align: center; font-size: 24px; line-height: 0.5;'>&darr;</div>",
                                    unsafe_allow_html=True
                                )
                    except nx.NetworkXNoPath:
                        st.error("Brak połączenia między wybranymi filmami.")
            with col1:
                st.components.v1.html(html, height=650, scrolling=True)

else:
    # Ekran powitalny
    st.header("🎬 Movie-Graph Explorer")
    st.write("Wpisz tytuł filmu, wybierz poziom rozszerzenia i zobacz relacje.")
