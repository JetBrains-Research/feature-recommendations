import logging
import random

from recommenders.recommender import Recommender

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


class RecommenderOneTip(Recommender):
    def __init__(self, train_devices, event_types, train_events, is_logging=True):
        if is_logging:
            logging.info("RecommenderOneTip:init: init started.")
        super(RecommenderOneTip, self).__init__(None, None, None, is_logging)

    def recommend(self, test_device_events, tips):
        if self.is_logging:
            logging.info("RecommenderOneTip:recommend: recommendation started.")
        random.shuffle(tips)
        if self.is_logging:
            logging.info("RecommenderOneTip:recommend: recommendation made.")
        return tips
