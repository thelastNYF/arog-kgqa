import ast
import random
import re
import time

import httpx
from nltk.app.wordnet_app import explanation
from openai import OpenAI
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sentence_transformers import util
# from vllm import SamplingParams
from zhipuai import ZhipuAI

from freebase_func import *

import hashlib
import base64
from httpx_socks import SyncProxyTransport

transport = SyncProxyTransport.from_url("socks5://127.0.0.1:7891")
http_client = httpx.Client(transport=transport)
SLMPATH = 'http://{{SentenceTransformer Server}}:5000/sentence_transformer'
SLMPATH_COS = 'http://{{SentenceTransformer Server}}:5000/sentence_transformer_cos'
SLMPATH_COS_LIST = 'http://{{SentenceTransformer Server}}:5000/sentence_transformer_cos_list'


def jsonl_to_json(jsonl_file, json_file):
    with open(jsonl_file, 'r') as infile:
        with open(json_file, 'w') as outfile:
            json_lines = infile.readlines()
            json_list = [json.loads(line) for line in json_lines]
            json.dump(json_list, outfile, indent=4)


# Core APIs
def run_llm(prompt, temperature, max_tokens, opeani_api_keys, engine="gpt-3.5-turbo"):
    if "glm" in engine.lower():
        print(prompt)
        llm = ZhipuAI(api_key=opeani_api_keys)
        response = llm.chat.completions.create(
            model=engine.lower(),
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        print(response.choices[0].message)
        token_num = {}
        return response.choices[0].message.content, token_num
    elif "llama" in engine.lower():
        pass
    elif "gpt" in engine.lower():
        messages = [{"role": "system", "content": "You are an AI assistant that helps people find information."}]
        message_prompt = {"role": "user", "content": prompt}
        messages.append(message_prompt)
        print(prompt)
        logging.info(prompt)
        result = ""
        token_num = {}
        f = 0
        while f == 0:
            try:
                client = OpenAI(api_key=opeani_api_keys, http_client=http_client)
                completion = client.chat.completions.create(
                    model=engine,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    n=1,
                )
                result = completion.choices[0].message.content
                token_num = {"total": completion.usage.total_tokens, "input": completion.usage.prompt_tokens,
                             "output": completion.usage.completion_tokens}
                f = 1
            except Exception as e:
                print(e)
                print("openai error, retry")
                logging.warning("openai error, retry")
                time.sleep(1)
        print(result)
        logging.info(result)
        logging.info(token_num)
        return result, token_num


def generate_without_explored_paths(question, args):
    prompt = generate_directly + "\n\nQ: " + question + "\nA:"
    generator_response_directly, token_num = run_llm(prompt, args.temperature_reasoning, args.max_length,
                                                     args.opeani_api_keys, args.LLM_type)
    return generator_response_directly, token_num


# APIs for Stage 0: prepare data
def prepare_dataset(dataset_name):
    if dataset_name == 'cwq':
        with open('data/cwq_1000.json', encoding='utf-8') as f:
            # with open('../data/cwq.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'webqsp':
        with open('data/WebQSP.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'RawQuestion'
    elif dataset_name == 'grailqa':
        with open('data/grailqa.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'simpleqa':
        with open('../../data/SimpleQA.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'qald':
        with open('../../data/qald_10-en.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'webquestions':
        with open('../../data/WebQuestions.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'trex':
        with open('../../data/T-REX.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'input'
    elif dataset_name == 'zeroshotre':
        with open('../../data/Zero_Shot_RE.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'input'
    elif dataset_name == 'creak':
        with open('../../data/creak.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'sentence'
    else:
        print(
            "dataset not found, you should pick from {cwq, webqsp, grailqa}.")
        exit(-1)
    return datas, question_string


def generate_abs_question(question, args):
    prompt = question_abstractly + "\n\nQ: " + question
    abs_question_result, token_num = run_llm(prompt, args.temperature_reasoning, args.max_length, args.opeani_api_keys,
                                             args.LLM_type)
    lines = abs_question_result.split('\n')
    thought = ''
    reasoning_path = ''
    answer = ''
    answer_type = ''
    crucial_entities = []
    for line in lines:
        if line.startswith('Thought:'):
            thought = line[len('Thought:'):].strip()
        elif line.startswith('Reasoning Path:'):
            reasoning_path = line[len('Reasoning Path:'):].strip()
        elif line.startswith('Answer:'):
            answer = line[len('Answer:'):].strip()
    pattern = r'\(.*?\)'
    matches = re.findall(pattern, reasoning_path)
    matches = [item.replace('(', '').replace(')', '').strip() for item in matches if item not in answer]
    crucial_entities = list(set(matches))
    answer_type = re.findall(pattern, answer)
    if len(answer_type) > 0:
        answer_type = answer_type[0].replace('(', '').replace(')', '').strip()
    else:
        answer_type = ""
    return thought, reasoning_path, answer, answer_type, crucial_entities, token_num


def simple_hash_encrypt(input_string):
    sha_signature = hashlib.sha256(input_string.encode()).digest()
    encoded_hash = base64.urlsafe_b64encode(sha_signature).decode().rstrip('=\n')
    encoded_hash = encoded_hash.replace('-', '0').replace('_', '1').lower()
    # Virtual unique MID
    return 'm.' + encoded_hash[:10]


# APIs for Step 1 in Stage 2
def relation_search_prune(entity_id, entity_name, pre_relations, pre_head, question, args):
    sparql_relations_extract_head = sparql_head_relations % entity_id
    head_relations = execurte_sparql(sparql_relations_extract_head)
    head_relations = replace_relation_prefix(head_relations)

    sparql_relations_extract_tail = sparql_tail_relations % entity_id
    tail_relations = execurte_sparql(sparql_relations_extract_tail)
    tail_relations = replace_relation_prefix(tail_relations)

    head_relations = list(set(head_relations))
    tail_relations = list(set(tail_relations))

    if args.remove_unnecessary_rel:
        head_relations = [relation for relation in head_relations if not abandon_rels(relation)]
        tail_relations = [relation for relation in tail_relations if not abandon_rels(relation)]

    if len(pre_relations) != 0:
        tail_relations = [rel for rel in tail_relations if rel not in pre_relations]
        head_relations = [rel for rel in head_relations if rel not in pre_relations]

    total_relations = head_relations + tail_relations
    total_relations = list(set(total_relations))

    token_num = {'total': 0, 'input': 0, 'output': 0}
    if args.prune_tools == "llm":
        prompt = construct_relation_prune_prompt(question, entity_name, total_relations, args)
        prune_relations_result, token_num = run_llm(prompt, args.temperature_exploration, args.max_length,
                                                    args.opeani_api_keys,
                                                    args.LLM_type)
        flag, retrieve_relations_with_scores = clean_relations(prune_relations_result, entity_id, head_relations,
                                                               total_relations)

    elif args.prune_tools == "bm25":
        topn_relations, topn_scores = compute_bm25_similarity(question, total_relations, args.width)
        flag, retrieve_relations_with_scores = clean_relations_bm25_sent(topn_relations, topn_scores, entity_id,
                                                                         head_relations)
    else:
        model = SentenceTransformer('sentence-transformers/msmarco-distilbert-base-tas-b')
        topn_relations, topn_scores = retrieve_top_docs(question, total_relations, model, args.width)
        flag, retrieve_relations_with_scores = clean_relations_bm25_sent(topn_relations, topn_scores, entity_id,
                                                                         head_relations)

    if flag:
        return retrieve_relations_with_scores, token_num
    else:
        return [], token_num  # format error or too small max_length


def construct_relation_prune_prompt(question, entity_name, total_relations, args):
    return extract_relation_prompt_light % (
        args.width) + question + '\nTopic Entity: ' + entity_name + '\nRelations: ' + '; '.join(
        total_relations) + "\nThe output is: \n"
    # return extract_relation_prompt % (
    #     args.width, args.width) + question + '\nTopic Entity: ' + entity_name + '\nRelations: ' + '; '.join(
    #     total_relations) + "\nA: "


def clean_relations(string, entity_id, head_relations, valid_relations):
    # pattern = r"{\s*(?P<relation>[^()]+)\s+\(Score:\s+(?P<score>[0-9.]+)\)}"
    # relations = []
    # for match in re.finditer(pattern, string):
    #     relation = match.group("relation").strip()
    #     if ';' in relation or relation not in valid_relations:
    #         continue
    #     score = match.group("score")
    #     if not relation or not score:
    #         return False, "output uncompleted.."
    #     try:
    #         score = float(score)
    #     except ValueError:
    #         return False, "Invalid score"
    #     if relation in head_relations:
    #         relations.append({"entity": entity_id, "relation": relation, "score": score, "head": True})
    #     else:
    #         relations.append({"entity": entity_id, "relation": relation, "score": score, "head": False})
    # if not relations:
    #     return False, "No relations found"
    # return True, relations

    last_brace_l = string.rfind('[')
    last_brace_r = string.rfind(']')

    if last_brace_l < last_brace_r:
        string = string[last_brace_l:last_brace_r + 1]

    relations = []
    score = 0
    rel_list = eval(string.strip())
    for relation in rel_list:
        if relation in head_relations:
            relations.append({"entity": entity_id, "relation": relation, "score": score, "head": True})
        elif relation in valid_relations:
            relations.append({"entity": entity_id, "relation": relation, "score": score, "head": False})

    if not relations:
        return False, "No relations found"
    return True, relations


def clean_entities(string, total_entities):
    pattern = r"{\s*(?P<entity>[^:]+)\s+\(Score:\s+(?P<score>[0-9.]+)\)}"
    entities = []
    for match in re.finditer(pattern, string):
        entity = match.group("entity").strip()
        if ';' in entity:
            continue
        score = match.group("score")
        if not entity or not score:
            return False, "output uncompleted.."
        try:
            score = float(score)
        except ValueError:
            return False, "Invalid score"
        if entity in total_entities:
            entities.append({"entity": entity, "score": score})
        else:
            entities.append({"entity": entity, "score": score})
    if not entities:
        return False, "No entities found"
    return True, entities


# APIs for Step 4 in Stage 2; here, summary is neccesary?
def summarize_retrival_results(total_candidates_id, pre_relations, raw_topic_entity, retrieve_entities,
                               total_triplets):
    chain_of_entities = []
    entities_id = []
    topic_entities_name = list(raw_topic_entity.values())
    topic_entities_ids = list(raw_topic_entity.keys())
    for entity_select in retrieve_entities:
        if entity_select not in total_candidates_id:
            continue
        # here, we only retrieve entities beginning with 'm.'
        for temp_triple_select in total_triplets:
            if (entity_select.startswith('m.') and entity_select not in topic_entities_name and entity_select not in
                    topic_entities_ids and entity_select in temp_triple_select):
                chain_of_entities.append(temp_triple_select)
                pre_relation = temp_triple_select.split(', ')[1]
                if '|' in pre_relation:
                    pre_relations.append(pre_relation.split('|')[0])
                    pre_relations.append(pre_relation.split('|')[1])
                else:
                    pre_relations.append(pre_relation)
                if "(specific value)" not in entity_select:
                    entities_id.append(entity_select.split('(')[0].strip())
    entities_id = [entity_id for entity_id in entities_id if entity_id.startswith('m.')]
    chain_of_entities = list(dict.fromkeys(chain_of_entities))
    return pre_relations, entities_id, chain_of_entities


# APIs for Step 2 in Stage 2
def entity_search(entity, relation, value_entity_dict, id_name_dict, value_entity_list, head=True):
    if head:
        tail_entities_extract = sparql_tail_entities_extract % (entity, relation)
        entities = execurte_sparql(tail_entities_extract)
    else:
        # TODO: Amend the tail relation retrieval issue
        # head_entities_extract = sparql_head_entities_extract % (entity, relation)
        head_entities_extract = sparql_head_entities_extract % (relation, entity)
        entities = execurte_sparql(head_entities_extract)
    if entities is not None and len(entities) > 0:
        entity_ids = replace_entities_prefix(entities)
        new_entity = [entity for entity in entity_ids if entity.startswith("m.")]
    else:
        entity_ids = []
        new_entity = []
    if len(entity_ids) > 0 and len(new_entity) == 0:
        new_entity = []
        for entity_id in entity_ids:
            entity_key = simple_hash_encrypt(entity_id)
            entity_value = entity_id
            if entity_key not in value_entity_dict:
                value_entity_dict[entity_key] = entity_value
                id_name_dict[entity_key] = entity_value
            if entity_key not in value_entity_list:
                value_entity_list.append(entity_key)
            new_entity.append(entity_key)

    return new_entity, value_entity_dict, value_entity_list, id_name_dict


def entity_score_with_description(topic_entity_name, value_entity_dict, value_entity_list,
                                  raw_topic_entity, entity_relation, question, head_relation, tail_relation,
                                  id_description_dict, id_type_dict, id_name_dict, entity_candidates_id,
                                  call_num, args):
    relation = entity_relation["relation"]
    head = entity_relation["head"]
    topic_entity_id = entity_relation["entity"]
    entity_candidates_name = [id2entity_name_or_type(value_entity_dict, raw_topic_entity, entity_id) for entity_id in
                              entity_candidates_id]
    current_t = {'total': 0, 'input': 0, 'output': 0}
    cvt_flag = False
    # case1：all entity is unknown entity
    if all_unknown_entity(entity_candidates_name):
        next_relation_list = []
        for cvt_entity_id in entity_candidates_id:
            if head:
                sparql_relations_extract_head = sparql_head_relations % cvt_entity_id
                head_relations = execurte_sparql(sparql_relations_extract_head)
                head_relations = replace_relation_prefix(head_relations)
                if args.remove_unnecessary_rel:
                    head_relations = [relation for relation in head_relations if not abandon_rels(relation)]
                head_relations = [relation + '|' + next_relation for next_relation in head_relations]
                next_relation_list.extend(head_relations)
            else:
                sparql_relations_extract_tail = sparql_tail_relations % cvt_entity_id
                tail_relations = execurte_sparql(sparql_relations_extract_tail)
                tail_relations = replace_relation_prefix(tail_relations)
                if args.remove_unnecessary_rel:
                    tail_relations = [relation for relation in tail_relations if not abandon_rels(relation)]
                tail_relations = [next_relation + '|' + relation for next_relation in tail_relations]
                next_relation_list.extend(tail_relations)
        if len(next_relation_list) == 0:
            return [], [], [], current_t, call_num, cvt_flag
        next_relation_list = list(set(next_relation_list))
        flag = False
        retrieve_relations_with_scores = []
        # if args.prune_tools == "llm":
        #     prompt = construct_relation_prune_prompt(question, topic_entity_name, next_relation_list, args)
        #     call_num += 1
        #     prune_cvt_relations_result, token_num = run_llm(prompt, args.temperature_exploration, args.max_length,
        #                                                     args.opeani_api_keys,
        #                                                     args.LLM_type)
        #     for kk in token_num.keys():
        #         current_t[kk] += token_num[kk]
        #     flag, retrieve_relations_with_scores = clean_relations(prune_cvt_relations_result, topic_entity_id,
        #                                                            next_relation_list, next_relation_list)
        #     cvt_flag = True
        relation_name_list = []
        relation_score_list = []
        if flag:
            relation_with_score_list = retrieve_relations_with_scores[:args.width]
            for relation_with_score in relation_with_score_list:
                relation_name = relation_with_score["relation"]
                relation_name_list.append(relation_name)
                relation_score_list.append(relation_with_score["score"])
        else:
            response_input = {'width': args.width, 'question': question,
                              'total_relations': '&;& '.join(next_relation_list)}
            response = requests.post(SLMPATH, json=response_input)
            relation_name_list = response.json()['topn_relations']
            relation_score_list = []
        next_relation_list = []
        for relation_name in relation_name_list:
            if '|' in relation_name:
                if head:
                    next_relation = relation_name.split('|')[1]
                else:
                    next_relation = relation_name.split('|')[0]
                next_relation_list.append(next_relation)
        if len(next_relation_list) == 0:
            cvt_flag = False
            return [], [], [], current_t, call_num, cvt_flag
        # Annotate
        final_entity_candidates_id = []
        final_entity_candidates_name = []
        final_topn_scores = []
        # here, maybe 3 relations connected to the cvt node.
        for relation_name in relation_name_list:
            if '|' not in relation_name:
                continue
            else:
                if head:
                    next_relation = relation_name.split('|')[1]
                    next_entity_candidates_id, value_entity_dict = entity_search_cvt(topic_entity_id, relation,
                                                                                     next_relation,
                                                                                     value_entity_dict)
                else:
                    next_relation = relation_name.split('|')[0]
                    next_entity_candidates_id, value_entity_dict = entity_search_cvt_tail(topic_entity_id, relation,
                                                                                          next_relation,
                                                                                          value_entity_dict)
            next_entity_candidates_id = list(set(next_entity_candidates_id) - set(topic_entity_id))
            if len(next_entity_candidates_id) >= 20:
                next_entity_candidates_id = random.sample(next_entity_candidates_id, 20)
            next_entity_candidates_name = [id2entity_name_or_type(value_entity_dict, raw_topic_entity, entity_id) for
                                           entity_id in next_entity_candidates_id]
            if len(next_entity_candidates_name) == 0:
                continue
            if len(next_entity_candidates_name) > 50:
                response_input = {'width': 50, 'question': question,
                                  'total_relations': '&;& '.join(next_entity_candidates_name)}
                response = requests.post(SLMPATH, json=response_input)
                topn_scores = response.json()['topn_scores']
                topn_names = response.json()['topn_relations']
            else:
                topn_scores = [1] * len(next_entity_candidates_name)
                topn_names = next_entity_candidates_name
            temp_entity_candidates_name = []
            temp_entity_candidates_id = []
            final_topn_scores.extend(topn_scores)
            for index in range(len(topn_scores)):
                entity_index = next_entity_candidates_name.index(topn_names[index])
                temp_entity_candidates_id.append(next_entity_candidates_id[entity_index])
            final_entity_candidates_id.extend(temp_entity_candidates_id)
            if head:
                tail_relation = relation_name
            call_num += 1
            id_description_dict, id_type_dict, id_name_dict, token_num = entity_annotation_all(topic_entity_name,
                                                                                               question,
                                                                                               temp_entity_candidates_id,
                                                                                               head_relation,
                                                                                               tail_relation,
                                                                                               id_description_dict,
                                                                                               id_type_dict,
                                                                                               id_name_dict,
                                                                                               value_entity_dict,
                                                                                               value_entity_list,
                                                                                               args)
            for kk in token_num.keys():
                current_t[kk] += token_num[kk]
            for entity_id in temp_entity_candidates_id:
                if entity_id in id_type_dict:
                    entity_type_plain = entity_id + ' (' + id_type_dict[entity_id] + ')'
                else:
                    entity_type_plain = entity_id + ' (entity)'
                temp_entity_candidates_name.append(entity_type_plain)
            if head:
                temp_entity_candidates_name = ['|' + next_relation + ', ' + topn_name for topn_name in
                                               temp_entity_candidates_name]
            else:
                temp_entity_candidates_name = [topn_name + ', ' + next_relation + '|' for topn_name in
                                               temp_entity_candidates_name]
            final_entity_candidates_name.extend(temp_entity_candidates_name)
        return final_topn_scores, final_entity_candidates_name, final_entity_candidates_id, current_t, call_num, cvt_flag

    else:
        # case2: not all entity is UnName Entity; clear UnName Entity, if exits
        un_entity_index = [index for index, element in enumerate(entity_candidates_name) if
                           element.startswith('UnName_Entity')]
        for i in un_entity_index:
            entity_candidates_id[i] = "UnName_Entity_ID"
        entity_candidates_id = [candidate_id for candidate_id in entity_candidates_id if
                                candidate_id != "UnName_Entity_ID"]
        entity_candidates_name = [candidate_name for candidate_name in entity_candidates_name if
                                  not candidate_name.startswith('UnName_Entity')]
        final_entity_candidates_id = []  # match top entity, from name to the id; need to be annoted
        final_entity_candidates_name = []
        topn_scores = []
        if len(entity_candidates_name) > 50:
            response_input = {'width': 50, 'question': question,
                              'total_relations': "&;& ".join(entity_candidates_name)}
            response = requests.post(SLMPATH, json=response_input)
            topn_scores = response.json()['topn_scores']
            topn_names = response.json()['topn_relations']
            for index in range(len(topn_names)):
                entity_index = entity_candidates_name.index(topn_names[index])
                final_entity_candidates_id.append(entity_candidates_id[entity_index])
        else:
            final_entity_candidates_id = entity_candidates_id
            topn_scores = [1] * len(entity_candidates_id)
        call_num += 1
        id_description_dict, id_type_dict, id_name_dict, token_num = entity_annotation_all(topic_entity_name, question,
                                                                                           final_entity_candidates_id,
                                                                                           head_relation,
                                                                                           tail_relation,
                                                                                           id_description_dict,
                                                                                           id_type_dict,
                                                                                           id_name_dict,
                                                                                           value_entity_dict,
                                                                                           value_entity_list,
                                                                                           args)
        for kk in token_num.keys():
            current_t[kk] += token_num[kk]
        for entity_id in final_entity_candidates_id:
            if entity_id in id_type_dict:
                entity_type_plain = entity_id + ' (' + id_type_dict[entity_id] + ')'
            else:
                entity_type_plain = entity_id + ' (entity)'
            final_entity_candidates_name.append(entity_type_plain)
        return topn_scores, final_entity_candidates_name, final_entity_candidates_id, current_t, call_num, cvt_flag


def all_unknown_entity(entity_candidates):
    return all(candidate == "UnName_Entity" for candidate in entity_candidates)
    # return all(candidate.startswith("UnName_Entity (") for candidate in entity_candidates)


def entity_search_cvt(entity, relation, next_relation, value_entity_dict):
    cvt_entities_extract = sparql_cvt_entities_extract % (entity, relation, next_relation)
    entities = execurte_sparql(cvt_entities_extract)
    entity_ids = replace_entities_prefix(entities)
    entity_ids = list(set(entity_ids))  # filter several entity with cvt entity
    new_entity = [entity for entity in entity_ids if entity.startswith("m.") or entity.startswith("g.")]
    if len(entity_ids) > 0 and len(new_entity) == 0:
        new_entity = []
        for entity_id in entity_ids:
            entity_key = simple_hash_encrypt(entity_id)
            entity_value = entity_id
            if entity_key not in value_entity_dict:
                value_entity_dict[entity_key] = entity_value
            new_entity.append(entity_key)
    return new_entity, value_entity_dict


def entity_search_cvt_tail(entity, relation, next_relation, value_entity_dict):
    cvt_entities_extract = sparql_cvt_entities_extract_tail % (relation, next_relation, entity)
    entities = execurte_sparql(cvt_entities_extract)
    entity_ids = replace_entities_prefix(entities)
    entity_ids = list(set(entity_ids))  # filter several entity with cvt entity
    new_entity = [entity for entity in entity_ids if entity.startswith("m.") or entity.startswith("g.")]
    if len(entity_ids) > 0 and len(new_entity) == 0:
        new_entity = []
        for entity_id in entity_ids:
            entity_key = simple_hash_encrypt(entity_id)
            entity_value = entity_id
            if entity_key not in value_entity_dict:
                value_entity_dict[entity_key] = entity_value
            new_entity.append(entity_key)
    return new_entity, value_entity_dict


def entity_annotation_all(topic_entity_name, question, entity_ids, head_relation, tail_relation, id_description_dict,
                          id_type_dict,
                          id_name_dict, value_entity_dict,
                          value_entity_list, args):
    entity_type = ""
    entity_description = [""]
    token_num = {'total': 0, 'input': 0, 'output': 0}
    for entity_id in entity_ids:
        if entity_id in value_entity_list:
            entity_type = "specific value"
            entity_description = ["specific value"]
            break
    for entity_id in entity_ids:
        if entity_id not in id_name_dict:
            id_name = id2entity_name_or_type(value_entity_dict, {}, entity_id)
            id_name_dict[entity_id] = id_name
    if entity_type != "specific value":
        if args.entity_abs:
            try:
                entity_description_prompt = ids_2_entities_description(tail_relation, head_relation, question,
                                                                       entity_ids)
                abs_entity_result, token_num = run_llm(entity_description_prompt, args.temperature_exploration,
                                                       args.max_length,
                                                       args.opeani_api_keys, args.LLM_type)
                restore_dict = eval(abs_entity_result.strip())
                assert isinstance(restore_dict, dict)
                assert len(list(restore_dict.keys())) == 2
            except Exception as e:
                restore_dict = {'type': "entity", 'description': "sth. or sb."}
        else:
            restore_dict = {'type': "entity", 'description': "sth. or sb."}
        entity_type = restore_dict['type'].strip()
    for entity_id in entity_ids:
        if entity_id not in id_type_dict:
            id_type_dict[entity_id] = entity_type
        elif entity_type.lower() not in id_type_dict[entity_id].lower():
            id_type_dict[entity_id] = id_type_dict[entity_id] + ', ' + entity_type
        if entity_id in id_description_dict:
            entity_description = id_description_dict[entity_id]
        if tail_relation != '':
            entity_description_item = topic_entity_name + ', ' + tail_relation + ', ' + entity_id + ' (' + id_type_dict[
                entity_id] + ')'
            entity_description.append(entity_description_item)
            for entity_type_item in id_type_dict[entity_id].split(', '):
                entity_description_item = topic_entity_name + ', ' + tail_relation + ', ' + entity_id + ' (' + entity_type_item + ')'
                entity_description.append(entity_description_item)
        else:
            entity_description_item = entity_id + ' (' + id_type_dict[
                entity_id] + ')' + ', ' + head_relation + ', ' + topic_entity_name
            entity_description.append(entity_description_item)
            for entity_type_item in id_type_dict[entity_id].split(', '):
                entity_description_item = entity_id + ' (' + entity_type_item + ')' + ', ' + head_relation + ', ' + topic_entity_name
                entity_description.append(entity_description_item)
        id_description_dict[entity_id] = entity_description

    return id_description_dict, id_type_dict, id_name_dict, token_num


def update_history(topic_entity, entity_candidates, entity, scores, entity_candidates_id, total_candidates,
                   total_scores,
                   total_relations, total_entities_id, total_topic_entities, total_topic_entities_name, total_head):
    candidates_relation = [entity['relation']] * len(entity_candidates)
    topic_entities = [entity['entity']] * len(entity_candidates)
    topic_entities_name = [topic_entity[entity['entity']]] * len(entity_candidates)
    head_num = [entity['head']] * len(entity_candidates)
    total_candidates.extend(entity_candidates)
    total_scores.extend(scores)
    total_relations.extend(candidates_relation)
    total_entities_id.extend(entity_candidates_id)
    total_topic_entities.extend(topic_entities)
    total_topic_entities_name.extend(topic_entities_name)
    total_head.extend(head_num)
    return total_candidates, total_scores, total_relations, total_entities_id, total_topic_entities, total_topic_entities_name, total_head


# APIs for Stage 3, case 2: we need a judge and a generator
def reasoning(question, cluster_chain_of_entities, id_name_dict, current_retrieve_depth, end_flag, call_num, args):
    current_t = {'total': 0, 'input': 0, 'output': 0}
    user_judge_prompt = judge_prompt_light + question + '\n'
    # user_judge_prompt = judge_prompt + question + '\n'
    chain_prompt = ""
    for triplets_list in cluster_chain_of_entities:
        chain_prompt += '\n'.join(triplets_list) + '\n'
    user_judge_prompt += "Knowledge Triplets: " + chain_prompt + 'A: '
    call_num += 1
    judge_response, token_num = run_llm(user_judge_prompt, args.temperature_reasoning, args.max_length,
                                        args.opeani_api_keys,
                                        args.LLM_type)
    for kk in token_num.keys():
        current_t[kk] += token_num[kk]
    flag = extract_answer(judge_response)
    if if_true(flag) or current_retrieve_depth >= args.depth or end_flag:
        if args.reason_with_name:
            if args.filter_judge:
                for entity_id in id_name_dict:
                    chain_prompt = chain_prompt.replace(entity_id, id_name_dict[entity_id])
                user_generator_prompt = generator_prompt + question + '\n'
                user_generator_prompt += "Knowledge Triplets: " + chain_prompt + 'A: '
                call_num += 1
                generator_response_with_name, token_num = run_llm(user_generator_prompt, args.temperature_reasoning,
                                                                  args.max_length,
                                                                  args.opeani_api_keys, args.LLM_type)
            else:
                call_num += 1
                generator_response_with_name, token_num = generate_without_explored_paths(question, args)
            for kk in token_num.keys():
                current_t[kk] += token_num[kk]
            return True, None, generator_response_with_name, current_t, call_num
        else:
            if args.filter_judge:
                user_generator_prompt = generator_prompt + question + '\n'
                user_generator_prompt += "Knowledge Triplets: " + chain_prompt + 'A: '
                call_num += 1
                generator_response, token_num = run_llm(user_generator_prompt, args.temperature_reasoning,
                                                        args.max_length,
                                                        args.opeani_api_keys, args.LLM_type)
            else:
                call_num += 1
                generator_response, token_num = generate_without_explored_paths(question, args)
            for kk in token_num.keys():
                current_t[kk] += token_num[kk]
            return True, generator_response, None, current_t, call_num
    else:
        return False, judge_response, None, current_t, call_num


def extract_answer(text):
    start_index = text.find("{")
    end_index = text.find("}")
    if start_index != -1 and end_index != -1:
        return text[start_index + 1:end_index].strip()
    else:
        return ""


def if_true(prompt):
    if prompt.lower().strip().replace(" ", "") == "yes":
        return True
    return False


# APIs for Stage 3, end the program
def save_2_jsonl(task_id, value_entity_dict, raw_topic_entity, question, answer, cluster_chain_of_entities,
                 id_name_dict, call_num, match_times, answer_list, token_num, tt, args):
    cluster_chain_of_entities_str = str(cluster_chain_of_entities)
    for entity_id in id_name_dict:
        answer = answer.replace(entity_id, id_name_dict[entity_id])
        cluster_chain_of_entities_str = cluster_chain_of_entities_str.replace(entity_id, id_name_dict[entity_id])
    result_dict = {"question": question, "results": answer, "reasoning_chains": cluster_chain_of_entities,
                   "reasoning_chains_str": cluster_chain_of_entities_str, "call_num": call_num,
                   "match_times": match_times, "answer_list": answer_list, "token_num": token_num, "time": tt}
    with open(
            "ARoG_0720_naive_1_{}_{}_{}_{}_{}_{}.jsonl".format(args.dataset, str(args.question_abs), str(args.entity_abs),"depth_"+str(args.depth),"width_"+str(args.width),
                                                          task_id),
            "a") as outfile:
        json_str = json.dumps(result_dict)
        outfile.write(json_str + "\n")


# APIs for Stage 3, end the program
def save_2_jsonl_with_name(task_id, value_entity_dict, raw_topic_entity, question, answer, cluster_chain_of_entities,
                           id_name_dict, call_num, match_times, answer_list, token_num, tt, args):
    cluster_chain_of_entities_str = str(cluster_chain_of_entities)
    for entity_id in id_name_dict:
        answer = answer.replace(entity_id, id_name_dict[entity_id])
        cluster_chain_of_entities_str = cluster_chain_of_entities_str.replace(entity_id, id_name_dict[entity_id])
    result_dict = {"question": question, "results": answer, "reasoning_chains": cluster_chain_of_entities,
                   "reasoning_chains_str": cluster_chain_of_entities_str, "call_num": call_num,
                   "match_times": match_times, "answer_list": answer_list, "token_num": token_num, "time": tt}
    with open(
            "ARoG_0720_naive_1_with_name_{}_{}_{}_{}_{}_{}.jsonl".format(args.dataset, str(args.question_abs),
                                                                    str(args.entity_abs),"depth_"+str(args.depth),"width_"+str(args.width),
                                                                    task_id),
            "a") as outfile:
        json_str = json.dumps(result_dict)
        outfile.write(json_str + "\n")


# Several BM25 or SentenceTransformer Similarity
def retrieve_top_docs(query, docs, model, width=3):
    """
    Retrieve the topn most relevant documents for the given query.

    Parameters:
    - query (str): The input query.
    - docs (list of str): The list of documents to search from.
    - model_name (str): The name of the SentenceTransformer model to use.
    - width (int): The number of top documents to return.

    Returns:
    - list of float: A list of scores for the topn documents.
    - list of str: A list of the topn documents.
    """

    query_emb = model.encode(query)
    doc_emb = model.encode(docs)

    scores = util.dot_score(query_emb, doc_emb)[0].cpu().tolist()

    doc_score_pairs = sorted(list(zip(docs, scores)), key=lambda x: x[1], reverse=True)

    top_docs = [pair[0] for pair in doc_score_pairs[:width]]
    top_scores = [pair[1] for pair in doc_score_pairs[:width]]

    return top_docs, top_scores


def compute_bm25_similarity(query, corpus, width=3):
    """
    Computes the BM25 similarity between a question and a list of relations,
    and returns the topn relations with the highest similarity along with their scores.

    Args:
    - question (str): Input question.
    - relations_list (list): List of relations.
    - width (int): Number of top relations to return.

    Returns:
    - list, list: topn relations with the highest similarity and their respective scores.
    """

    tokenized_corpus = [doc.split(" ") for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query.split(" ")

    doc_scores = bm25.get_scores(tokenized_query)

    relations = bm25.get_top_n(tokenized_query, corpus, n=width)
    doc_scores = sorted(doc_scores, reverse=True)[:width]

    return relations, doc_scores


def clean_relations_bm25_sent(topn_relations, topn_scores, entity_id, head_relations):
    relations = []
    if if_all_zero(topn_scores):
        topn_scores = [float(1 / len(topn_scores))] * len(topn_scores)
    for relation in topn_relations:
        i = topn_relations.index(relation)
        if relation in head_relations:
            relations.append({"entity": entity_id, "relation": relation, "score": topn_scores[i], "head": True})
        else:
            relations.append({"entity": entity_id, "relation": relation, "score": topn_scores[i], "head": False})
    return True, relations


def if_all_zero(topn_scores):
    return all(score == 0 for score in topn_scores)
