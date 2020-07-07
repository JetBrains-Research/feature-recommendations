from reader import read_events_raw, event_to_tips
from constants import TIPS_GROUP, ACTION_INVOKED_GROUP, PREDICTED_TIME_MILLIS, FORGET_TIME_DAYS
import os
from tqdm import tqdm
from enum import Enum

PATH = os.path.split(__file__)[0]
PER_DEVICE_LOG_DIR = PATH + "/per_device_per_month_logs/"
PER_DEVICE_LOG_FILES = ""
LOG_FILE_OUT = PATH + "/preprocessed_logs.csv"
if os.path.isdir(PER_DEVICE_LOG_DIR):
    PER_DEVICE_LOG_FILES = os.listdir(PER_DEVICE_LOG_DIR)


class PreprocessedEvent:
    class Type(Enum):
        TIP = 0
        ACTION = 1

    def __init__(self, type, timestamp, device_id, filename, was_done_before=None, action_id=None):
        self.type = type
        self.timestamp = timestamp
        self.device_id = device_id
        self.filename = filename
        self.was_done_before = was_done_before
        self.action_id = action_id


class PreprocessedLogBuilder:
    def process_tip(self, event):
        tip_name = event.event_id.split(";")[0]
        algo_name = event.event_id.split(";")[1]

        is_tip_done_before = False
        for done_action in self.done_actions.keys():
            event_id, _ = done_action
            action_timestamp, _ = self.done_actions[done_action]

            if tip_name in event_to_tips(group_id=ACTION_INVOKED_GROUP, event_id=event_id) \
                    and event.timestamp - action_timestamp < FORGET_TIME_DAYS * 24 * 60 * 60 * 1000:
                self.preprocessed_logs.append(
                     PreprocessedEvent(
                         PreprocessedEvent.Type.ACTION, event.timestamp, event.device_id, tip_name, action_id=event_id))
                is_tip_done_before = True
                break

        if not is_tip_done_before:
            self.shown_tips.append((tip_name, event.timestamp, algo_name))
            self.preprocessed_logs.append(
                PreprocessedEvent(
                    PreprocessedEvent.Type.TIP, event.timestamp, event.device_id, tip_name, was_done_before=False))
        else:
            self.preprocessed_logs.append(
                 PreprocessedEvent(
                     PreprocessedEvent.Type.TIP, event.timestamp, event.device_id, tip_name, was_done_before=True))

    def process_action(self, event):
        if (event.event_id, event.ide) not in self.done_actions.keys():
            self.done_actions[(event.event_id, event.ide)] = (event.timestamp, event.count)
        else:
            _, cnt = self.done_actions[(event.event_id, event.ide)]
            self.done_actions[(event.event_id, event.ide)] = \
                (event.timestamp, cnt + event.count)

        for (tip, tip_timestamp, algo) in self.shown_tips:
            if tip in event_to_tips(group_id=ACTION_INVOKED_GROUP, event_id=event.event_id):
                self.preprocessed_logs.append(
                     PreprocessedEvent(
                         PreprocessedEvent.Type.ACTION, event.timestamp, event.device_id, tip, action_id=event.event_id))

    def process(self, events):
        tips_cnt = 0
        for event in events:
            if event.group_id == TIPS_GROUP:
                self.process_tip(event)
                tips_cnt += 1

            else:
                if event.group_id == ACTION_INVOKED_GROUP:
                    self.process_action(event)

        return self.preprocessed_logs

    def __init__(self):
        self.shown_tips = []
        self.done_actions = {}
        self.preprocessed_logs = []


if __name__ == "__main__":
    preprocessed_logs = []
    for file_name in tqdm(PER_DEVICE_LOG_FILES):
        if not (file_name[-4:] == '.csv'):
            continue
        events, event_types, devices = read_events_raw(PER_DEVICE_LOG_DIR + file_name)
        events.sort(key=lambda x: x.timestamp)
        logs = PreprocessedLogBuilder().process(events)
        for log in logs:
            preprocessed_logs.append(log)

    preprocessed_logs.sort(key=lambda x: x.timestamp)
    with open(LOG_FILE_OUT, 'w') as fout:
        for log in preprocessed_logs:
            log_string = ""
            if log.type == PreprocessedEvent.Type.TIP:
                log_string += "TIP,"
            else:
                log_string += "ACTION,"
            log_string += str(log.timestamp) + ","
            log_string += log.device_id + ","
            log_string += log.filename + ","
            if log.type == PreprocessedEvent.Type.TIP:
                log_string += str(log.was_done_before) + "\n"
            else:
                log_string += log.action_id + "\n"
            fout.write(log_string)
