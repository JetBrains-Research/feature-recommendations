from constants import ACTION_INVOKED_GROUP, FORGET_TIME_DAYS

class Recommender:
    def __init__(self, train_devices, event_types, train_events):
        self.train_devices = train_devices
        self.event_types = event_types
        self.train_events = train_events
        self.forget_time_millis = FORGET_TIME_DAYS * 24 * 60 * 60 * 1000

    def _get_current_time_millis(self, test_device_events):
        max_timestamp = None
        for (group_id, event_id) in test_device_events:
            last_timestamp, _ = test_device_events[(group_id, event_id)]
            if not max_timestamp:
                max_timestamp = last_timestamp
            else:
                max_timestamp = max(max_timestamp, last_timestamp)
        return max_timestamp

    def _filter_old_test_device_events(self, test_device_events):
        current_time_millis = self._get_current_time_millis(test_device_events)
        filtered_test_device_events = {}
        for (group_id, event_id) in test_device_events.keys():
            if group_id != ACTION_INVOKED_GROUP:
                continue

            last_timestamp, cnt = test_device_events[(group_id, event_id)]
            if last_timestamp >= current_time_millis - self.forget_time_millis:
                filtered_test_device_events[(group_id, event_id)] = (last_timestamp, cnt)
        return filtered_test_device_events

    def recommend(self, test_device_events, tips):
        pass
