import operator
from tqdm import tqdm

from reader import read_events_raw, event_to_tips
from constants import INPUT_FILE_NAME, TIPS_GROUP, ACTION_INVOKED_GROUP, PREDICTED_TIME_MILLIS


def evaluate(events):
    all_tips = 0  # do dictionary when algorithm name added to logs
    useful_tips = 0
    device_to_tips = {}
    for event in tqdm(events):
        device_id, group_id, event_id, timestamp, count, bucket = event
        if group_id == TIPS_GROUP:
            if device_id not in device_to_tips:
                device_to_tips[device_id] = []
            device_to_tips[device_id].append((event_id, timestamp))
            all_tips += 1

    for event in tqdm(events):
        device_id, group_id, event_id, timestamp, count, bucket = event
        if group_id == ACTION_INVOKED_GROUP:
            if device_id in device_to_tips.keys():
                possible_tips = event_to_tips((group_id, event_id))
                showed_tips = device_to_tips[device_id]
                for elem in showed_tips:
                    tip, tip_timestamp = elem
                    if tip in possible_tips and timestamp > tip_timestamp and (timestamp - tip_timestamp) < PREDICTED_TIME_MILLIS:
                        useful_tips += 1

    return useful_tips / all_tips


if __name__ == "__main__":
    events, event_types, devices = read_events_raw(INPUT_FILE_NAME)
    accuracy = evaluate(events)
    print(f"Accuracy is: {accuracy}")
