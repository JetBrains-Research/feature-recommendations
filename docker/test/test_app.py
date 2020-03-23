from tqdm import tqdm
import os
import json
import requests

from constants import ACTION_INVOKED_GROUP, Method, METHODS_CNT
from reader import event_to_tips


TEST_EVENTS_DIR = "./test_events"
TEST_LABELS_DIR = "./test_labels"
FILE_NAMES = os.listdir(TEST_EVENTS_DIR)


def _read_user_events(file):
    with open("./test_events/" + file, 'r') as fin:
        data = json.load(fin)
        return data


URL = "http://0.0.0.0:5000/tips/v1"


def _is_intersection(list1, list2):
    return len(set(list1).intersection(list2)) > 0


def _build_recommendations():
    user_to_recommendation = {}

    for file_name in tqdm(FILE_NAMES):
        if not (file_name[-5:] == '.json'):
            continue

        json_events = _read_user_events(file_name)
        r = requests.post(URL, json=json_events)

        user_to_recommendation[file_name[:-5]] = json.loads(str(r.text))

    return user_to_recommendation


def _build_done_tips():
    user_to_done = {}

    for file_name in tqdm(FILE_NAMES):
        if not (file_name[-5:] == '.json'):
            continue

        user_to_done[file_name[:-5]] = []

        for row in open(TEST_LABELS_DIR + "/" + file_name[:-5] + ".csv", 'r'):
            event = row[:-1].split(",")
            if event[0] == ACTION_INVOKED_GROUP:
                tips = event_to_tips(event)
                for tip in tips:
                    user_to_done[file_name[:-5]].append(tip)

    return user_to_done


def _evaluate_recommendations(user_to_done, user_to_recommendation):
    all_recommendations = {}
    true_recommendations = {}

    for i in range(METHODS_CNT):
        all_recommendations[Method(i).name] = 0
        true_recommendations[Method(i).name] = 0

    for file_name in tqdm(FILE_NAMES):
        device_id = file_name[:-5]

        done_tips = user_to_done[device_id]
        recommended_tips = user_to_recommendation[device_id]["showingOrder"]

        algorithm = user_to_recommendation[device_id]["usedAlgorithm"]
        all_recommendations[algorithm] += 1

        if _is_intersection(done_tips, recommended_tips):
            true_recommendations[algorithm] += 1

    recommendation_accuracy = {}
    for device_id in all_recommendations.keys():
        recommendation_accuracy[device_id] = true_recommendations[device_id] / all_recommendations[device_id]

    return recommendation_accuracy


def run_test():
    user_to_recommendation = _build_recommendations()
    user_to_done = _build_done_tips()
    recommendation_accuracy = _evaluate_recommendations(user_to_done, user_to_recommendation)

    for i in range(METHODS_CNT):
        print(f"{Method(i).name}: {recommendation_accuracy[Method(i).name]}")


if __name__ == '__main__':
    run_test()
