import logging
from tqdm import tqdm
import operator

from recommenders.recommender_top_event import RecommenderTopEvent

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


def _get_event_to_devices_count(train_events):
    event_to_devices = {}

    for (device_id, group_id, event_id) in tqdm(train_events.keys()):
        _, cnt = train_events[(device_id, group_id, event_id)]
        if (group_id, event_id) not in event_to_devices.keys():
            event_to_devices[(group_id, event_id)] = {}
        event_to_devices[(group_id, event_id)][device_id] = True

    event_to_device_count = {}
    for key in event_to_devices.keys():
        event_to_device_count[key] = len(list(event_to_devices[key].keys()))
    return event_to_device_count


def _get_top_events(train_events):
    logging.info("RecommenderWidelyUsed:get_top_events: generating top events started.")

    event_to_device_count = _get_event_to_devices_count(train_events)
    logging.info("RecommenderWidelyUsed:get_top_events: event_to_count computed.")

    sorted_by_count_events = sorted(event_to_device_count.items(), key=operator.itemgetter(1), reverse=True)
    logging.info("RecommenderWidelyUsed:get_top_events: event_to_count sorted.")

    all_count_sum = 0
    for event_count in sorted_by_count_events:
        all_count_sum += event_count[1]

    top_events = [(x[0], x[1] / all_count_sum) for x in sorted_by_count_events]
    logging.info("RecommenderWidelyUsed:get_top_events: events top list received.")

    return top_events


class RecommenderWidelyUsed(RecommenderTopEvent):
    def __init__(self, train_devices, event_types, train_events):
        logging.info("RecommenderWidelyUsed:init: init started.")
        super(RecommenderWidelyUsed, self).__init__(train_devices, event_types, train_events)
        self.top_events = _get_top_events(self.train_events)
