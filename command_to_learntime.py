import operator

from reader import read_events_raw, action_id_to_tips_dict
from constants import TIPS_GROUP, ACTION_INVOKED_GROUP, PREDICTED_TIME_MILLIS, INPUT_FILE_NAME, LEARN_TIME_FILE_NAME


class LearnTime:
    def process_tip(self, event):
        tip_name = event.event_id.split(";")[0]

        if event.device_id not in self.device_to_tips.keys():
            self.device_to_tips[event.device_id] = []
        self.device_to_tips[event.device_id].append((tip_name, event.timestamp))

    def process_action(self, event):
        if event.event_id in self.commands_from_tips:
            if (event.device_id, event.event_id) not in self.command_device_to_time.keys():
                is_from_tip = False
                if event.device_id in self.device_to_tips.keys():
                    for (tip, tip_timestamp) in self.device_to_tips[event.device_id]:
                        if event.timestamp - tip_timestamp < PREDICTED_TIME_MILLIS:
                            is_from_tip = True
                if not is_from_tip:
                    self.command_device_to_time[(event.device_id, event.event_id)] = event.timestamp - self.device_to_first_timestamp[event.device_id]

    def build(self, events):
        tips_cnt = 0
        for event in events:
            if event.device_id not in self.device_to_first_timestamp.keys():
                self.device_to_first_timestamp[event.device_id] = event.timestamp
            if event.group_id == TIPS_GROUP:
                self.process_tip(event)
                tips_cnt += 1

            else:
                if event.group_id == ACTION_INVOKED_GROUP:
                    self.process_action(event)

        command_to_average_time = {}
        command_to_cnt = {}

        for (device_id, command) in self.command_device_to_time.keys():
            if command not in command_to_average_time.keys():
                command_to_average_time[command] = self.command_device_to_time[(device_id, command)]
                command_to_cnt[command] = 1
            else:
                command_to_average_time[command] += self.command_device_to_time[(device_id, command)]
                command_to_cnt[command] += 1

        for command in command_to_average_time.keys():
            command_to_average_time[command] = command_to_average_time[command] * 1.0 / command_to_cnt[command]

        sorted_command_to_average_time = sorted(command_to_average_time.items(), key=operator.itemgetter(1), reverse=True)
        print(len(list(sorted_command_to_average_time)))
        print(len(list(self.commands_from_tips)))
        return sorted_command_to_average_time, command_to_cnt

    def __init__(self):
        self.command_device_to_time = {}
        self.device_to_tips = {}
        self.commands_from_tips = action_id_to_tips_dict.keys()
        self.device_to_first_timestamp = {}


if __name__ == "__main__":
    events, event_types, devices = read_events_raw(INPUT_FILE_NAME)
    events.sort(key=lambda x: x.timestamp)
    command_to_average_time, command_to_cnt = LearnTime().build(events)
    with open(LEARN_TIME_FILE_NAME, 'w') as fout:
        for element in command_to_average_time:
            print(str(element[0]) + " " + str(element[1] / 1000 / 60 / 60 / 24))
            print(command_to_cnt[element[0]])
            if command_to_cnt[element[0]] > 10:
                fout.write(str(element[0]) + "," + str(int(element[1])) + "\n")

