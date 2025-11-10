import json
import argparse
from tqdm import tqdm
from utils import *
from prompt_list import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str,
                        default="cwq", help="choose the dataset.")
    parser.add_argument("--prompt_methods", type=str,
                        default="sc", help="cot or io.")
    parser.add_argument("--max_length", type=int,
                        default=256, help="the max length of LLMs output.")
    parser.add_argument("--temperature", type=int,
                        default=0, help="the temperature")
    parser.add_argument("--LLM_type", type=str,
                        default="gpt-4o-mini", help="base LLM model.")
    parser.add_argument("--opeani_api_keys", type=str,
                        default="your api key here",
                        help="if the LLM_type is gpt-3.5-turbo or gpt-4, you need add your own openai api keys.")
    args = parser.parse_args()

with open("sc_0713_0_{}.jsonl".format(args.dataset), 'a+', encoding="UTF-8") as out:
    datas, question_string = prepare_dataset(args.dataset)
    datas=split_array_into_10(datas)[0]
    for i in tqdm(datas, total=len(datas)):
        if args.prompt_methods == "sc":
            prompt = cot_prompt + "\n\nQ: " + i[question_string] + "\nA: "
            result_list = []
            for index in range(6):
                result_index = run_llm(prompt, args.temperature, args.max_length, args.opeani_api_keys, args.LLM_type)
                result_index = result_index.lower()
                if check_string(result_index):
                    response = clean_results(result_index)
                else:
                    response = result_index
                result_list.append(response)
            results = most_common_element(result_list)
            print(results)

        else:
            if args.prompt_methods == "cot":
                prompt = cot_prompt + "\n\nQ: " + i[question_string] + "\nA: "
            elif args.prompt_methods == "io":
                prompt = io_prompt + "\n\nQ: " + i[question_string] + "\nA: "
            results = run_llm(prompt, args.temperature, args.max_length, args.opeani_api_keys, args.LLM_type)
        print(results)
        out.write(
            json.dumps({"question": i[question_string], "{}_0702_result".format(args.prompt_methods): results}) + '\n')
