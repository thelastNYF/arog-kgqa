from collections import Counter

import openai
import time
import json
import httpx
from httpx_socks import SyncProxyTransport
transport = SyncProxyTransport.from_url("socks5://127.0.0.1:7891")
http_client = httpx.Client(transport=transport)

def run_llm(prompt, temperature, max_tokens, opeani_api_keys, engine="gpt-3.5-turbo"):
    # if "llama" not in engine.lower():
    #     openai.api_key = "EMPTY"
    #     openai.api_base = "http://localhost:8000/v1"  # your local llama server port
    #     engine = openai.Model.list()["data"][0]["id"]
    # else:
    #     openai.api_key = opeani_api_keys

    messages = [{"role":"system","content":"You are an AI assistant that helps people find information."}]
    message_prompt = {"role":"user","content":prompt}
    messages.append(message_prompt)
    print("start openai")
    client = openai.OpenAI(api_key=opeani_api_keys,http_client=http_client)
    f=0
    while(f == 0):
        try:
            response = client.chat.completions.create(
                    model=engine,
                    messages = [{"role":"user","content":prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    frequency_penalty=0,
                    presence_penalty=0)
            # result = response["choices"][0]['message']['content']
            result = response.choices[0].message.content
            f = 1
        except Exception as e:
            print(e)
            print("openai error, retry")
            time.sleep(2)
    print("end openai")
    return result

def prepare_dataset(dataset_name):
    if dataset_name == 'cwq':
        with open('../data/cwq_1000.json',encoding='utf-8') as f:
        # with open('../data/cwq.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'webqsp':
        with open('../data/WebQSP.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'RawQuestion'
    elif dataset_name == 'grailqa':
        with open('../data/grailqa.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'simpleqa':
        with open('../data/SimpleQA.json',encoding='utf-8') as f:
            datas = json.load(f)    
        question_string = 'question'
    elif dataset_name == 'qald':
        with open('../data/qald_10-en.json',encoding='utf-8') as f:
            datas = json.load(f) 
        question_string = 'question'   
    elif dataset_name == 'webquestions':
        with open('../data/WebQuestions.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'trex':
        with open('../data/T-REX.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'input'    
    elif dataset_name == 'zeroshotre':
        with open('../data/Zero_Shot_RE.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'input'    
    elif dataset_name == 'creak':
        with open('../data/creak.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'sentence'
    else:
        print("dataset not found")
        exit(-1)
    return datas, question_string

def check_string(string):
    return "{" in string

def clean_results(string):
    string = string.replace("{Yes}", "").replace("{No}", "")
    if "{" in string:
        start = string.find("{") + 1
        end = string.find("}")
        content = string[start:end]
        return content
    else:
        return string

def most_common_element(lst):
    count = Counter(lst)
    most_common = count.most_common(1)
    return most_common[0][0]

def split_array_into_10(lst):
    length = len(lst)
    part_size = length // 10
    remainder = length % 10
    result = []
    start = 0
    for i in range(10):
        end = start + part_size + (1 if i < remainder else 0)
        result.append(lst[start:end])
        start = end
    return result
