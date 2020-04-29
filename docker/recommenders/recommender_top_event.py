import logging
from tqdm import tqdm
import operator

from recommenders.recommender import Recommender
from util import _is_intersection
from reader import event_to_tips

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


def _get_event_to_count(train_events):
    event_to_count = {}

    for (device_id, group_id, event_id) in tqdm(train_events.keys()):
        _, cnt = train_events[(device_id, group_id, event_id)]
        if (group_id, event_id) in event_to_count.keys():
            event_to_count[(group_id, event_id)] = event_to_count[(group_id, event_id)] + cnt
        else:
            event_to_count[(group_id, event_id)] = cnt
    return event_to_count


def _get_top_events(train_events, is_logging):
    if is_logging:
        logging.info("RecommenderTopEvent:get_top_events: generating top events started.")

    event_to_count = _get_event_to_count(train_events)
    if is_logging:
        logging.info("RecommenderTopEvent:get_top_events: event_to_count computed.")

    sorted_by_count_events = sorted(event_to_count.items(), key=operator.itemgetter(1), reverse=True)
    if is_logging:
        logging.info("RecommenderTopEvent:get_top_events: event_to_count sorted.")

    all_count_sum = 0
    for event_count in sorted_by_count_events:
        all_count_sum += event_count[1]

    top_events = [(x[0], x[1] / all_count_sum) for x in sorted_by_count_events]
    if is_logging:
        logging.info("RecommenderTopEvent:get_top_events: events top list received.")

    return top_events


class RecommenderTopEvent(Recommender):
    def __init__(self, train_devices, event_types, train_events, is_logging=True):
        if is_logging:
            logging.info("RecommenderTopEvent:init: init started.")
        super(RecommenderTopEvent, self).__init__(train_devices, event_types, train_events, is_logging)
        self.top_events = _get_top_events(self.train_events, self.is_logging)
    
    def recommend(self, test_device_events, tips):
        if self.is_logging:
            logging.info("RecommenderTopEvent:recommend: recommendation started.")
        test_device_events = self._filter_old_test_device_events(test_device_events)

        tips_to_recommend = []

        for top_event in self.top_events:
            top_event = top_event[0]
            if (top_event not in test_device_events.keys())\
                    and _is_intersection(tips, event_to_tips(top_event)) > 0:
                for tip in event_to_tips(top_event):
                    if tip in tips:
                        tips_to_recommend.append(tip)
        if self.is_logging:
            logging.info("RecommenderTopEvent:recommend: recommendation made.")
        return tips_to_recommend
