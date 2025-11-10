import json
import logging
import time
import traceback

from prompt_list import *
from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.parse import unquote
import requests

SPARQLPATH = "http://xxx.xxx.xxx.xxx:8890/sparql"  # depend on your own internal address and port, shown in Freebase folder's readme.md
SLMPATH = 'http://{{SentenceTransformer Server}}/sentence_transformer'
# "&;& "
# relation search
sparql_head_relations = """\nPREFIX ns: <http://rdf.fbwq.com/ns/>\nSELECT ?relation\nWHERE {\n  ns:%s ?relation ?x .\n}"""
sparql_head_relations_no_cvt = """\nPREFIX ns: <http://rdf.fbwq.com/ns/>\nSELECT ?relation\nWHERE {\n  ns:%s ?relation ?x .\n ?x ns:type.object.type ns:common.topic . \n}"""
sparql_tail_relations = """\nPREFIX ns: <http://rdf.fbwq.com/ns/>\nSELECT ?relation\nWHERE {\n  ?x ?relation ns:%s .\n}"""
sparql_tail_relations_no_cvt = """\nPREFIX ns: <http://rdf.fbwq.com/ns/>\nSELECT ?relation\nWHERE {\n  ?x ?relation ns:%s .\n ?x ns:type.object.type ns:common.topic . \n}"""
# entity search
sparql_tail_entities_extract = """PREFIX ns: <http://rdf.fbwq.com/ns/>\nSELECT ?tailEntity\nWHERE {\nns:%s ns:%s ?tailEntity .\n}"""
sparql_head_entities_extract = """PREFIX ns: <http://rdf.fbwq.com/ns/>\nSELECT ?tailEntity\nWHERE {\n?tailEntity ns:%s ns:%s  .\n}"""
# entity search when meeting cvt node
sparql_cvt_entities_extract = """PREFIX ns: <http://rdf.fbwq.com/ns/>\nSELECT ?tailEntity\nWHERE {\nns:%s ns:%s ?mid_entity . \n ?mid_entity ns:%s ?tailEntity .\n}"""
sparql_cvt_entities_extract_tail = """PREFIX ns: <http://rdf.fbwq.com/ns/>\nSELECT ?tailEntity\nWHERE {\n ?tailEntity ns:%s ?mid_entity . \n ?mid_entity ns:%s ns:%s .\n}"""

# id 2 name
sparql_id = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?tailEntity\nWHERE {\n  {\n    ?entity ns:type.object.name ?tailEntity .\n    FILTER(?entity = ns:%s)\n  }\n}"""
sparql_id_english = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?tailEntity\nWHERE {\n  FILTER (!isLiteral(?tailEntity) OR lang(?tailEntity) = '' OR langMatches(lang(?tailEntity), 'en')) {\n    ?entity ns:type.object.name ?tailEntity .\n    FILTER(?entity = ns:%s)\n  }\n}"""
sparql_id_cvt_node = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?tailEntity\nWHERE {\n  {\n    ?entity ns:type.object.name ?tailEntity .\n    FILTER(?entity = ns:%s)\n  }\n} LIMIT 1"""
sparql_id_fbwq = """PREFIX ns: <http://rdf.fbwq.com/ns/>\nSELECT DISTINCT ?tailEntity\nWHERE {\n  {\n    ?entity ns:type.object.name ?tailEntity .\n    FILTER(?entity = ns:%s)\n  }\n}"""
sparql_id_relation_friendly="""PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?tailEntity \nWHERE {\n FILTER (!isLiteral(?x) OR lang(?x) = '' OR langMatches(lang(?x), 'en'))\n  {\n    ns:%s ns:type.object.name ?tailEntity . \n }\n} LIMIT 1"""

def check_end_word(s):
    words = [" ID", " code", " number", "instance of", "website", "URL", "inception", "image", " rate", " count"]
    return any(s.endswith(word) for word in words)


