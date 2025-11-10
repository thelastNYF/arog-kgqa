import argparse
from utils import *

# 


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str,
                        default="cwq_alias", help="choose the dataset.")
    parser.add_argument("--output_file", type=str,
                        default="ARoG_0710_naive_1_webqsp_True_True_depth_3_width_3_total.json",
                        help="73.9, 60.4, 10781.871165644172")
    parser.add_argument("--constraints_refuse", type=bool,
                        default=True, help="LLM may have refuse error, enable this option to skip current sample.")
    args = parser.parse_args()

    ground_truth_datas, question_string, output_datas = prepare_dataset_for_eval(args.dataset, args.output_file)

    num_right = 0
    num_error = 0
    num_data = 0
    num_no_clues = 0
    output_datas.reverse()
    new_output_datas = [output_datas[0]]
    data_list = [output_datas[0]["question"]]
    # 
    for data in output_datas[1:]:
        if data["question"] not in data_list:
            new_output_datas.append(data)
        data_list.append(data["question"])
    print(len(data_list))
    data_list = list(set(data_list))
    print(len(data_list))
    print(len(new_output_datas))
    question_list = []
    print(new_output_datas[-1][question_string])
    if args.dataset == "grailqa":
        with open('../../CoT/cot_grailqa_right.json', 'r') as f:
            cot_question_list = json.load(f)
    elif args.dataset == "webqsp":
        with open('../../CoT/cot_webqsp_right.json', 'r') as f:
            cot_question_list = json.load(f)
    elif args.dataset == "cwq_alias":
        with open('../../CoT/cot_cwq_alias_right.json', 'r') as f:
            cot_question_list = json.load(f)
    # cot_question_list=[]
    for data in new_output_datas:
        if data["question"] not in cot_question_list:
            continue
        try:
            origin_data = [j for j in ground_truth_datas if j['question'] == data["question"]][0]
        except:
            origin_data = [j for j in ground_truth_datas if j['RawQuestion'] == data[question_string]][0]
        # if origin_data[compositionality_type]!="composition":
        #     continue
        answers = align(args.dataset, question_string, data, ground_truth_datas)
        # answers_ids = align_ids(args.dataset, question_string, data, ground_truth_datas)
        answers_ids = answers
        # print(answers)
        retrieve_results = str(data['reasoning_chains_str'])
        response = retrieve_results
        if args.constraints_refuse and check_string(response):
            continue
        if exact_match(response, answers_ids):
            retrieve_flag = True
        else:
            retrieve_flag = False
        # if retrieve_flag:
        if True:
            try:
                results = data['results']
            except:
                # results = data['io_0702_result']
                # results = data['cot_0702_result']
                results = data['sc_0702_result']
            if check_string(results):
                response = clean_results(results)
                if response == "NULL":
                    # response = response
                    response = results
                else:
                    if exact_match(response, answers):
                        print(data[question_string])
                        num_right += 1
                    else:
                        num_error += 1
            else:
                # response = "NULL"
                response = results
                if args.constraints_refuse and check_string(response):
                    continue
                if exact_match(response, answers):
                    num_right += 1
                    print(data[question_string])
                else:

                    num_error += 1
        else:
            num_no_clues += 1
            question_list.append(data[question_string])

    print("right: {}, error: {}, pass: {}".format(num_right, num_error, num_no_clues))
    print(100 * (num_right + num_error) / (num_right + num_error+num_no_clues), 100 * num_right / (num_right + num_error),
          100 * num_right /  (num_right + num_error+num_no_clues))
    print(100 * (num_right + num_error) / (len(ground_truth_datas)), 100 * num_right / (num_right + num_error),
          100 * num_right / (len(ground_truth_datas)))
    print(100 * (num_right + num_error) / (len(ground_truth_datas) - len(cot_question_list)),
          100 * num_right / (num_right + num_error),
          100 * num_right / (len(ground_truth_datas) - len(cot_question_list)))

    save_result2json(args.dataset, num_right, num_error, len(output_datas), method=None)
