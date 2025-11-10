import urllib

from rdflib import Graph, URIRef, Namespace, Literal
from rdflib.namespace import RDF, RDFS

# A test to convert .nt KG data
g = Graph()


ns = Namespace("http://rdf.fbwq.com/ns/")
ns2= Namespace("")


with open('mid2name.csv', 'r',encoding='utf-8') as f:
    for line in f:
        lines=line.strip().split(',')
        subject=lines[0]
        relation=lines[1]
        object_line = lines[2:]
        object=','.join([str(i) for i in object_line])
        object=urllib.parse.quote(object)
        subject_uri = URIRef(ns[subject])
        obj_uri = URIRef(object)
        # g.add((subject_uri, RDF.type, ns[relation]))
        g.add((subject_uri, ns[relation], obj_uri))
        print(subject_uri,ns[relation],obj_uri)

g.serialize(destination='mid2name', format='nt',encoding='utf-8')