def abandon_rels_description(relation):
    if relation == "N/A" or relation == "type.object.type" or relation == "type.object.name" or relation.startswith(
            "common.") or relation.startswith(
        "freebase.") or "sameAs" in relation or " " in relation or "http://www.w3.org/" in relation or "http://rdf.freebase.com/key/" in relation or "kg." in relation or relation.startswith(
        "base.") or relation.startswith("type.object") or relation.startswith("user."):
        return True

def abandon_rels(relation):
    if relation == "N/A" or relation.startswith(
            "common.") or relation.startswith(
        "freebase.") or "sameAs" in relation or " " in relation or "http://www.w3.org/" in relation or "http://rdf.freebase.com/key/" in relation or relation.startswith(
        "kg.") or relation.startswith(
        "type."):
        return True

def judge_cvt_node(entity_id):
    sparql_query = sparql_id_cvt_node % (entity_id)
    sparql = SPARQLWrapper(SPARQLPATH)
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if len(results["results"]["bindings"]) == 0:
        return "UnName_Entity"
    else:
        return (results["results"]["bindings"][0]['tailEntity']['value']).replace('http://rdf.fbwq.com/ns/',
                                                                                         "").replace(
            "http://rdf.freebase.com/ns/", "")

def execurte_sparql(sparql_query):
    times = 5
    for _ in range(times):
        try:
            sparql = SPARQLWrapper(SPARQLPATH)
            sparql_query = sparql_query.replace("<http://rdf.fbwq.com/ns/>", "<http://rdf.freebase.com/ns/>")
            sparql.setQuery(sparql_query)
            print(sparql_query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            return results["results"]["bindings"]
        except Exception as e:
            time.sleep(1)
            traceback.print_exc()
            logging.error(f"we pass sparql_query: {e}\n{traceback.format_exc()}\n{sparql_query}")
            continue
    return None



def execurte_sparql_fbwq(sparql_query):
    sparql = SPARQLWrapper(SPARQLPATH)
    sparql_query = sparql_query.replace("<http://rdf.fbwq.com/ns/>", "<http://rdf.freebase.com/ns/>")
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results["results"]["bindings"]


def replace_relation_prefix(relations):
    return [
        relation['relation']['value'].replace("http://rdf.fbwq.com/ns/", "").replace("http://rdf.freebase.com/ns/", "")
        for relation in relations]


def replace_entities_prefix(entities):
    return [
        entity['tailEntity']['value'].replace("http://rdf.fbwq.com/ns/", "").replace("http://rdf.freebase.com/ns/", "")
        for entity in entities]


# return private names of the entity
def id2entity_name_or_type_privacy(value_entity_dict, raw_topic_entity, entity_id):
    if entity_id in value_entity_dict:
        return entity_id
    if entity_id in raw_topic_entity:
        return raw_topic_entity[entity_id]
    sparql_query = sparql_id_english % entity_id
    # sparql_query = sparql_id % entity_id  # only english
    sparql = SPARQLWrapper(SPARQLPATH)
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if len(results["results"]["bindings"]) == 0:
        # return "UnName_Entity (%s)" % entity_id
        return "UnName_Entity"
    else:
        return entity_id

def id_2_relation_name(relation_id):
    return relation_id
    # sparql_query = sparql_id_relation_friendly % relation_id
    # sparql = SPARQLWrapper(SPARQLPATH)
    # sparql.setQuery(sparql_query)
    # sparql.setReturnFormat(JSON)
    # results = sparql.query().convert()
    # try:
    #     if len(results["results"]["bindings"]) == 0:
    #         return relation_id
    #     else:
    #         return results["results"]["bindings"][0]['tailEntity']['value'].replace('http://rdf.fbwq.com/ns/',
    #                                                                                          "").replace(
    #             "http://rdf.freebase.com/ns/", "")
    # except Exception as e:
    #     return relation_id


# return ture names of the entity; if cvt nodes, all are "UnName_Entity"
def id2entity_name_or_type(value_entity_dict, raw_topic_entity, entity_id):
    if entity_id in value_entity_dict:
        return value_entity_dict[entity_id]
    if entity_id in raw_topic_entity:
        return raw_topic_entity[entity_id]
    sparql_query = sparql_id_english % (entity_id)
    sparql = SPARQLWrapper(SPARQLPATH)
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if len(results["results"]["bindings"]) == 0:
        return "UnName_Entity"
    else:
        return unquote(results["results"]["bindings"][0]['tailEntity']['value']).replace('http://rdf.fbwq.com/ns/',
                                                                                         "").replace(
            "http://rdf.freebase.com/ns/", "")


def id_2_entity_description(tail_relation, head_relation, question, entity_id):
    if tail_relation != "":
        sparql_relations_extract_head = sparql_head_relations % entity_id
        head_relations = execurte_sparql(sparql_relations_extract_head)
        head_relations = replace_relation_prefix(head_relations)
        tail_relations = []
    else:
        sparql_relations_extract_tail = sparql_tail_relations % entity_id
        tail_relations = execurte_sparql(sparql_relations_extract_tail)
        tail_relations = replace_relation_prefix(tail_relations)
        # tail_relations = [relation.split(".")[-1] for relation in tail_relations]
        # head_relation = head_relation.split(".")[-1]
        head_relations = []

    if tail_relation != "":
        head_relations = [relation for relation in head_relations if not abandon_rels_description(relation)]
        head_relations = list(set(head_relations))
        total_relations = head_relations
        # pick top 5 relations to annotate the description of the entity
        if len(total_relations) > 5:
            data = {'width': '5', 'question': question,
                    'total_relations': '&;& '.join(total_relations)}
            response = requests.post(SLMPATH, json=data)
            total_relations = response.json()['topn_relations']

        total_relations = [relation.split(".")[-1] for relation in total_relations]
        tail_relation = tail_relation.split(".")[-1]
        # user_prompt = entity_2_description_tail.replace("{{HEAD_RELATIONS}}", "; ".join(total_relations)).replace(
        #     "{{QUESTION}}", question).replace("{{TAIL_RELATION}}", tail_relation)
        user_prompt = entity_2_description_tail_single.replace("{{HEAD_RELATION}}",
                                                               "; ".join(total_relations[:5])).replace(
            "{{QUESTION}}", question).replace("{{TAIL_RELATION}}", tail_relation)
    else:
        tail_relations = list(set(tail_relations))
        tail_relations = [relation for relation in tail_relations if not abandon_rels_description(relation)]
        total_relations = tail_relations
        if len(total_relations) > 5:
            data = {'width': '5', 'question': question,
                    'total_relations': '&;& '.join(total_relations)}
            response = requests.post(SLMPATH, json=data)
            total_relations = response.json()['topn_relations']
        total_relations = [relation.split(".")[-1] for relation in total_relations]
        head_relation = head_relation.split(".")[-1]
        user_prompt = entity_2_description_head_single.replace("{{TAIL_RELATION}}",
                                                               "; ".join(total_relations[:5])).replace(
            "{{QUESTION}}", question).replace("{{HEAD_RELATION}}", head_relation)
    return user_prompt


def ids_2_entities_description(tail_relation, head_relation, question, entity_ids):
    total_head_relations = []
    total_tail_relations = []
    for entity_id in entity_ids:
        if tail_relation != "":
            sparql_relations_extract_head = sparql_head_relations % entity_id
            head_relations = execurte_sparql(sparql_relations_extract_head)
            head_relations = replace_relation_prefix(head_relations)
            tail_relations = []
        else:
            sparql_relations_extract_tail = sparql_tail_relations % entity_id
            tail_relations = execurte_sparql(sparql_relations_extract_tail)
            tail_relations = replace_relation_prefix(tail_relations)
            head_relations = []
        total_head_relations.extend(head_relations)
        total_tail_relations.extend(tail_relations)

    if tail_relation != "":
        head_relations = list(set(total_head_relations))
        head_relations = [relation for relation in head_relations if not abandon_rels_description(relation)]
        total_relations = head_relations
        # pick top 5 relations to annotate the description of the entity
        if len(total_relations) > 5:
            data = {'width': '5', 'question': question,
                    'total_relations': '&;& '.join(total_relations)}
            response = requests.post(SLMPATH, json=data)
            total_relations = response.json()['topn_relations']
        total_relations_name=[]
        for relation in total_relations:
            relation_name=id_2_relation_name(relation)
            total_relations_name.append(relation_name)
        tail_relation_name=id_2_relation_name(tail_relation)
        # object_triplets_str = "sth. or sb. -> {} -> 'ENTITY'".format(tail_relation)
        # object_triplets_str = "sth. or sb. -> {} -> 'ENTITY'".format(tail_relation_name)
        object_triplets_str = tail_relation_name
        subject_triplets = []
        # for relation in total_relations[:5]:
        for relation in total_relations_name[:5]:
            # subject_triplet = "'ENTITY' -> {} -> sth., sb. or specific value".format(relation)
            # subject_triplets.append(subject_triplet)
            subject_triplets.append(relation)
        subject_triplets_str = "; ".join(subject_triplets)
        user_prompt = entity_2_description_light_light.replace("{{OBJECT_TRIPLETS}}", object_triplets_str).replace(
            "{{SUBJECT_TRIPLETS}}", subject_triplets_str)
        # user_prompt = entity_2_description_light.replace("{{OBJECT_TRIPLETS}}", object_triplets_str).replace(
        #     "{{SUBJECT_TRIPLETS}}", subject_triplets_str)
        # user_prompt = entity_2_description.replace("{{OBJECT_TRIPLETS}}", object_triplets_str).replace(
        #     "{{SUBJECT_TRIPLETS}}", subject_triplets_str)
    else:
        tail_relations = list(set(total_tail_relations))
        tail_relations = [relation for relation in tail_relations if not abandon_rels_description(relation)]
        total_relations = tail_relations
        if len(total_relations) > 5:
            data = {'width': '5', 'question': question,
                    'total_relations': '&;& '.join(total_relations)}
            response = requests.post(SLMPATH, json=data)
            total_relations = response.json()['topn_relations']
        # friendly name of relations
        total_relations_name=[]
        for relation in total_relations:
            relation_name=id_2_relation_name(relation)
            total_relations_name.append(relation_name)
        head_relation_name=id_2_relation_name(head_relation)
        # subject_triplets_str = "'ENTITY' -> {} -> sth. or sb.".format(head_relation)
        # subject_triplets_str = "'ENTITY' -> {} -> sth. or sb.".format(head_relation_name)
        subject_triplets_str = head_relation_name
        object_triplets = []
        for relation in total_relations_name[:5]:
            # object_triplet = "sth. or sb. -> {} -> 'ENTITY'".format(relation)
            # object_triplets.append(object_triplet)
            object_triplets.append(relation)
        object_triplets_str = "; ".join(object_triplets)
        user_prompt = entity_2_description_light_light.replace("{{OBJECT_TRIPLETS}}", object_triplets_str).replace(
            "{{SUBJECT_TRIPLETS}}", subject_triplets_str)
        # user_prompt = entity_2_description_light.replace("{{OBJECT_TRIPLETS}}", object_triplets_str).replace(
        #     "{{SUBJECT_TRIPLETS}}", subject_triplets_str)
        # user_prompt = entity_2_description.replace("{{OBJECT_TRIPLETS}}", object_triplets_str).replace(
        #     "{{SUBJECT_TRIPLETS}}", subject_triplets_str)
    return user_prompt
