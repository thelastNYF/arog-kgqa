import json
import time

from SPARQLWrapper import SPARQLWrapper, JSON

SPARQLPATH = "http://localhost:6006/sparql"
sparql_pos_pos = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?relation1 ?relation2\nWHERE {\n  {\n    ns:%s ?relation1 ?neighbor .\n ?neighbor ?relation2 ns:%s .\n}\n}"""


def test():
    try:
        sparql = SPARQLWrapper(SPARQLPATH)
        sparql_txt = """PREFIX ns: <http://rdf.freebase.com/ns/>
            SELECT distinct ?name3
            WHERE {
            ns:m.0k2kfpc ns:award.award_nominated_work.award_nominations ?e1.
            ?e1 ns:award.award_nomination.award_nominee ns:m.02pbp9.
            ns:m.02pbp9 ns:people.person.spouse_s ?e2.
            ?e2 ns:people.marriage.spouse ?e3.
            ?e2 ns:people.marriage.from ?e4.
            ?e3 ns:type.object.name ?name3
            MINUS{?e2 ns:type.object.name ?name2}
            }
        """
        sparql_txt = """PREFIX ns: <http://rdf.fbwq.com/ns/>
            SELECT ?t WHERE {ns:m.078w2 ns:influence.influence_node.influenced_by ?t . }
        """
        sparql_txt = sparql_pos_pos % ('m.025pyr', 'm.083p7')

        print(sparql_txt)
        sparql.setQuery(sparql_txt)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        print(results)
    except:
        print('Your database is not installed properly !!!')


sparql_id = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?tailEntity\nWHERE {\n  {\n    ?entity ns:type.object.name ?tailEntity .\n    FILTER(?entity = ns:%s)\n  }\n}"""
sparql = SPARQLWrapper(SPARQLPATH)
sparql_txt = sparql_id % ('m.0ds82nr')
start_time = time.time()

print(sparql_txt)
sparql.setQuery(sparql_txt)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
end_time = time.time()
print(end_time - start_time)
print(results)
