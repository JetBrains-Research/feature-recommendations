import csv
from tqdm import tqdm
import json
import logging

from constants import ACTION_INVOKED_GROUP, TIP_TO_EVENT_FILE_NAME, INPUT_FILE_NAME, TRAIN_TIME_MILLIS, TIPS_GROUP

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


def read_tip_to_event(file_name):
    _tip_to_action_ids_dict = {}
    _action_id_to_tips_dict = {}
    with open(file_name, 'r') as fin:
        for html_to_event in tqdm(csv.reader(fin, delimiter=',')):
            tip = html_to_event[0]
            action_id = html_to_event[1]
                
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


def event_to_tips(event):
    group_id, event_id = event
    if group_id != ACTION_INVOKED_GROUP:
        return []

    action_id = event_id
    if action_id in action_id_to_tips_dict.keys():
        return action_id_to_tips_dict[action_id]
    return []


def _check_group_event_id(group_id, event_id):
    return group_id not in ('performance', 'vcs.change.reminder') \
           and event_id not in ('ui.lagging',
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


def _extract_from_csv_row(event_data):
    count = event_data[12].split('.')[0]
    if count:
        count = int(count)
    else:
        count = 0

    group_id = event_data[5]
    event_id = event_data[10]

    if group_id == "actions" and event_id == "action.invoked":
        event_info = json.loads(event_data[11])
        group_id = ACTION_INVOKED_GROUP
        event_id = event_info["action_id"]

    if group_id == "ui.tips" and event_id == "tip.shown":
        event_info = json.loads(event_data[11])
        group_id = TIPS_GROUP
        event_id = event_info["filename"]

    timestamp = int(event_data[3])
    device_id = event_data[7]
    bucket = event_data[9]

    return group_id, event_id, device_id, count, timestamp, bucket


def read_events_raw(file_name):
    events = []
    event_types = {}
    devices = {}
    with open(file_name, 'r') as fin:
        is_first = True
        for event_data in tqdm(csv.reader(fin, delimiter=',')):
            if is_first:
                is_first = False
                continue

            group_id, event_id, device_id, count, timestamp, bucket = _extract_from_csv_row(event_data)

            if count and _check_group_event_id(group_id, event_id):
                event_types[(group_id, event_id)] = True
                devices[device_id] = True
                events.append((device_id, group_id, event_id, timestamp, count, bucket))

    devices = list(devices.keys())
    event_types = list(event_types.keys())
    return events, event_types, devices


def get_device_to_max_timestamp(events):
    device_to_max_timestamp = {}

    for event in tqdm(events):
        device_id, _, _, timestamp, _, _ = event

        if device_id not in device_to_max_timestamp.keys():
            device_to_max_timestamp[device_id] = timestamp
        else:
            device_to_max_timestamp[device_id] = max(device_to_max_timestamp[device_id], timestamp)

    return device_to_max_timestamp


def get_device_to_min_timestamp(events):
    device_to_min_timestamp = {}

    for event in tqdm(events):
        device_id, _, _, timestamp, _, _ = event

        if device_id not in device_to_min_timestamp.keys():
            device_to_min_timestamp[device_id] = timestamp
        else:
            device_to_min_timestamp[device_id] = min(device_to_min_timestamp[device_id], timestamp)

    return device_to_min_timestamp


def _ignore_old_events(events):
    device_to_max_timestamp = get_device_to_max_timestamp(events)

    train_events = {}
    for event in tqdm(events):
        device_id, group_id, event_id, timestamp, count, _ = event
        max_timestamp = device_to_max_timestamp[device_id]

        threshold = max_timestamp - TRAIN_TIME_MILLIS
        if timestamp >= threshold:
            if (device_id, group_id, event_id) in train_events.keys():
                _, prev_count = train_events[(device_id, group_id, event_id)]
                train_events[(device_id, group_id, event_id)] = (max_timestamp, prev_count + count)
            else:
                train_events[(device_id, group_id, event_id)] = (max_timestamp, count)
    return train_events


def read_events_from_file():
    events, events_types, train_device_ids = read_events_raw(INPUT_FILE_NAME)
        
    logging.info(str(len(train_device_ids)) + " devices found.")
    logging.info(str(len(events_types)) + " event types found.")

    train_events = _ignore_old_events(events)

    logging.info(str(len(train_events.keys())) + " train events will be used.")

    return train_events, events_types, train_device_ids


