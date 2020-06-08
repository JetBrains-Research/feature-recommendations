import logging
import os
import pickle

from recommenders.recommender import Recommender
from reader import read_test_pairs
from constants import METHOD_TO_FILE_NAME, Method
from recommenders.recommender_top_event import RecommenderTopEvent
from recommenders.recommender_als import AlternatingLeastSquares
from recommenders.recommender_widely_used import RecommenderWidelyUsed
from recommenders.recommender_codis import RecommenderCoDis

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


class RecommenderWeightsBase(Recommender):
    def train(self):
        pass

    def __init__(self, train_devices, event_types, train_events, is_logging):
        if is_logging:
            logging.info("RecommenderWeightsBase:init: init started.")
        super(RecommenderWeightsBase, self).__init__(None, None, None, is_logging)
        self.recommend_input_done, self.recommend_input_not_done, self.user_to_done_tips, self.user_to_not_done_tips =\
            read_test_pairs()
        algorithms_classes = [RecommenderTopEvent, AlternatingLeastSquares, RecommenderWidelyUsed, RecommenderCoDis]
        algorithms_ids = [Method.TOP, Method.MATRIX_ALS, Method.WIDE, Method.CODIS]
        self.algorithms = []
        for i in range(len(algorithms_classes)):
            if os.path.isfile(METHOD_TO_FILE_NAME[algorithms_ids[i]]):
                with open(METHOD_TO_FILE_NAME[algorithms_ids[i]], 'rb') as f:
                    self.algorithms.append(pickle.load(f))
                    if self.is_logging:
                        logging.info("RecommenderWeightsBase: Algorithm " + str(algorithms_ids[i].name) + " loaded.")
            else:
                self.algorithms.append(algorithms_classes[i](train_devices, event_types, train_events, False))
                if self.is_logging:
                    logging.info("RecommenderWeightsBase: Algorithm " + str(algorithms_ids[i].name) + " generated.")
                with open(METHOD_TO_FILE_NAME[algorithms_ids[i]], 'wb') as f:
                    pickle.dump(self.algorithms[i], f)
                    if self.is_logging:
                        logging.info("RecommenderWeightsBase: Algorithm " + str(algorithms_ids[i].name) + " saved.")
        for algo in self.algorithms:
            algo.is_logging = False
        if self.is_logging:
            logging.info("RecommenderWeightsBase: train starting")
        self.train()
