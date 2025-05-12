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


def get_movie_core(title_en: str) -> List[Dict]:
    query = f"""
    SELECT ?film ?director ?actor
    WHERE {{
      ?film rdfs:label "{title_en}"@en ;
            dbo:director ?director ;
            dbo:starring ?actor .
    }}
    LIMIT 50
    """
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
