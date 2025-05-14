"""
Pobieranie danych o filmie, reżyserze i aktorach z DBpedii.
"""

from typing import List, Dict
from SPARQLWrapper import SPARQLWrapper, JSON

ENDPOINT = "https://dbpedia.org/sparql"


def _run_query(query: str) -> List[Dict]:
    sparql = SPARQLWrapper(ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()["results"]["bindings"]

def get_movie_suggestions(fragment: str, limit: int = 10) -> List[Dict]:
    """
    Zwraca listę filmów (URI + etykieta) których angielski tytuł
    zawiera podany fragment (case-insensitive).
    """
    # 1) Escape’ujemy podwójne cudzysłowy i backslashe w tytule
    sanitized = fragment.replace("\\", "\\\\").replace('"', '\\"')

    # 2) Budujemy zapytanie, w f-stringu jest już tylko zmienna sanitized
    query = f'''
    SELECT DISTINCT ?film ?lbl WHERE {{
      ?film a dbo:Film ;
            rdfs:label ?lbl .
      FILTER (
        lang(?lbl) = 'en' &&
        CONTAINS(lcase(str(?lbl)), lcase("{sanitized}"))
      )
    }}
    LIMIT {limit}
    '''

    results = _run_query(query)
    return [{"film": r["film"]["value"], "label": r["lbl"]["value"]} for r in results]


def get_movie_core(identifier: str) -> List[Dict]:
    """
    Zwraca podstawowe relacje film–reżyser–aktor.
    Jeśli identifier wygląda jak URI (zaczyna się od "http"), zapytanie
    będzie szukać relacji dla dokładnie tego filmu.
    W przeciwnym razie traktuje argument jako fragment tytułu.
    """
    # Rozróżnienie URI vs. fragment tytułu
    if identifier.lower().startswith("http"):
        # Zapytanie po konkretnym URI
        film_uri = identifier
        query = f'''
        SELECT ?film ?director ?actor WHERE {{
          BIND(<{film_uri}> AS ?film)
          ?film dbo:director ?director ;
                dbo:starring  ?actor .
        }}
        '''
    else:
        # Escape tytułu (cudzysłowy / backslashe)
        sanitized = identifier.replace("\\", "\\\\").replace('"', '\\"')
        query = f'''
        SELECT ?film ?director ?actor WHERE {{
          ?film rdfs:label ?lbl ;
                dbo:director ?director ;
                dbo:starring  ?actor .
          FILTER (
            lang(?lbl) = 'en' &&
            STRSTARTS( LCASE(str(?lbl)), LCASE("{sanitized}") )
          )
        }}
        LIMIT 50
        '''
    return _run_query(query)


def get_other_movies(person_uri: str, limit: int = 5) -> List[Dict]:
    query = f"""
    SELECT ?film
    WHERE {{
      ?film dbo:starring|dbo:director <{person_uri}> .
      ?film rdfs:label ?label .
      FILTER (lang(?label) = 'en')
    }}
    LIMIT {limit}
    """
    return _run_query(query)
