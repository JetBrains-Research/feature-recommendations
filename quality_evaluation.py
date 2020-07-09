from constants import PREDICTED_TIME_MILLIS, FORGET_TIME_DAYS
import os

from logs_preprocess import PreprocessedEvent

PATH = os.path.split(__file__)[0]
LOG_FILE_OUT = PATH + "/preprocessed_logs.csv"


class Evaluation:
    def process_tip(self, event):
        tip_name = event.filename
        algo_name = event.tip_algo_name

        if algo_name not in self.all_tips_cnt.keys():
            self.all_tips_cnt[algo_name] = 0
            self.good_tips_cnt[algo_name] = 0
            self.devices_good[algo_name] = {}
            self.devices_all[algo_name] = {}
        self.all_tips_cnt[algo_name] += 1
        self.devices_all[algo_name][event.device_id] = True

        is_tip_done_before = False
        if event.device_id in self.device_to_done_actions.keys():
            for filename in self.device_to_done_actions[event.device_id].keys():
                action_timestamp = self.device_to_done_actions[event.device_id][filename]

                if tip_name == filename and\
                        event.timestamp - action_timestamp < FORGET_TIME_DAYS * 24 * 60 * 60 * 1000:
                    is_tip_done_before = True
                    break

        if not is_tip_done_before:
            if event.device_id not in self.device_to_tips.keys():
                self.device_to_tips[event.device_id] = []
            self.device_to_tips[event.device_id].append((tip_name, event.timestamp, algo_name))

    def process_action(self, event):
        if event.device_id not in self.device_to_done_actions.keys():
            self.device_to_done_actions[event.device_id] = {}

        self.device_to_done_actions[event.device_id][event.filename] = event.timestamp

        if event.device_id in self.device_to_tips.keys():
            for (tip, tip_timestamp, algo) in self.device_to_tips[event.device_id]:
                if tip == event.filename and event.timestamp - tip_timestamp < PREDICTED_TIME_MILLIS and\
                        (event.device_id, tip, tip_timestamp) not in self.done_tips.keys():
                    self.good_tips_cnt[algo] += 1
                    self.done_tips[(event.device_id, tip, tip_timestamp)] = True
                    self.devices_good[algo][event.device_id] = True

    def evaluate(self, events):
        tips_cnt = 0
        for event in events:
            if event.type == PreprocessedEvent.Type.TIP:
                self.process_tip(event)
                tips_cnt += 1

            if event.type == PreprocessedEvent.Type.ACTION:
                self.process_action(event)

            if event.type == PreprocessedEvent.Type.TIP_GROUP:
                pass

        accuracy = {}
        device_accuracy = {}
        for algo in self.all_tips_cnt.keys():
            accuracy[algo] = self.good_tips_cnt[algo] * 1. / self.all_tips_cnt[algo]
            device_accuracy[algo] = len(self.devices_good[algo].keys()) * 1. / len(self.devices_all[algo].keys())

        return accuracy, device_accuracy, self.good_tips_cnt, self.all_tips_cnt

    def __init__(self):
        self.device_to_done_actions = {}
        self.device_to_tips = {}
        self.done_tips = {}
        self.good_tips_cnt = {}
        self.all_tips_cnt = {}
        self.devices_good = {}
        self.devices_all = {}


if __name__ == "__main__":
    preprocessed_logs = []

    with open(LOG_FILE_OUT, 'r') as fin:
        for line in fin:
            event_line = line.replace("\n", '').split(',')
            timestamp = int(event_line[1])
            device_id = event_line[2]
            event = None

            if event_line[0] == "TIP":
                type_ = PreprocessedEvent.Type.TIP
                filename = event_line[3]
                tip_algo_name = event_line[4]
                event = PreprocessedEvent(type_, timestamp, device_id, filename=filename, tip_algo_name=tip_algo_name)
            if event_line[0] == "ACTION":
                type_ = PreprocessedEvent.Type.ACTION
                filename = event_line[3]
                action_id = event_line[4]
                event = PreprocessedEvent(type_, timestamp, device_id, filename=filename, action_id=action_id)
            if event_line[0] == "TIP_GROUP":
                type_ = PreprocessedEvent.Type.TIP_GROUP
                event_id = event_line[3]
                event = PreprocessedEvent(type_, timestamp, device_id, tip_group_event_id=event_id)

            preprocessed_logs.append(event)

    accuracy, users_accuracy, good_tips_cnt, all_tips_cnt = Evaluation().evaluate(preprocessed_logs)
    for algo in accuracy.keys():
        print(f"{algo}: percent of followed tips: {accuracy[algo] * 100}")
        #print(f"{algo}: good tips count: {good_tips_cnt[algo]}")
        #print(f"{algo}: all tips count: {all_tips_cnt[algo]}")
        #print(f"{algo}: percent of users who followed the tips is: {users_accuracy[algo] * 100}")
