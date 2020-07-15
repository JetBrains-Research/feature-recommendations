import logging
import random

from recommenders.recommender import Recommender

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


class RecommenderOneTip(Recommender):
    def __init__(self, train_devices, event_types, train_events, is_logging=True):
        if is_logging:
            logging.info("RecommenderOneTip:init: init started.")
        super(RecommenderOneTip, self).__init__(None, None, None, is_logging)
        self.the_tip = "neue-smart_selection.html"

    def recommend(self, test_device_events, tips):
        if self.is_logging:
            logging.info("RecommenderOneTip:recommend: recommendation started.")
        random.shuffle(tips)
        new_tips = []
        is_tip_met = False
        for tip in tips:
            if self.the_tip == tip:
                is_tip_met = True
            else:
                new_tips.append(tip)
        if is_tip_met:
            new_tips = [self.the_tip] + new_tips
        if self.is_logging:
            logging.info("RecommenderOneTip:recommend: recommendation made.")
        return new_tips
