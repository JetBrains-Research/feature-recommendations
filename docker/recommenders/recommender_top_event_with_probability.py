import logging

from recommenders.recommender_top_event import RecommenderTopEvent, _is_intersection
from reader import event_to_tips
import numpy as np

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


class RecommenderTopEventWithProbability(RecommenderTopEvent):
    def _get_not_done_events_with_probability(self, test_device_events, tips):
        not_done_event_with_prob = []
        all_not_done_top_sum = 0

        for top_event in self.top_events:
            event = top_event[0]
            probability = top_event[1]
            if (event not in test_device_events.keys()) \
                    and _is_intersection(tips, event_to_tips(event)) > 0:
                not_done_event_with_prob.append(top_event)
                all_not_done_top_sum += probability

        return not_done_event_with_prob, all_not_done_top_sum

    def recommend(self, test_device_events, tips):
        logging.info("RecommenderTopEventWithProbability:recommend: recommendation started.")

        test_device_events = self._filter_old_test_device_events(test_device_events)

        not_done_event_with_prob, all_not_done_top_sum = \
            self._get_not_done_events_with_probability(test_device_events, tips)
        logging.info("RecommenderTopEventWithProbability:recommend: not_done_events computed, " +
                     str(len(not_done_event_with_prob)) + " found.")

        if len(not_done_event_with_prob) <= 0:
            return event_to_tips(self.top_events[0][0])

        probs = []
        for event in not_done_event_with_prob:
            probs.append(event[1] / all_not_done_top_sum)

        logging.info("RecommenderTopEventWithProbability:recommend: probability for not_done_events computed")

        events_ids = np.random.choice(range(len(not_done_event_with_prob)), len(not_done_event_with_prob), replace=False, p=probs)
        events = np.array(not_done_event_with_prob)[events_ids]
        tips_to_recommend = []
        for event in events:
            for tip in event_to_tips(event[0]):
                if tip in tips:
                    tips_to_recommend.append(tip)
        logging.info("RecommenderTopEventWithProbability:recommend: tip generated.")

        return tips_to_recommend
