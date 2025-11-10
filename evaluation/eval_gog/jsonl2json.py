import json


def jsonl_to_json(jsonl_file, json_file):
    with open(jsonl_file, 'r') as infile:
        with open(json_file, 'w') as outfile:
            json_lines = infile.readlines()
            json_list = [json.loads(line) for line in json_lines]
            json.dump(json_list, outfile, indent=4)


with open("") as f:
    data = json.load(f)
    questions = []
    for item in data:
        questions.append(item['question'])

    print(len(questions))
    print(len(list(set(questions))))