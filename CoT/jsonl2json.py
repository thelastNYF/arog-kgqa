import json

def jsonl_to_json(dataset):
    total_json_list=[]
    json_file="/ropkg/CoT/sc_0713_total_{}.json".format(dataset)
    for index in range(10):
        jsonl_file="/ropkg/CoT/sc_0713_{}_{}.jsonl".format(index,dataset)
        with open(jsonl_file, 'r') as infile:
            json_lines = infile.readlines()
            json_list = [json.loads(line) for line in json_lines]
            total_json_list.extend(json_list)
    with open(json_file, 'w') as outfile:
        json.dump(total_json_list, outfile, indent=4)


jsonl_to_json("webqsp")
jsonl_to_json("grailqa")
