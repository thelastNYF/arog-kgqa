import json

first_token={'total': 0, 'input': 0, 'output': 0,'time':0,'call_num':0}
second_token={'total': 0, 'input': 0, 'output': 0,'time':0,'call_num':0}
with open("ropkg/ToG_on_private_kg/ToG_0708_cwq.json") as f:
    questions_answers_list = json.load(f)
    length=len(questions_answers_list)
    for item in questions_answers_list[:length]:
        second_token['total'] += item['token_num']['total']
        second_token['input'] += item['token_num']['input']
        second_token['output'] += item['token_num']['output']
        second_token['time'] += item['time']
        second_token['call_num'] += item['call_num']

    second_token['total'] =  second_token['total']/ length
    second_token['input'] = second_token['input']/ length
    second_token['output'] = second_token['output']/ length
    second_token['time'] = second_token['time']/length
    second_token['call_num'] = second_token['call_num']/ length
    print(second_token)
    print(len(questions_answers_list))