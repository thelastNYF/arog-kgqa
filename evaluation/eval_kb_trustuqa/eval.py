import argparse
import traceback

from utils import *




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str,
                        default="webqsp", help="choose the dataset.")

    parser.add_argument("--output_file", type=str,
                        default=r"TrustUQA/wqsp/all_result.json",
                        help="")

    parser.add_argument("--constraints_refuse", type=bool,
                        default=True, help="LLM may have refuse error, enable this option to skip current sample.")
    args = parser.parse_args()

    ground_truth_datas, question_string, output_datas = prepare_dataset_for_eval(args.dataset, args.output_file)

    num_right = 0
    num_error = 0
    num_data = 0
    num_no_clues = 0
    # output_datas.reverse()
    new_output_datas = [output_datas[0]]
    data_list = [output_datas[0][next(iter(output_datas[0]))]["question"]]
    for data in output_datas[1:]:
        if data[next(iter(data))]["question"] not in data_list:
            new_output_datas.append(data)
        data_list.append(data[next(iter(data))]["question"])
    print(len(data_list))
    data_list = list(set(data_list))
    print(len(data_list))
    print(len(new_output_datas))
    question_list = []
    print(new_output_datas[-1][next(iter(output_datas[-1]))][question_string])
    if args.dataset == "webqsp":
        with open('../../CoT/cot_webqsp_right.json', 'r') as f:
            cot_question_list = json.load(f)
    elif args.dataset == "cwq_alias" or args.dataset == "cwq":
        with open('../../CoT/cot_cwq_alias_right.json', 'r') as f:
            cot_question_list = json.load(f)
    if args.dataset == "grailqa":
        with open('../../CoT/cot_grailqa_right.json', 'r') as f:
            cot_question_list = json.load(f)
    cot_question_list=[]
    for data in new_output_datas:
        try:
            if args.dataset=="webqsp":
                origin_data = [j for j in ground_truth_datas if j['RawQuestion'] == data[next(iter(data))][question_string]][0]
            else:
                origin_data = [j for j in ground_truth_datas if j['question'] == data[question_string]][0]
        except:
            traceback.print_exc()
            print(data[question_string])
            continue
        if args.dataset == "webqsp":
            if origin_data["RawQuestion"] in cot_question_list:
                continue
        else:
            if origin_data["question"] in cot_question_list:
                continue
        answers = align(args.dataset, question_string, data, ground_truth_datas)
        # answers predicated by the methods
        results = data[next(iter(data))]['prediction']
        response=results
        if response is None:
            response = results
        else:
            # response = " ".join(results)
            response=str(results)
            if exact_match(response, answers):
                num_right += 1
            else:
                num_error += 1

    print("total_questions: ",len(ground_truth_datas))
    print("filter_questions: ",len(cot_question_list))
    print("right: {}, error: {}, pass: {}".format(num_right, num_error, num_no_clues))
    print(100*(num_right+num_error)/(num_right+num_error+num_no_clues),100*num_right/(num_right+num_error),100*num_right/(num_right+num_error+num_no_clues))
