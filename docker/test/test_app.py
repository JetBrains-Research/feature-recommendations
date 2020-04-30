from tqdm import tqdm
import os
import json
import requests

from constants import Method, METHODS_CNT
from metrics import compute_map_k, compute_ndcg_k, compute_accuracy_first, compute_mrr_k

TEST_EVENTS_DIR = "./test_events"
TEST_LABELS_DIR = "./test_labels"
FILE_NAMES = os.listdir(TEST_EVENTS_DIR)


def _read_user_events(file):
    with open("./test_events/" + file, 'r') as fin:
        data = json.load(fin)
        return data


URL = "http://3.126.201.114/tips/v1"


def _is_intersection(list1, list2):
    return len(set(list1).intersection(list2)) > 0


def _build_recommendations():
    user_to_recommendation = {}
    bucket = 0

    for i in range(METHODS_CNT):
        user_to_recommendation[i] = {}

    for file_name in tqdm(FILE_NAMES):
        if not (file_name[-5:] == '.json'):
            continue

        if not os.path.isfile(TEST_LABELS_DIR + "_positive/" + file_name[:-5] + ".csv"):
            continue

        json_events = _read_user_events(file_name)
        for i in range(METHODS_CNT):
            json_events["bucket"] = i
            r = requests.post(URL, json=json_events)
            user_to_recommendation[i][file_name[:-5]] = json.loads(str(r.text))['showingOrder']

    return user_to_recommendation


def _build_shown_tips():
    user_to_done = {}
    user_to_not_done = {}

    for file_name in tqdm(FILE_NAMES):
        if not (file_name[-5:] == '.json'):
            continue

        if os.path.isfile(TEST_LABELS_DIR + "_positive/" + file_name[:-5] + ".csv"):
            user_to_done[file_name[:-5]] = []
            for row in open(TEST_LABELS_DIR + "_positive/" + file_name[:-5] + ".csv", 'r'):
                tip = row[:-1]
                user_to_done[file_name[:-5]].append(tip)
        else:
            pass
            if os.path.isfile(TEST_LABELS_DIR + "_negative/" + file_name[:-5] + ".csv"):
                user_to_not_done[file_name[:-5]] = []
                for row in open(TEST_LABELS_DIR + "_negative/" + file_name[:-5] + ".csv", 'r'):
                    tip = row[:-1]
                    user_to_not_done[file_name[:-5]].append(tip)
            else:
                print('Unknown user: ' + file_name[:-5])

    return user_to_done, user_to_not_done


def _evaluate_recommendations(user_to_done, user_to_recommendation):
    map_5 = {}
    map_10 = {}
    ndcg_5 = {}
    ndcg_10 = {}
    mrr_5 = {}
    mrr_10 = {}
    accuracy = {}

    for i in range(METHODS_CNT):
        map_5[Method(i).name] = compute_map_k(user_to_done, user_to_recommendation[i], 5)
        map_10[Method(i).name] = compute_map_k(user_to_done, user_to_recommendation[i], 10)
        ndcg_5[Method(i).name] = compute_ndcg_k(user_to_done, user_to_recommendation[i], 5)
        ndcg_10[Method(i).name] = compute_ndcg_k(user_to_done, user_to_recommendation[i], 10)
        mrr_5[Method(i).name] = compute_mrr_k(user_to_done, user_to_recommendation[i], 5)
        mrr_10[Method(i).name] = compute_mrr_k(user_to_done, user_to_recommendation[i], 10)
        accuracy[Method(i).name] = compute_accuracy_first(user_to_done, user_to_recommendation[i])

    return map_5, map_10, ndcg_5, ndcg_10, mrr_5, mrr_10, accuracy


def run_test():
    user_to_recommendation = _build_recommendations()
    user_to_done, user_to_not_done = _build_shown_tips()

    map_5, map_10, ndcg_5, ndcg_10, mrr_5, mrr_10, accuracy =\
        _evaluate_recommendations(user_to_done, user_to_recommendation)

    #map_5_not_done, map_10_not_done, ndcg_5_not_done, ndcg_10_not_done, mrr_5_not_done, mrr_10_not_done, accuracy_not_done = \
    #    _evaluate_recommendations(user_to_not_done, user_to_recommendation)

    for i in range(METHODS_CNT):
        print(f"{Method(i).name}: map@5 = {map_5[Method(i).name]}")
        print(f"{Method(i).name}: map@10 = {map_10[Method(i).name]}")
        print(f"{Method(i).name}: nDCG@5 = {ndcg_5[Method(i).name]}")
        print(f"{Method(i).name}: nDCG@10 = {ndcg_10[Method(i).name]}")
        print(f"{Method(i).name}: MRR@5 = {mrr_5[Method(i).name]}")
        print(f"{Method(i).name}: MRR@10 = {mrr_10[Method(i).name]}")
        print(f"{Method(i).name}: accuracy of first = {accuracy[Method(i).name]}")

   # for i in range(METHODS_CNT):
   #     print(f"{Method(i).name}: map@5 not done = {map_5_not_done[Method(i).name]}")
   #     print(f"{Method(i).name}: map@10 not done = {map_10_not_done[Method(i).name]}")
   #     print(f"{Method(i).name}: nDCG@5 not done = {ndcg_5_not_done[Method(i).name]}")
   #     print(f"{Method(i).name}: nDCG@10 not done = {ndcg_10_not_done[Method(i).name]}")
   #     print(f"{Method(i).name}: MRR@5 not done = {mrr_5_not_done[Method(i).name]}")
   #     print(f"{Method(i).name}: MRR@10 not done = {mrr_10_not_done[Method(i).name]}")
   #     print(f"{Method(i).name}: accuracy of first not done = {accuracy_not_done[Method(i).name]}")

    #for file_name in tqdm(FILE_NAMES):
    #    device_id = file_name[:-5]
    #    print(device_id)
    #    print(user_to_done[device_id])
    #    for i in range(METHODS_CNT):
    #        recommended_tips = user_to_recommendation[device_id][i]["showingOrder"]
    #        print(f"{Method(i).name}: {recommended_tips[:5]}")


if __name__ == '__main__':
    run_test()
