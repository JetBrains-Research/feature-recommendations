from reader import read_events_raw, event_to_tips
from constants import TIPS_GROUP, ACTION_INVOKED_GROUP, PREDICTED_TIME_MILLIS, FORGET_TIME_DAYS

INPUT_FILE_NAME = "./log_sample_with_answers_full.csv"


class Evaluation:
    def process_tip(self, event):
        tip_name = event.event_id.split(";")[0]
        algo_name = event.event_id.split(";")[1]

        if algo_name not in self.all_tips_cnt.keys():
            self.all_tips_cnt[algo_name] = 0
            self.good_tips_cnt[algo_name] = 0
            self.devices_good[algo_name] = {}
            self.devices_all[algo_name] = {}
        self.all_tips_cnt[algo_name] += 1
        self.devices_all[algo_name][event.device_id] = True

        is_tip_done_before = False
        if event.device_id in self.device_to_done_actions.keys():
            for done_action in self.device_to_done_actions[event.device_id].keys():
                event_id, _ = done_action
                action_timestamp, _ = self.device_to_done_actions[event.device_id][done_action]

                if tip_name in event_to_tips(group_id=ACTION_INVOKED_GROUP, event_id=event_id) \
                        and event.timestamp - action_timestamp < FORGET_TIME_DAYS * 24 * 60 * 60 * 1000:
                    is_tip_done_before = True
                    break

        if not is_tip_done_before:
            if event.device_id not in self.device_to_tips.keys():
                self.device_to_tips[event.device_id] = []
            self.device_to_tips[event.device_id].append((tip_name, event.timestamp, algo_name))

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
            for (tip, tip_timestamp, algo) in self.device_to_tips[event.device_id]:
                if tip in event_to_tips(group_id=ACTION_INVOKED_GROUP, event_id=event.event_id):
                    if event.timestamp - tip_timestamp < PREDICTED_TIME_MILLIS:
                        self.good_tips_cnt[algo] += 1
                        self.devices_good[algo][event.device_id] = True

    def evaluate(self, events):
        tips_cnt = 0
        for event in events:
            if event.group_id == TIPS_GROUP:
                self.process_tip(event)
                tips_cnt += 1

            else:
                if event.group_id == ACTION_INVOKED_GROUP:
                    self.process_action(event)

        accuracy = {}
        device_accuracy = {}
        for algo in self.all_tips_cnt.keys():
            accuracy[algo] = self.good_tips_cnt[algo] * 1. / self.all_tips_cnt[algo]
            device_accuracy[algo] = len(self.devices_good[algo].keys()) * 1. / len(self.devices_all[algo].keys())

        return accuracy, device_accuracy, self.good_tips_cnt, self.all_tips_cnt

    def __init__(self):
        self.device_to_done_actions = {}
        self.device_to_tips = {}
        self.good_tips_cnt = {}
        self.all_tips_cnt = {}
        self.devices_good = {}
        self.devices_all = {}


if __name__ == "__main__":
    events, event_types, devices = read_events_raw(INPUT_FILE_NAME)
    events.sort(key=lambda x: x.timestamp)
    accuracy, users_accuracy, good_tips_cnt, all_tips_cnt = Evaluation().evaluate(events)
    for algo in accuracy.keys():
        print(f"{algo}: percent of followed tips: {accuracy[algo] * 100}")
        print(f"{algo}: good tips count: {good_tips_cnt[algo]}")
        print(f"{algo}: all tips count: {all_tips_cnt[algo]}")
        print(f"{algo}: percent of users who followed the tips is: {users_accuracy[algo] * 100}")

