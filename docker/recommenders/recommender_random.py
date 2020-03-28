import logging
import random

from recommenders.recommender import Recommender, _is_intersection
from reader import event_to_tips

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


class RecommenderRandom(Recommender):
    def __init__(self, train_devices, event_types, train_events):
        logging.info("RecommenderRandom:init: init started.")
        super(RecommenderRandom, self).__init__(None, None, None)

    def recommend(self, test_device_events, tips):
        logging.info("RecommenderRandom:recommend: recommendation started.")
        random.shuffle(tips)
        logging.info("RecommenderRandom:recommend: recommendation made.")
        return tips
