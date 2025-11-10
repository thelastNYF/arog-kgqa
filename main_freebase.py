import argparse
import time
import traceback

from tqdm import tqdm
from utils import *
from freebase_func import *
import random
from concurrent.futures import ProcessPoolExecutor


def task_run(datas, question_string, args, task_id):
    reasoning_path_list = []
    if args.filter_cot:
        if args.dataset == "cwq":
            with open('CoT/cot_cwq_alias_right.json', 'r') as f:
                cot_question_list = json.load(f)
        elif args.dataset == "webqsp":
            with open('CoT/cot_webqsp_right.json', 'r') as f:
                cot_question_list = json.load(f)
        elif args.dataset == "grailqa":
            with open('CoT/cot_grailqa_right.json', 'r') as f:
                cot_question_list = json.load(f)
    else:
        cot_question_list = []
    if args.dataset == "cwq":
        with open('data/cwq_1000_alias.json', 'r') as f:
            cwq_alias_datas = json.load(f)
    for data in tqdm(datas):
        start_time = time.time()
        call_num = 0
        all_t = {'total': 0, 'input': 0, 'output': 0}
        cluster_chain_of_entities = []
        pre_relations = []
        id_description_dict = {}
        id_type_dict = {}
        id_name_dict = {}
        value_entity_dict = {}
        value_entity_list = []
        question = data[question_string]
        total_sorted_scores = []
        topic_entity = data['topic_entity']
        raw_topic_entity = data['topic_entity']
        answer_list = []
        if args.dataset == "cwq":
            origin_data = [j for j in cwq_alias_datas if j[question_string] == data[question_string]][0]
            if 'answer_names' in origin_data:
                answers = origin_data["answer_names"]
                answer_list.extend(answers)
        elif args.dataset == "webqsp":
            answers = data["Parses"]
            for answer in answers:
                for name in answer['Answers']:
                    if name['EntityName'] == None:
                        answer_list.append(name['AnswerArgument'])
                    else:
                        answer_list.append(name['EntityName'])
        elif args.dataset == "grailqa":
            answers = data["answer"]
            for answer in answers:
                if "entity_name" in answer:
                    answer_list.append(answer['entity_name'])
                else:
                    answer_list.append(answer['answer_argument'])
        answer_list = list(set(answer_list))
        pre_heads = [-1] * len(topic_entity)
        match_flag = True
        match_times = 0
        # if question in cot_question_list:
        #     continue
        # if True:
        try:
            #     Stage 1, Generate reasoning_path in the form of entity property path
            cot_replaced_triples_str = None
            reasoning_path = None
            predicated_answer = ""
            answer_type = ""
            crucial_entities = []
            predicated_entities = []
            if args.question_abs:
                call_num += 1
                thought, reasoning_path, predicated_answer, answer_type, crucial_entities, token_num = generate_abs_question(
                    question, args)
                for kk in token_num.keys():
                    all_t[kk] += token_num[kk]
                predicated_entities = crucial_entities.copy()
                predicated_entities.append(answer_type)
                cot_replaced_triples_str = reasoning_path.replace("}", "").replace("{", "").replace(" -> ", ", ").split(
                    "; ")
                reasoning_path_list.append(
                    {"question": question, "reasoning_path": reasoning_path})

            # Stage 2, Retrieve
            current_retrieve_depth=0
            for depth in range(1, args.depth + 1):
                depth_flag = False
                current_retrieve_depth+=1
                print('topic_entity: ', topic_entity)
                logging.info('topic_entity: %s' % str(topic_entity))
                current_entity_relations_list = []
                if len(topic_entity) == 0:
                    call_num += 1
                    results, token_num = generate_without_explored_paths(question, args)
                    for kk in token_num.keys():
                        all_t[kk] += token_num[kk]
                    tt=time.time()-start_time
                    if args.reason_with_name:
                        save_2_jsonl_with_name(task_id, value_entity_dict, raw_topic_entity, question,
                                                   results,
                                                   cluster_chain_of_entities, id_name_dict, call_num, match_times,
                                                   answer_list, all_t, tt,
                                                   args)
                    else:
                        save_2_jsonl(task_id, value_entity_dict, raw_topic_entity, question,
                                     results,
                                     cluster_chain_of_entities, id_name_dict, call_num, match_times,
                                     answer_list, all_t, tt,
                                     args)

                    break
                total_candidates = []
                total_scores = []
                total_relations = []
                total_entities_id = []
                total_topic_entities = []
                total_topic_entities_name = []
                total_head = []
                i = 0
                for entity in topic_entity:
                    # Step 1, Relation-prune, the output form: {"entity": entity_id, "relation": relation, "score": score, "head": False}
                    call_num += 1
                    retrieve_relations_with_scores, token_num = relation_search_prune(entity, topic_entity[entity],
                                                                                      pre_relations,
                                                                                      pre_heads[i], question, args)
                    for kk in token_num.keys():
                        all_t[kk] += token_num[kk]
                    current_entity_relations_list.extend(retrieve_relations_with_scores)
                    i += 1
                for entity_relation in current_entity_relations_list:
                    # Step 2, Entity-prune after entity search, score entity with the guidance reasoning_path
                    tail_relation = ""
                    head_relation = ""
                    topic_entity_name = topic_entity[entity_relation['entity']]
                    if entity_relation['head']:
                        entity_candidates_id, value_entity_dict, value_entity_list, id_name_dict = entity_search(
                            entity_relation['entity'], entity_relation['relation'], value_entity_dict, id_name_dict,
                            value_entity_list, True)
                        tail_relation = entity_relation['relation']
                    else:
                        entity_candidates_id, value_entity_dict, value_entity_list, id_name_dict = entity_search(
                            entity_relation['entity'], entity_relation['relation'], value_entity_dict, id_name_dict,
                            value_entity_list, False)
                        head_relation = entity_relation['relation']
                    if len(entity_candidates_id) >= 20:
                        entity_candidates_id = random.sample(entity_candidates_id, args.num_retain_entity)
                    if len(entity_candidates_id) == 0:
                        continue
                    scores, entity_candidates, entity_candidates_id, token_num, call_num, cvt_flag = entity_score_with_description(
                        topic_entity_name,
                        value_entity_dict,
                        value_entity_list,
                        raw_topic_entity,
                        entity_relation,
                        question,
                        head_relation,
                        tail_relation,
                        id_description_dict,
                        id_type_dict,
                        id_name_dict,
                        entity_candidates_id,
                        call_num,
                        args)
                    for kk in token_num.keys():
                        all_t[kk] += token_num[kk]
                    if cvt_flag:
                        depth_flag = True
                    (total_candidates, total_scores, total_relations, total_entities_id, total_topic_entities,
                     total_topic_entities_name, total_head) = update_history(
                        topic_entity, entity_candidates, entity_relation, scores, entity_candidates_id,
                        total_candidates, total_scores,
                        total_relations, total_entities_id, total_topic_entities, total_topic_entities_name,
                        total_head)
                # Step 3, Triplets-prune, score entities under total_triplets instead of calculating similarity in BeamSearch format
                total_triplets = []
                total_candidates_name = []
                for index in range(len(total_candidates)):
                    if total_head[index]:
                        if total_candidates[index].startswith('|'):
                            total_triplets.append(
                                total_topic_entities_name[index] + ', ' + total_relations[index] + total_candidates[
                                    index])
                            total_candidates_name.append(total_candidates[index].split(', ')[1])
                        else:
                            total_triplets.append(
                                total_topic_entities_name[index] + ', ' + total_relations[index] + ', ' +
                                total_candidates[
                                    index])
                            total_candidates_name.append(total_candidates[index])
                    else:
                        if total_candidates[index].endswith('|'):
                            total_triplets.append(
                                total_candidates[index] + total_relations[index] + ', ' + total_topic_entities_name[
                                    index])
                            total_candidates_name.append(total_candidates[index].split(', ')[0])
                        else:
                            total_triplets.append(total_candidates[index] + ', ' + total_relations[index] + ', ' +
                                                  total_topic_entities_name[index])
                            total_candidates_name.append(total_candidates[index])
                total_candidates_id = [item.split('(')[0].strip() for item in total_candidates_name if
                                       item.startswith('m.') or item.startswith('g.')]
                # use slm to prune
                total_candidates_id = list(set(total_candidates_id) - set(topic_entity.keys()))
                total_candidates_kg_names = []
                if args.entity_abs:
                    for entity_id in total_candidates_id:
                        if entity_id in id_description_dict:
                            for description in id_description_dict[entity_id]:
                                if description != "":
                                    total_candidates_kg_names.append(description)
                    total_triplets_new = []
                    for triple in total_candidates_kg_names:
                        for entity_id in id_name_dict:
                            if entity_id in triple:
                                triple = triple.replace(entity_id, id_name_dict[entity_id])
                        total_triplets_new.append(triple)
                    total_candidates_kg_names = total_triplets_new
                    if len(total_candidates_kg_names) == 0:
                        total_candidates_kg_names = [
                            id2entity_name_or_type(value_entity_dict, raw_topic_entity, entity_id)
                            for entity_id in total_candidates_id]
                else:
                    total_candidates_kg_names = [
                        id2entity_name_or_type(value_entity_dict, raw_topic_entity, entity_id)
                        for entity_id in total_candidates_id]
                if len(total_candidates_kg_names) == 0:
                    total_candidates_kg_names = total_candidates_id
                if len(total_candidates_kg_names) == 0:
                    total_candidates_kg_names = ['nothing']
                hit_entities = []
                if args.question_abs:
                    for entity_id in total_candidates_id:
                        if entity_id in id_name_dict:
                            if id_name_dict[entity_id].lower() in reasoning_path.lower():
                                hit_entities.append(entity_id)
                slm_total_scores = []
                slm_total_names = []
                slm_total_predicated_entity = []
                if args.question_abs:
                    pass
                else:
                    cot_replaced_triples_str = [question]
                for predicated_entity in cot_replaced_triples_str:
                    response_input = {'same_part': '&&&&&', 'width': len(total_candidates_kg_names),
                                      'question': predicated_entity,
                                      'total_relations': '&;& '.join(total_candidates_kg_names)}
                    response = requests.post(SLMPATH_COS_LIST, json=response_input)
                    try:
                        slm_scores = response.json()['topn_scores']
                        slm_names = response.json()['topn_relations']
                    except:
                        slm_scores = []
                        slm_names = []
                    slm_total_scores.extend(slm_scores)
                    slm_total_names.extend(slm_names)
                    slm_total_predicated_entity.extend([predicated_entity] * len(total_candidates_kg_names))
                combined = list(zip(slm_total_scores, slm_total_names, slm_total_predicated_entity))
                combined.sort(reverse=True)
                sorted_names = [name for score, name, _ in combined]
                sorted_scores = [score for score, name, _ in combined]
                total_sorted_scores.extend(sorted_scores)
                explore_entities_abs_q = []
                explore_entities_abs_q_score = []
                explore_entities_q = []
                explore_entities_q_score = []
                explore_entities = []
                for triple_score, triple_item, _ in combined:
                    for entity_id in total_candidates_id:
                        if id_name_dict[entity_id] in triple_item and entity_id not in explore_entities_abs_q:
                            explore_entities_abs_q.append(entity_id)
                            explore_entities_abs_q_score.append(triple_score)
                explore_entities_abs_q = list(dict.fromkeys(explore_entities_abs_q))
                explore_entities_abs_q = explore_entities_abs_q[:args.width]
                if args.question_abs:
                    response_input = {'same_part': '&&&&&', 'width': len(total_candidates_kg_names),
                                      'question': question,
                                      'total_relations': '&;& '.join(total_candidates_kg_names)}
                    response = requests.post(SLMPATH_COS_LIST, json=response_input)
                    try:
                        slm_scores = response.json()['topn_scores']
                        slm_names = response.json()['topn_relations']
                    except:
                        slm_scores = []
                        slm_names = []
                    slm_total_scores.extend(slm_scores)
                    slm_total_names.extend(slm_names)
                    combined_naive = list(zip(slm_scores, slm_names))
                    combined_naive.sort(reverse=True)
                    sorted_names = [name for score, name in combined_naive]
                    total_sorted_scores.extend(sorted_scores)
                    sorted_names = list(dict.fromkeys(sorted_names))
                    for triple_score, triple_item in combined_naive:
                        for entity_id in total_candidates_id:
                            if id_name_dict[entity_id] in triple_item and entity_id not in explore_entities_q:
                                explore_entities_q.append(entity_id)
                                explore_entities_q_score.append(triple_score)
                    explore_entities_q = explore_entities_q[:args.width]
                    explore_entities = list(dict.fromkeys(explore_entities_abs_q + explore_entities_q))
                else:
                    explore_entities = explore_entities_abs_q[:args.width]

                for entity_id in hit_entities:
                    if entity_id not in explore_entities:
                        explore_entities.append(entity_id)
                        total_sorted_scores.append(1.0)
                pre_relations, entities_id, chain_of_entities = summarize_retrival_results(total_candidates_id,
                                                                                           pre_relations,
                                                                                           raw_topic_entity,
                                                                                           explore_entities,
                                                                                           total_triplets)
                entities_id = list(set(entities_id) & set(explore_entities_abs_q))
                if match_flag:
                    match_times += 1
                logging.info('retrieved_entities: %s' % str(explore_entities))
                logging.info('chain_of_entities: %s' % str(chain_of_entities))
                logging.info('chain_of_entities (retrieved_triples): %s' % str(chain_of_entities))
                cluster_chain_of_entities.append(chain_of_entities)

                # Stage 3, Judge and Generate answer
                if len(explore_entities) == 0:
                    end_flag = True
                else:
                    end_flag = False
                stop, results, results_with_name, token_num, call_num = reasoning(question, cluster_chain_of_entities,
                                                                                  id_name_dict, current_retrieve_depth,
                                                                                  end_flag, call_num, args)
                for kk in token_num.keys():
                    all_t[kk] += token_num[kk]
                if stop:
                    logging.info("ARoG stoped at depth %d." % depth)
                    end_time = time.time()
                    tt = end_time - start_time
                    if args.reason_with_name:
                        save_2_jsonl_with_name(task_id, value_entity_dict, raw_topic_entity, question,
                                               results_with_name,
                                               cluster_chain_of_entities, id_name_dict, call_num, match_times,
                                               answer_list, all_t, tt,
                                               args)
                    else:
                        save_2_jsonl(task_id, value_entity_dict, raw_topic_entity, question, results,
                                     cluster_chain_of_entities, id_name_dict, call_num, match_times, answer_list,
                                     all_t, tt,
                                     args)
                    break
                else:
                    logging.info("depth %d still not find the answer." % depth)
                    topic_entity = {}
                    for entity in entities_id:
                        if entity in id_type_dict:
                            topic_entity[entity] = entity + " (" + id_type_dict[entity] + ")"
                        else:
                            topic_entity[entity] = id2entity_name_or_type_privacy(value_entity_dict, raw_topic_entity,
                                                                                  entity)
                        pre_heads = [-1] * len(topic_entity)
                    continue
        except Exception as e:
            print("we pass %s" % data[question_string])
            print(e)
            logging.warning("we pass %s" % data[question_string])
            logging.warning(e)
            traceback.print_exc()
            logging.error(f"we pass: {e}\n{traceback.format_exc()}")
            continue
    if args.max_worker == 1:
        jsonl_to_json(
            "ARoG_0720_naive_1_{}_{}_{}_{}_{}_{}.jsonl".format(args.dataset, str(args.question_abs), str(args.entity_abs),"depth_"+str(args.depth),"width_"+str(args.width),
                                                          task_id),
            "ARoG_0720_naive_1_{}_{}_{}_{}_{}_{}.json".format(args.dataset, str(args.question_abs), str(args.entity_abs),"depth_"+str(args.depth),"width_"+str(args.width),
                                                         task_id))
        if args.reason_with_name:
            jsonl_to_json(
                "ARoG_0720_naive_1_with_name_{}_{}_{}_{}_{}_{}.jsonl".format(args.dataset, str(args.question_abs),
                                                                        str(args.entity_abs),"depth_"+str(args.depth),"width_"+str(args.width),
                                                                        task_id),
                "ARoG_0720_naive_1_with_name_{}_{}_{}_{}_{}_{}.json".format(args.dataset, str(args.question_abs),
                                                                       str(args.entity_abs),"depth_"+str(args.depth),"width_"+str(args.width),
                                                                       task_id))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str,
                        default="webqsp", help="choose the dataset(QA).")
    parser.add_argument("--max_length", type=int,
                        default=256, help="the max length of LLMs output.")
    parser.add_argument("--temperature_exploration", type=float,
                        default=0.4, help="the temperature in exploration stage.")
    parser.add_argument("--temperature_reasoning", type=float,
                        default=0, help="the temperature in reasoning stage.")
    parser.add_argument("--width", type=int,
                        default=3, help="choose the search width of ARoG.")
    parser.add_argument("--depth", type=int,
                        default=3, help="choose the search depth of ARoG.")
    parser.add_argument("--remove_unnecessary_rel", type=bool,
                        default=True, help="whether removing unnecessary relations.")
    parser.add_argument("--question_abs", action="store_false", help="whether abstract question.")
    parser.add_argument("--entity_abs", action="store_false", help="whether abstract entity.")
    parser.add_argument("--filter_cot", action="store_true",
                        help="whether filter samples which could be answered with CoT approach.")
    parser.add_argument("--filter_judge", action="store_false",
                        help="whether use CoT manner or total existing evidences to answer, when no answers are identified in evidence.")
    parser.add_argument("--reason_with_name", action="store_true",
                        help="In the final reasoning stage, save answers in two ways: one where all entities in the evidence are replaced with formal name / formal name + type, and another where the mid+type format is retained. Note that formal name and type may conflict.")
    parser.add_argument("--naive_retrieve", action="store_false",
                        help="whether use naive retrieval methods. store_true means ete retrieval defaultly")
    parser.add_argument("--slm_triple_prune", action="store_false",
                        help="whether use slm to prune triples.")
    parser.add_argument("--LLM_type", type=str,
                        default="gpt-4o-mini-2024-07-18", help="base LLM model.")
    parser.add_argument("--opeani_api_keys", type=str,
                        default="{OPEANI_API_KEY}",
                        help="if the LLM_type is gpt-3.5-turbo or gpt-4, you need add your own openai api keys.")
    parser.add_argument("--num_retain_entity", type=int,
                        default=5, help="Number of entities retained during entities search.")
    parser.add_argument("--prune_tools", type=str,
                        default="llm",
                        help="prune tools for ARoG, can be llm (same as LLM_type), bm25 or sentencebert.")
    parser.add_argument("--max_worker", type=int,
                        default=1,
                        help="number of max_worker")
    args = parser.parse_args()
    datas, question_string = prepare_dataset(args.dataset)
    logging.basicConfig(
        filename='ARoG_%s_%s_%s_0720_naive_1.log' % (args.dataset, str(args.question_abs), str(args.entity_abs)),
        filemode='w',
        level=logging.INFO,
        encoding='utf-8', format='%(asctime)s %(message)s')
    logging.warning('You are given a warning!')
    logging.info("Start Running ARoG with description on %s dataset." % args.dataset)
    llm = None
    random.seed(12345)
    if args.dataset == "webqsp":
        datas = random.sample(datas, len(datas))
        # datas = random.sample(datas, int(len(datas) / 10))
        # datas=datas[int(len(datas) / 10):]
    else:
        datas = random.sample(datas, 1000)
    if args.max_worker == 1:
        task_run(datas, question_string, args, -1)
    else:
        sub_datas = [datas[i::args.max_worker] for i in range(args.max_worker)]
        with ProcessPoolExecutor(max_workers=args.max_worker) as executor:
            futures = [executor.submit(task_run, sub_data, question_string, args, i) for i, sub_data in
                       enumerate(sub_datas)]
            for future in futures:
                future.result()
        combined_list = []
        for i in range(args.max_worker):
            try:
                jsonl_to_json(
                    "ARoG_0720_naive_1_{}_{}_{}_{}_{}_{}.jsonl".format(args.dataset, str(args.question_abs),
                                                                  str(args.entity_abs),"depth_"+str(args.depth),"width_"+str(args.width),
                                                                  i),
                    "ARoG_0720_naive_1_{}_{}_{}_{}_{}_{}.json".format(args.dataset, str(args.question_abs),
                                                                 str(args.entity_abs),"depth_"+str(args.depth),"width_"+str(args.width),
                                                                 i))
                if args.reason_with_name:
                    jsonl_to_json(
                        "ARoG_0720_naive_1_with_name_{}_{}_{}_{}_{}_{}.jsonl".format(args.dataset, str(args.question_abs),
                                                                                str(args.entity_abs),"depth_"+str(args.depth),"width_"+str(args.width),
                                                                                i),
                        "ARoG_0720_naive_1_with_name_{}_{}_{}_{}_{}_{}.json".format(args.dataset, str(args.question_abs),
                                                                               str(args.entity_abs),"depth_"+str(args.depth),"width_"+str(args.width),
                                                                               i))
            except Exception as e:
                print("Exception occured!", e)
                continue

            filename = "ARoG_0720_naive_1_{}_{}_{}_{}_{}_{}.json".format(args.dataset, str(args.question_abs),
                                                                    str(args.entity_abs),"depth_"+str(args.depth),"width_"+str(args.width),
                                                                    i)
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    combined_list.extend(data)
            except FileNotFoundError:
                continue
        with open(
                "ARoG_0720_naive_1_{}_{}_{}_{}_{}_{}.json".format(args.dataset, str(args.question_abs),
                                                             str(args.entity_abs),"depth_"+str(args.depth),"width_"+str(args.width),
                                                             "total"), 'w', encoding='utf-8') as outfile:
            json.dump(combined_list, outfile, ensure_ascii=False, indent=4)
        if args.reason_with_name:
            combined_list_with_name = []
            for i in range(args.max_worker):
                filename = "ARoG_0720_naive_1_with_name_{}_{}_{}_{}_{}_{}.json".format(args.dataset,
                                                                                  str(args.question_abs),
                                                                                  str(args.entity_abs),"depth_"+str(args.depth),"width_"+str(args.width),
                                                                                  i)
                try:
                    with open(filename, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        combined_list_with_name.extend(data)
                except FileNotFoundError:
                    continue

            with open("ARoG_0720_naive_1_with_name_{}_{}_{}_{}_{}_{}.json".format(args.dataset, str(args.question_abs),
                                                                             str(args.entity_abs),"depth_"+str(args.depth),"width_"+str(args.width),
                                                                             "total"), 'w',
                      encoding='utf-8') as outfile:
                json.dump(combined_list_with_name, outfile, ensure_ascii=False, indent=4)
