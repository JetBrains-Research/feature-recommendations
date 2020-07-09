from reader import read_events_raw, event_to_tips, ide_to_tips
from constants import TIPS_GROUP, ACTION_INVOKED_GROUP
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
        TIP_GROUP = 2

    def __init__(self, type_, timestamp, device_id, filename=None, action_id=None, tip_group_event_id=None, tip_algo_name=None):
        self.type = type_
        self.timestamp = timestamp
        self.device_id = device_id
        self.filename = filename
        self.action_id = action_id
        self.tip_group_event_id = tip_group_event_id
        self.tip_algo_name = tip_algo_name


class PreprocessedLogBuilder:
    def process_tip(self, event):
        tip_name = event.event_id.split(";")[0]
        algo_name = event.event_id.split(";")[1]

        self.preprocessed_logs.append(
                PreprocessedEvent(
                    PreprocessedEvent.Type.TIP, event.timestamp, event.device_id,
                    filename=tip_name, tip_algo_name=algo_name))

    def process_action(self, event):
        ide = event.ide
        tips_all = self.ide_to_tips[ide]
        tips_action = event_to_tips(group_id=ACTION_INVOKED_GROUP, event_id=event.event_id)

        for tip in tips_action:
            if tip in tips_all:
                self.preprocessed_logs.append(
                     PreprocessedEvent(
                         PreprocessedEvent.Type.ACTION, event.timestamp, event.device_id,
                         filename=tip, action_id=event.event_id))

    def process_tips_group(self, event):
        self.preprocessed_logs.append(
            PreprocessedEvent(
                PreprocessedEvent.Type.TIP_GROUP, event.timestamp, event.device_id,
                tip_group_event_id=event.event_id))

    def process(self, events):
        tips_cnt = 0
        for event in events:
            if event.group_id == TIPS_GROUP:
                self.process_tip(event)
                tips_cnt += 1

            else:
                if event.group_id == ACTION_INVOKED_GROUP:
                    self.process_action(event)
                else:
                    if event.group_id == 'ui.tips':
                        self.process_tips_group(event)

        return self.preprocessed_logs

    def __init__(self):
        self.shown_tips = []
        self.done_actions = {}
        self.preprocessed_logs = []
        self.ide_to_tips = ide_to_tips()


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
            if log.type == PreprocessedEvent.Type.ACTION:
                log_string += "ACTION,"
            if log.type == PreprocessedEvent.Type.TIP_GROUP:
                log_string += "TIP_GROUP,"
            log_string += str(log.timestamp) + ","
            log_string += log.device_id + ","
            if log.type == PreprocessedEvent.Type.TIP:
                log_string += log.filename + ","
                log_string += log.tip_algo_name + "\n"
            if log.type == PreprocessedEvent.Type.ACTION:
                log_string += log.filename + ","
                log_string += log.action_id + "\n"
            if log.type == PreprocessedEvent.Type.TIP_GROUP:
                log_string += log.tip_group_event_id + "\n"
            fout.write(log_string)
