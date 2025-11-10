from rdflib import Graph, URIRef, Namespace, Literal
from rdflib.namespace import RDF, RDFS

# A test to convert .nt KG data

g = Graph()


ns = Namespace("http://rdf.fb15k237.com/ns/")


with open('fb15k237.csv', 'r',encoding='utf-8') as f:
    for line in f:
        subject, relation, object = line.strip().split(',')
        subject_uri = URIRef(ns[subject])
        obj_uri = URIRef(ns[object])
        g.add((subject_uri, RDF.type, ns[relation]))
        g.add((subject_uri, ns[relation], obj_uri))


g.serialize(destination='output.nt', format='nt')
