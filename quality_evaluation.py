from tqdm import tqdm

from reader import read_events_raw, event_to_tips
from constants import INPUT_FILE_NAME, TIPS_GROUP, ACTION_INVOKED_GROUP, PREDICTED_TIME_MILLIS

# INPUT_FILE_NAME = "./log_sample_with_answers_full.csv"


def evaluate(events, device_cnt):
    all_tips = 0  # do dictionary when algorithm name added to logs
    useful_tips = 0
    device_to_tips = {}
    tip_types = {}
    for event in tqdm(events):
        device_id, group_id, event_id, timestamp, count, bucket = event
        if group_id == TIPS_GROUP:
            if device_id not in device_to_tips:
                device_to_tips[device_id] = []
            device_to_tips[device_id].append((event_id, timestamp))
            all_tips += 1
            tip_types[event_id] = True

    good_devices = {}
    good_tips = {}
    for event in tqdm(events):
        device_id, group_id, event_id, timestamp, count, bucket = event
        if group_id == ACTION_INVOKED_GROUP:
            if device_id in device_to_tips.keys():
                possible_tips = event_to_tips((group_id, event_id))
                showed_tips = device_to_tips[device_id]
                for elem in showed_tips:
                    tip, tip_timestamp = elem
                    if tip in possible_tips and timestamp > tip_timestamp \
                            and (timestamp - tip_timestamp) < PREDICTED_TIME_MILLIS:
                        useful_tips += 1
                        good_devices[device_id] = True
                        good_tips[tip] = True

    accuracy = useful_tips / all_tips
    users_accuracy = len(list(good_devices.keys())) * 1. / device_cnt
    tips_accuracy = len(list(good_tips.keys())) * 1. / len(list(tip_types.keys()))
    return accuracy, users_accuracy, tips_accuracy


if __name__ == "__main__":
    events, event_types, devices = read_events_raw(INPUT_FILE_NAME)
    accuracy, users_accuracy, tips_accuracy = evaluate(events, len(devices))
    print(f"Accuracy is: {accuracy}")
    print(f"Percent of users who followed the tips is: {users_accuracy}")
    print(f"Percent of tips that were used al least once: {tips_accuracy}")
