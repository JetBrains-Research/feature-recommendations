import json
from tqdm import tqdm

import reader
from constants import PREDICTED_TIME_MILLIS, TIPS_GROUP, ACTION_INVOKED_GROUP
from reader import event_to_tips, ide_to_tips
from util import _is_intersection

INPUT_FILE_NAME_TEST = '../resources/' + 'new_feb_'


def generate_json(events, file_name, file_id):
    device_to_done_actions = {}
    device_to_tips = {}
    tips_done = {}
    tip_id_cur = 0
    ide_tips = ide_to_tips(file_name)
    print(ide_tips.keys())

    data = {"tips": [], "usageInfo": {}, "ideName": ""}
    for event in events:
        if event.group_id == TIPS_GROUP:
            if event.device_id in device_to_done_actions.keys():
                if event.device_id not in device_to_tips.keys():
                    device_to_tips[event.device_id] = []
                device_to_tips[event.device_id].append((event.event_id, event.timestamp, str(tip_id_cur)))

                data["usageInfo"] = {}
                data["bucket"] = event.bucket
                with open("./test_events/" + event.device_id + "_"
                          + str(tip_id_cur) + "_" + str(file_id) + ".json", 'w') as fout:

                    data["tips"] = []
                    for t in ide_tips[event.ide].keys():
                        data["tips"].append(t)
                    data['ideName'] = event.ide

                    for (group_id, event_id, ide) in device_to_done_actions[event.device_id]:
                        max_timestamp, count = device_to_done_actions[event.device_id][(group_id, event_id, ide)]
                        if ide == event.ide:
                            data["usageInfo"][event_id] = {}
                            data["usageInfo"][event_id]["usageCount"] = count
                            data["usageInfo"][event_id]["lastUsedTimestamp"] = max_timestamp

                    json.dump(data, fout)

                tip_id_cur += 1

        else:
            if event.group_id == ACTION_INVOKED_GROUP:
                if event.device_id not in device_to_done_actions.keys():
                    device_to_done_actions[event.device_id] = {}
                if (event.group_id, event.event_id) not in device_to_done_actions[event.device_id].keys():
                    device_to_done_actions[event.device_id][(event.group_id, event.event_id, event.ide)] = \
                        (event.timestamp, event.count)
                else:
                    _, cnt = device_to_done_actions[event.device_id][(event.group_id, event.event_id, event.ide)]
                    device_to_done_actions[event.device_id][(event.group_id, event.event_id, event.ide)] = \
                        (event.timestamp, cnt + event.count)

                if event.device_id in device_to_tips.keys():
                    for (tip, tip_timestamp, tip_id) in device_to_tips[event.device_id]:
                        if _is_intersection(event_to_tips(event.group_id, event.event_id), [tip]):
                            if event.timestamp - tip_timestamp < PREDICTED_TIME_MILLIS:
                                with open("./test_labels_positive/" + event.device_id + "_"
                                          + tip_id + "_" + str(file_id) + ".csv", 'w') as fout:
                                    fout.write(tip + "\n")
                                tips_done[tip_id] = True

    for device_id in device_to_tips.keys():
        for (tip, timestamp, tip_id) in device_to_tips[device_id]:
            if tip_id not in tips_done.keys():
                with open("./test_labels_negative/" + device_id + "_"
                          + tip_id + "_" + str(file_id) + ".csv", 'w') as fout:
                    fout.write(tip + "\n")


def generate_test_files(file_name, file_id):
    events, events_types, devices = reader.read_events_raw(file_name)

    events.sort(key=lambda x: x.timestamp)

    generate_json(events, file_name, file_id)


if __name__ == '__main__':
    for i in range(1, 11):
        print(i)
        generate_test_files(INPUT_FILE_NAME_TEST + str(i) + ".csv", str(i))
