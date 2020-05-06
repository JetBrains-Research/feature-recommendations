import json
import shutil
import numpy as np

import reader
from constants import *
from reader import event_to_tips, ide_to_tips


class LabeledTestFileGenerator:
    def generate_file_name(self, device_id, end, tip_id):
        return "/" + str(self.file_id) + "_" + str(tip_id) + "_" + device_id + "." + end

    def process_tip(self, event):
        data = {
            "tips": [],
            "usageInfo": {},
            "bucket": event.bucket,
            'ideName': event.ide
        }
        tip_name = event.event_id.split(";")[0]

        for t in self.ide_tips[event.ide].keys():
            data["tips"].append(t)

        is_tip_done_before = False

        for done_action in self.device_to_done_actions[event.device_id].keys():

            event_id, ide = done_action

            max_timestamp, count = self.device_to_done_actions[event.device_id][done_action]

            if tip_name in event_to_tips(group_id=ACTION_INVOKED_GROUP, event_id=event_id):
                is_tip_done_before = True
                break

            if ide == event.ide:
                data["usageInfo"][event_id] = {}
                data["usageInfo"][event_id]["usageCount"] = count
                data["usageInfo"][event_id]["lastUsedTimestamp"] = max_timestamp
        if not is_tip_done_before:
            with open(TRAIN_EVENTS_DIR + self.generate_file_name(event.device_id, "json", self.tip_id_cur), 'w') as fout:
                json.dump(data, fout)

            if event.device_id not in self.device_to_tips.keys():
                self.device_to_tips[event.device_id] = []
            self.device_to_tips[event.device_id].append((tip_name, event.timestamp, str(self.tip_id_cur)))
            self.tip_id_cur += 1

    def process_action(self, event):
        if event.device_id not in self.device_to_done_actions.keys():
            self.device_to_done_actions[event.device_id] = {}

        if (event.event_id, event.ide) not in self.device_to_done_actions[event.device_id].keys():
            self.device_to_done_actions[event.device_id][(event.event_id, event.ide)] = (event.timestamp, event.count)
        else:
            _, cnt = self.device_to_done_actions[event.device_id][(event.event_id, event.ide)]
            self.device_to_done_actions[event.device_id][(event.event_id, event.ide)] = \
                (event.timestamp, cnt + event.count)

        if event.device_id in self.device_to_tips.keys():
            for (tip, tip_timestamp, tip_id) in self.device_to_tips[event.device_id]:
                if tip in event_to_tips(group_id=ACTION_INVOKED_GROUP, event_id=event.event_id):
                    if event.timestamp - tip_timestamp < PREDICTED_TIME_MILLIS:
                        with open(TRAIN_LABELS_POSITIVE_DIR + self.generate_file_name(event.device_id, "csv", tip_id), 'w') as fout:
                            fout.write(tip + "\n")
                        self.tips_done[tip_id] = True

    def process_not_done_tips(self):
        for device_id in self.device_to_tips.keys():
            for (tip, timestamp, tip_id) in self.device_to_tips[device_id]:
                if tip_id not in self.tips_done.keys():
                    with open(TRAIN_LABELS_NEGATIVE_DIR + self.generate_file_name(device_id, "csv", tip_id), 'w') as fout:
                        fout.write(tip + "\n")

    def generate(self):
        for event in self.events:
            if event.group_id == TIPS_GROUP:
                if event.device_id in self.device_to_done_actions.keys():
                    self.process_tip(event)
            else:
                if event.group_id == ACTION_INVOKED_GROUP:
                    self.process_action(event)
        self.process_not_done_tips()

    def __init__(self, file_name, file_id):
        self.events, _, _ = reader.read_events_raw(file_name)

        self.events.sort(key=lambda x: x.timestamp)

        self.ide_tips = ide_to_tips(file_name)
        self.device_to_done_actions = {}
        self.device_to_tips = {}
        self.tips_done = {}
        self.tip_id_cur = 0
        self.file_id = file_id

        self.generate()


def rm_make(file_name):
    if os.path.isdir(file_name):
        shutil.rmtree(file_name)
    os.mkdir(file_name)


def generate_dirs():
    rm_make(TEST_EVENTS_DIR)
    rm_make(TRAIN_EVENTS_DIR)
    rm_make(TEST_LABELS_NEGATIVE_DIR)
    rm_make(TRAIN_LABELS_NEGATIVE_DIR)
    rm_make(TEST_LABELS_POSITIVE_DIR)
    rm_make(TRAIN_LABELS_POSITIVE_DIR)


def split_train_test():
    positive_files = os.listdir(TRAIN_LABELS_POSITIVE_DIR)
    negative_files = os.listdir(TRAIN_LABELS_NEGATIVE_DIR)
    positive_test_files = np.random.choice(positive_files, int(len(positive_files) * 0.1), replace=False)
    negative_test_files = np.random.choice(negative_files, int(len(negative_files) * 0.1), replace=False)

    for file in positive_test_files:
        os.rename(TRAIN_LABELS_POSITIVE_DIR + "/" + file, TEST_LABELS_POSITIVE_DIR + "/" + file)
        os.rename(TRAIN_EVENTS_DIR + "/" + file[:-3] + "json", TEST_EVENTS_DIR + "/" + file[:-3] + "json")

    for file in negative_test_files:
        os.rename(TRAIN_LABELS_NEGATIVE_DIR + "/" + file, TEST_LABELS_NEGATIVE_DIR + "/" + file)
        os.rename(TRAIN_EVENTS_DIR + "/" + file[:-3] + "json", TEST_EVENTS_DIR + "/" + file[:-3] + "json")


if __name__ == '__main__':
    generate_dirs()

    i = 0
    for file_name in LABELS_DATA_SOURCE_FILES:
        if file_name.endswith(".csv"):
            print(i)
            print(file_name)
            LabeledTestFileGenerator(LABELS_DATA_SOURCE + "/" + file_name, str(i))
            i += 1

    split_train_test()
