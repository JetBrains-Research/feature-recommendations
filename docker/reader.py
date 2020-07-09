import csv
from tqdm import tqdm
import json
import logging

from constants import *

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


def read_request_json(json_data):
    user_events = {}
    tips = []
    for tip in json_data["tips"]:
        tips.append(tip)
            
    for event in json_data["usageInfo"].keys():
        last_timestamp = json_data["usageInfo"][event]["lastUsedTimestamp"]
        count = json_data["usageInfo"][event]["usageCount"]
        user_events[(ACTION_INVOKED_GROUP, event)] = (last_timestamp, count)
    
    bucket = int(json_data["bucket"])

    return bucket, user_events, tips


class EventFull:
    def __init__(self, group_id, event_id, device_id, count, timestamp, bucket, ide):
        self.group_id = group_id
        self.event_id = event_id
        self.device_id = device_id
        self.count = count
        self.timestamp = timestamp
        self.bucket = bucket
        self.ide = ide


def read_tip_to_event(file_name):
    _tip_to_action_ids_dict = {}
    _action_id_to_tips_dict = {}
    with open(file_name, 'r') as fin:
        for html_to_event in tqdm(csv.reader(fin, delimiter=',')):
            tip = html_to_event[0]
            action_ids_string = html_to_event[1]
            action_ids = action_ids_string.split(" ")
            for action_id in action_ids:
                if tip in _tip_to_action_ids_dict.keys():
                    _tip_to_action_ids_dict[tip].append(action_id)
                else:
                    _tip_to_action_ids_dict[tip] = [action_id]

                if action_id in _action_id_to_tips_dict.keys():
                    _action_id_to_tips_dict[action_id].append(tip)
                else:
                    _action_id_to_tips_dict[action_id] = [tip]
    return _tip_to_action_ids_dict, _action_id_to_tips_dict


tip_to_action_ids_dict, action_id_to_tips_dict = read_tip_to_event(TIP_TO_EVENT_FILE_NAME)


def tip_to_event(tip):
    if tip in tip_to_action_ids_dict.keys():
        action_ids = tip_to_action_ids_dict[tip]
        return [(ACTION_INVOKED_GROUP, action_id) for action_id in action_ids]
    return []


def event_to_tips(group_id, event_id):
    if group_id != ACTION_INVOKED_GROUP:
        return []

    action_id = event_id
    if action_id in action_id_to_tips_dict.keys():
        return action_id_to_tips_dict[action_id]
    return []


def _check_group_event_id(event):
    return event.group_id not in ('performance', 'vcs.change.reminder') \
           and event.event_id not in ('ui.lagging',
                                'ide.error',
                                'ide.freeze',
                                'ui.latency',
                                'registered',
                                'invoked',
                                'TsLintLanguageService',
                                'whitelist.updated',
                                'logs.send',
                                'notification.shown',
                                'ESLintLanguageService')


product_name_to_ide_ = {
    "OC": "appcode",
    "CL": "clion",
    "DB": "datagrip",
    "GO": "go",
    "IU": "intellij-idea",
    "IC": "intellij-idea-community",
    "PS": "phpstorm",
    "PY": "pycharm",
    "PC": "pycharm-community",
    "PYA": "pycharm",
    "PCA": "pycharm-community",
    "RM": "rubymine",
    "WS": "webstorm"
}


def product_name_to_ide(pn):
    if pn in product_name_to_ide_.keys():
        return product_name_to_ide_[pn]
    return pn


def _extract_from_csv_row(event_data, is_eval):
    if is_eval:
        ide = product_name_to_ide(event_data[13])
        count = event_data[11].split('.')[0]
        group_id = event_data[4]
        event_id = event_data[9]

        timestamp = int(event_data[2])
        device_id = event_data[6]
        bucket = event_data[8]

    else:
        if len(event_data) < 20:
            return None
        ide = product_name_to_ide(event_data[19])
        count = event_data[12].split('.')[0]
        group_id = event_data[5]
        event_id = event_data[10]

        timestamp = int(event_data[3])
        device_id = event_data[7]
        bucket = event_data[9]

    if count:
        count = int(count)
    else:
        count = 0

    if group_id == "actions" and event_id == "action.invoked":
        if is_eval:
            event_info = json.loads(event_data[10])
        else:
            event_info = json.loads(event_data[11])
        group_id = ACTION_INVOKED_GROUP
        event_id = event_info["action_id"]

    if group_id == "ui.tips" and event_id == "tip.shown":
        if is_eval:
            event_info = json.loads(event_data[10])
        else:
            event_info = json.loads(event_data[11])
        group_id = TIPS_GROUP
        event_id = event_info["filename"] + ";"
        if "algorithm" in event_info.keys():
            event_id = event_id + event_info["algorithm"]

    event = EventFull(group_id=group_id, event_id=event_id, device_id=device_id,
                      count=count, timestamp=timestamp, bucket=bucket, ide=ide)

    return event


