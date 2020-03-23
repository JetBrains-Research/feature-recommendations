import numpy as np
from tqdm import tqdm
import json
import shutil
import os

import reader
from constants import INPUT_FILE_NAME, PREDICTED_TIME_MILLIS, TRAIN_TIME_MILLIS


def _generate_json(events_types, test_events, test_labels, device_id_to_bucket):
    if os.path.isdir('./test_events'):
        shutil.rmtree('./test_events')
    if os.path.isdir('./test_labels'):
        shutil.rmtree('./test_labels')
    os.mkdir("./test_events")
    os.mkdir("./test_labels")

    data = {"tips": []}
    for elem in events_types:
        tip = reader.event_to_tips(elem)
        for t in tip:
            data["tips"].append(t)
    data["usageInfo"] = {}
    data["ideName"] = ""
    for device_id in test_events.keys():
        if (len(list(test_events[device_id]))) > 0:
            data["usageInfo"] = {}
            data["bucket"] = device_id_to_bucket[device_id]

            with open("./test_events/" + device_id + ".json", 'w') as fout:
                for event_type in events_types:
                    if event_type in test_events[device_id].keys():
                        max_timestamp, count = test_events[device_id][event_type]

                        action_id = event_type[1]
                        data["usageInfo"][action_id] = {}
                        data["usageInfo"][action_id]["usageCount"] = count
                        data["usageInfo"][action_id]["lastUsedTimestamp"] = max_timestamp

                json.dump(data, fout)

            with open("./test_labels/" + device_id + ".csv", 'w') as fout:
                for (group_id, event_id) in test_labels[device_id]:
                    fout.write(str(group_id) + "," + str(event_id) + "\n")


def _generate_test_events_labels(events, test_devices):
    test_events = {}
    test_labels = {}

    device_to_min_timestamp = reader.get_device_to_min_timestamp(events)
    device_to_max_timestamp = reader.get_device_to_max_timestamp(events)

    for event in tqdm(events):
        device_id, group_id, event_id, timestamp, count, _ = event

        if device_id not in test_devices:
            continue

        min_timestamp = device_to_min_timestamp[device_id]
        max_timestamp = device_to_max_timestamp[device_id]

        if (max_timestamp - min_timestamp) < PREDICTED_TIME_MILLIS:
            continue

        if device_id not in test_events.keys():
            test_events[device_id] = {}
        if device_id not in test_labels.keys():
            test_labels[device_id] = {}

        threshold = max_timestamp - PREDICTED_TIME_MILLIS

        if timestamp <= threshold:
            if timestamp >= threshold - TRAIN_TIME_MILLIS:
                if (group_id, event_id) in test_events[device_id].keys():
                    _, prev_count = test_events[device_id][(group_id, event_id)]
                    test_events[device_id][(group_id, event_id)] = (max_timestamp, prev_count + count)
                else:
                    test_events[device_id][(group_id, event_id)] = (max_timestamp, count)
        else:
            test_labels[device_id][(group_id, event_id)] = True
    return test_events, test_labels


def _generate_device_id_to_bucket(events):
    device_id_to_bucket = {}
    for event in tqdm(events):
        device_id, _, _, _, _, bucket = event
        device_id_to_bucket[device_id] = bucket
    return device_id_to_bucket


def read_events_from_file(file_name):
    events, events_types, devices = reader.read_events_raw(file_name)

    test_devices = np.random.choice(devices, int(len(devices) / 3), replace=False)
    test_events, test_labels = _generate_test_events_labels(events, test_devices)

    device_id_to_bucket = _generate_device_id_to_bucket(events)

    _generate_json(events_types, test_events, test_labels, device_id_to_bucket)


if __name__ == '__main__':
    read_events_from_file(INPUT_FILE_NAME)





