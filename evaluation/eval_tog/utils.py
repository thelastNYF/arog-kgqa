import json
import random
import re
from typing import List

from SPARQLWrapper import JSON, SPARQLWrapper

SPARQLPATH = "http://{{SentenceTransformer Server}}:8890/sparql"  # depend on your own internal address and port, shown in Freebase folder's readme.md
sparql_id_english = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?tailEntity\nWHERE {\n  FILTER (!isLiteral(?tailEntity) OR lang(?tailEntity) = '' OR langMatches(lang(?tailEntity), 'en')) {\n    ?entity ns:type.object.name ?tailEntity .\n    FILTER(?entity = ns:%s)\n  }\n}"""


def prepare_dataset_for_eval(dataset_name, output_file):
    if dataset_name == 'cwq':
        with open('../../data/cwq_1000.json', encoding='utf-8') as f:
            # with open('../data/cwq.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'cwq_alias':
        with open('../../data/cwq_1000_alias.json', encoding='utf-8') as f:
            # with open('../data/cwq.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'webqsp':
        with open('../../data/WebQSP.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
        # question_string = 'RawQuestion'
    elif dataset_name == 'grailqa':
        with open('../../data/grailqa.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'simpleqa':
        with open('../data/SimpleQA.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'qald':
        with open('../data/qald_10-en.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'webquestions':
        with open('../data/WebQuestions.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'trex':
        with open('../data/T-REX.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'input'
    elif dataset_name == 'zeroshotre':
        with open('../data/Zero_Shot_RE.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'input'
    elif dataset_name == 'creak':
        with open('../data/creak.json', encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'sentence'
    else:
        print(
            "dataset not found, you should pick from {cwq, webqsp, grailqa, simpleqa, qald, webquestions, trex, zeroshotre, creak}.")
        exit(-1)
    with open(output_file, encoding='utf-8') as f:
        output_datas = json.load(f)
    return datas, question_string, output_datas


def align(dataset_name, question_string, data, ground_truth_datas):
    if dataset_name == 'cwq':
        answer_list = []
        origin_data = [j for j in ground_truth_datas if j[question_string] == data[question_string]][0]
        if 'answers' in origin_data:
            answers = origin_data["answers"]
        else:
            answers = origin_data["answer"]
        answer_list.append(answers)
    elif dataset_name == 'cwq_alias':
        answer_list = []
        origin_data = [j for j in ground_truth_datas if j[question_string] == data[question_string]][0]
        answers = origin_data["answer_names"]
        answers_2 = origin_data["answer_ids"]
        answer_list.extend(answers)
        answer_list.extend(answers_2)
    elif dataset_name == 'webqsp':
        answer_list = []
        try:
            origin_data = [j for j in ground_truth_datas if j['RawQuestion'] == data[question_string]][0]
        except IndexError:
            origin_data = [j for j in ground_truth_datas if j['ProcessedQuestion'] == data[question_string]][0]
        answers = origin_data["Parses"]
        for answer in answers:
            for name in answer['Answers']:
                if name['EntityName'] == None:
                    answer_list.append(name['AnswerArgument'])
                else:
                    answer_list.append(name['EntityName'])
                    answer_list.append(name['AnswerArgument'])
    elif dataset_name == 'grailqa':
        answer_list = []
        origin_data = [j for j in ground_truth_datas if j[question_string] == data[question_string]][0]
        answers = origin_data["answer"]
        for answer in answers:
            if "entity_name" in answer:
                answer_list.append(answer['entity_name'])
                answer_list.append(answer['answer_argument'])
            else:
                answer_list.append(answer['answer_argument'])
    #
    # elif dataset_name == 'simpleqa':
    #     answers = origin_data["answer"]
    #     answer_list.append(answers)
    #
    # elif dataset_name == 'qald':
    #     answers = origin_data["answer"]
    #     for answer in answers:
    #         answer_list.append(answers[answer])
    #
    # elif dataset_name == 'webquestions':
    #     answer_list = origin_data["answers"]
    #
    # elif dataset_name == 'trex' or dataset_name == 'zeroshotre':
    #     answers = origin_data["answer"]
    #     answer_list.append(answers)
    #
    # elif dataset_name == 'creak':
    #     answer = origin_data['label']
    #     answer_list.append(answer)

    return list(set(answer_list))


# 
def align_ids(dataset_name, question_string, data, ground_truth_datas):
    if dataset_name == 'cwq':
        answer_list = []
        origin_data = [j for j in ground_truth_datas if j[question_string] == data[question_string]][0]
        if 'answers' in origin_data:
            answers = origin_data["answers"]
        else:
            answers = origin_data["answer"]
        answer_list.append(answers)
    elif dataset_name == 'cwq_alias':
        answer_list = []
        origin_data = [j for j in ground_truth_datas if j[question_string] == data[question_string]][0]
        if 'answer_names' in origin_data:
            answers = origin_data["answer_names"]
        answer_list.extend(answers)
    elif dataset_name == 'webqsp':
        answer_list = []
        try:
            origin_data = [j for j in ground_truth_datas if j['RawQuestion'] == data[question_string]][0]
        except IndexError:
            origin_data = [j for j in ground_truth_datas if j['ProcessedQuestion'] == data[question_string]][0]

        # origin_data = [j for j in ground_truth_datas if j[question_string] == data[question_string]][0]
        # 
        answers = origin_data["Parses"]
        for answer in answers:
            for name in answer['Answers']:
                if name['EntityName'] == None:
                    print("None: %s" % data[question_string])
                    answer_list.append(name['AnswerArgument'])
                else:
                    # answer_list.append(name['EntityName'])
                    answer_list.append(name['AnswerArgument'])
    elif dataset_name == 'grailqa':
        answer_list = []
        origin_data = [j for j in ground_truth_datas if j[question_string] == data[question_string]][0]
        answers = origin_data["answer"]
        for answer in answers:
            if "entity_name" in answer:
                answer_list.append(answer['entity_name'])
                answer_list.append(answer['answer_argument'])
            else:
                answer_list.append(answer['answer_argument'])
    #
    # elif dataset_name == 'simpleqa':
    #     answers = origin_data["answer"]
    #     answer_list.append(answers)
    #
    # elif dataset_name == 'qald':
    #     answers = origin_data["answer"]
    #     for answer in answers:
    #         answer_list.append(answers[answer])
    #
    # elif dataset_name == 'webquestions':
    #     answer_list = origin_data["answers"]
    #
    # elif dataset_name == 'trex' or dataset_name == 'zeroshotre':
    #     answers = origin_data["answer"]
    #     answer_list.append(answers)
    #
    # elif dataset_name == 'creak':
    #     answer = origin_data['label']
    #     answer_list.append(answer)

    return list(set(answer_list))


def check_string(string):
    return "{" in string


def id2entity_name_or_type(value_entity_dict, raw_topic_entity, entity_id):
    if entity_id in value_entity_dict:
        return value_entity_dict[entity_id]
    if entity_id in raw_topic_entity:
        return raw_topic_entity[entity_id]
    # with open('../data/mid2name.json', encoding='utf-8') as f:
    #     mid2name_dict = json.load(f)
    #     if entity_id in mid2name_dict:
    #         return str(mid2name_dict[entity_id])
    sparql_query = sparql_id_english % (entity_id)
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


def clean_results_cot(string):

    string = string.lstrip(" {Yes}").lstrip(" {No}")
    string = string.split("\n\n")[0]
    string = string.replace("{Yes}", "").replace("{No}", "")
    if "{" in string:
        start = string.find("{") + 1
        end = string.find("}")
        content = string[start:end]
        if content == "Yes":
            print("yes")
        elif content == "No":
            print("no")
        return content
    else:

        return string


# 
def clean_results(string):
    string = string.replace("{Yes}", "").replace("{No}", "")
    if "{" in string:
        start = string.find("{") + 1
        end = string.find("}")
        content = string[start:end]
        return content
    else:
        return string


def check_refuse(string):
    refuse_words = ["however", "sorry"]
    return any(word in string.lower() for word in refuse_words)


def remove_content_within_all_parentheses(s):
    # 、
    pattern = r'[\[\(\{].*?[\]\)\}]'
    # 
    s = re.sub(pattern, '', s)
    return s


def cal_f1_score(pred_answers, correct_answers):
    hit_answers = set(pred_answers) & set(correct_answers)
    if not hit_answers:
        return 0
    # elif pred_answers[0] in correct_answers:
    #     return 1
    # else:
    #     return 0
    prec = len(hit_answers) / len(pred_answers)
    recall = len(hit_answers) / len(correct_answers)
    f1 = (2 * prec * recall) / (prec + recall)
    return f1


def FindInList(entry, elist):
    for item in elist:
        if entry == item:
            return True
    return False


def CalculatePRF1(goldAnswerList: List[str], predAnswerList: List[str]):
    if len(goldAnswerList) == 0:
        if len(predAnswerList) == 0:
            return [
                1.0,
                1.0,
                1.0,
                1.0,
            ]  # consider it 'correct' when there is no labeled answer, and also no predicted answer
        else:
            return [
                0.0,
                1.0,
                0.0,
                0.0,
            ]  # precision=0 and recall=1 when there is no labeled answer, but has some predicted answer(s)
    elif len(predAnswerList) == 0:
        return [
            1.0,
            0.0,
            0.0,
            0.0,
        ]  # precision=1 and recall=0 when there is labeled answer(s), but no predicted answer
    else:
        tp = 1e-40  # numerical trick
        fp = 0.0
        fn = 0.0
        # Calculate true positives (tp) and false negatives (fn) directly for each element in the predicted list and the golden list.
        for gentry in goldAnswerList:
            if FindInList(gentry, predAnswerList):  # Calculate how many are correct in the plist.
                tp += 1
            else:
                fn += 1
        for pentry in predAnswerList:
            if not FindInList(pentry, goldAnswerList):  # Calculate how many are wrong in the glist.
                fp += 1

        precision = tp / (tp + fp)
        recall = tp / (tp + fn)

        f1 = (2 * precision * recall) / (precision + recall)

        num_random = 100
        random_hit = 0
        for i in range(num_random):
            random_ans = random.choice(predAnswerList)
            if random_ans in goldAnswerList:
                random_hit += 1
        random_hit /= num_random
        return [precision, recall, f1, random_hit]



def exact_match(response, answers):
    response = re.sub(r'\(.*?\)', '', response).strip()
    clean_result = response.strip().replace(" ", "").lower()
    for answer in answers:
        clean_answer = answer.strip().replace(" ", "").lower()
        if clean_result == clean_answer or clean_result in clean_answer or clean_answer in clean_result:
            return True
    return False


def exact_match_gog(response, answers):
    clean_result = [response_item.strip().replace(" ", "").lower() for response_item in response]
    clean_result = ','.join(clean_result)
    for answer in answers:
        clean_answer = answer.strip().replace(" ", "").lower()
        # if clean_answer in clean_result:
        if clean_result == clean_answer or clean_result in clean_answer or clean_answer in clean_result:
            return True
    return False


def save_result2json(dataset_name, num_right, num_error, total_nums, method):
    results_data = {
        'dataset': dataset_name,
        'method': method,
        'Exact Match': float(num_right / total_nums),
        'Right Samples': num_right,
        'Error Sampels': num_error
    }
    with open('ToG_{}_results.json'.format(dataset_name), 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=4)


def extract_content(s):
    matches = re.findall(r'\{(.*?)\}', s)
    if len(matches) >= 2 and matches[0].lower() == 'yes':
        return matches[1]
    elif len(matches) >= 1:
        return matches[0]
    else:
        return 'NULL'