def read_events_raw(file_name, is_eval=False):
    events = []
    event_types = {}
    devices = {}
    ide_to_tips_ = ide_to_tips()
    with open(file_name, 'r') as fin:
        is_first = True
        for event_data in tqdm(csv.reader(fin, delimiter=',')):
            if is_first:
                is_first = False
                continue

            event = _extract_from_csv_row(event_data, is_eval)
            if (not event) or event.group_id != ACTION_INVOKED_GROUP and event.group_id != TIPS_GROUP and\
                    event.group_id != 'ui.tips'\
                    or event.ide not in ide_to_tips_.keys():
                continue

            if event.count and _check_group_event_id(event):
                event_types[(event.group_id, event.event_id)] = True
                devices[event.device_id] = True
                events.append(event)

    devices = list(devices.keys())
    event_types = list(event_types.keys())
    return events, event_types, devices


def get_device_to_max_timestamp(events):
    device_to_max_timestamp = {}

    for event in tqdm(events):

        if event.device_id not in device_to_max_timestamp.keys():
            device_to_max_timestamp[event.device_id] = event.timestamp
        else:
            device_to_max_timestamp[event.device_id] = max(device_to_max_timestamp[event.device_id], event.timestamp)

    return device_to_max_timestamp


def get_device_to_min_timestamp(events):
    device_to_min_timestamp = {}

    for event in tqdm(events):

        if event.device_id not in device_to_min_timestamp.keys():
            device_to_min_timestamp[event.device_id] = event.timestamp
        else:
            device_to_min_timestamp[event.device_id] = min(device_to_min_timestamp[event.device_id], event.timestamp)

    return device_to_min_timestamp


def _ignore_old_events(events):
    device_to_max_timestamp = get_device_to_max_timestamp(events)

    train_events = {}
    for event in tqdm(events):
        max_timestamp = device_to_max_timestamp[event.device_id]

        threshold = max_timestamp - TRAIN_TIME_MILLIS
        if event.timestamp >= threshold:
            if (event.device_id, event.group_id, event.event_id) in train_events.keys():
                times, prev_count = train_events[(event.device_id, event.group_id, event.event_id)]
                times.append(event.timestamp)
                train_events[(event.device_id, event.group_id, event.event_id)] = (times, prev_count + event.count)
            else:
                train_events[(event.device_id, event.group_id, event.event_id)] = ([event.timestamp], event.count)

    for event in tqdm(train_events.keys()):
        timestamps, cnt = train_events[event]
        train_events[event] = (sorted(timestamps), cnt)
    return train_events


def read_events_from_file():
    events, events_types, train_device_ids = read_events_raw(INPUT_FILE_NAME)
        
    logging.info(str(len(train_device_ids)) + " devices found.")
    logging.info(str(len(events_types)) + " event types found.")

    train_events = _ignore_old_events(events)

    logging.info(str(len(train_events.keys())) + " train events will be used.")

    return train_events, events_types, train_device_ids


def ide_to_tips():
    ide_to_tips = {}
    with open(IDE_TO_TIPS_FILE, 'r') as fin:
        for line in fin:
            tip = line.split(",")[0]
            ide = line.split(",")[1].replace("\n", '')
            if ide not in ide_to_tips.keys():
                ide_to_tips[ide] = {}
            ide_to_tips[ide][tip] = True
    return ide_to_tips


def _read_user_events(file):
    with open(TRAIN_EVENTS_DIR + "/" + file, 'r') as fin:
        data = json.load(fin)
        return data


def read_test_pairs():
    recommend_input_done = {}
    recommend_input_not_done = {}
    for file_name in tqdm(TRAIN_EVENTS_DIR_FILES):
        if not (file_name[-5:] == '.json'):
            continue

        content = _read_user_events(file_name)
        _, user_events, tips = read_request_json(content)

        if os.path.isfile(TRAIN_LABELS_POSITIVE_DIR + "/" + file_name[:-5] + ".csv"):
            recommend_input_done[file_name[:-5]] = (user_events, tips)

        if os.path.isfile(TRAIN_LABELS_NEGATIVE_DIR + "/" + file_name[:-5] + ".csv"):
            recommend_input_not_done[file_name[:-5]] = (user_events, tips)

    user_to_done_tips = {}
    user_to_not_done_tips = {}
    for file_name in tqdm(TRAIN_EVENTS_DIR_FILES):
        if not (file_name[-5:] == '.json'):
            continue

        if os.path.isfile(TRAIN_LABELS_POSITIVE_DIR + "/" + file_name[:-5] + ".csv"):
            user_to_done_tips[file_name[:-5]] = []
            for row in open(TRAIN_LABELS_POSITIVE_DIR + "/" + file_name[:-5] + ".csv", 'r'):
                tip = row[:-1]
                user_to_done_tips[file_name[:-5]].append(tip)

        if os.path.isfile(TRAIN_LABELS_NEGATIVE_DIR + "/" + file_name[:-5] + ".csv"):
            user_to_not_done_tips[file_name[:-5]] = []
            for row in open(TRAIN_LABELS_NEGATIVE_DIR + "/" + file_name[:-5] + ".csv", 'r'):
                tip = row[:-1]
                user_to_not_done_tips[file_name[:-5]].append(tip)

    return recommend_input_done, recommend_input_not_done, user_to_done_tips, user_to_not_done_tips
