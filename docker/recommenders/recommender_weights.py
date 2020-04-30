import logging
import os
import pickle
import operator
from scipy.optimize import basinhopping, brute, differential_evolution, shgo, dual_annealing
import numpy as np
from tqdm import tqdm


from recommenders.recommender import Recommender
from reader import read_test_pairs
from constants import METHOD_TO_FILE_NAME, Method
from metrics import compute_map_k

from recommenders.recommender_top_event import RecommenderTopEvent
from recommenders.recommender_top_event_with_probability import RecommenderTopEventWithProbability
from recommenders.recommender_bpr import BayesianPersonalizedRanking
from recommenders.recommender_widely_used import RecommenderWidelyUsed
from recommenders.recommender_codis import RecommenderCoDis

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


class RecommenderWeights(Recommender):
    def _loss(self, weights):
        user_to_recommended = {}
        for device_id in tqdm(self.user_to_events_tips.keys()):
            test_device_events, tips = self.user_to_events_tips[device_id]
            recommended_tips = self._recommend(test_device_events, tips, weights, False)
            user_to_recommended[device_id] = recommended_tips
        return -compute_map_k(self.user_to_done_tips, user_to_recommended, 10)

    def _train(self):
        self.weights = shgo(self._loss, bounds=[(0, 1), (0, 1), (0, 1), (0, 1)])['x']
        logging.info("RecommenderWeights: shgo train done, weights = " + str(self.weights))

        self.weights = np.array([1., 1., 1., 1.])

        self.weights = brute(self._loss, ranges=[(0, 1), (0, 1), (0, 1), (0, 1)])[0]
        logging.info("RecommenderWeights: brute train done, weights = " + str(self.weights))

        self.weights = np.array([1., 1., 1., 1.])

        self.weights = basinhopping(self._loss, np.array([1., 1., 1., 1.]), niter=1).x
        logging.info("RecommenderWeights: basinhopping train done, weights = " + str(self.weights))

        self.weights = np.array([1., 1., 1., 1.])

        self.weights = differential_evolution(self._loss, bounds=[(0, 1), (0, 1), (0, 1), (0, 1)])['x']
        logging.info("RecommenderWeights: differential_evolution train done, weights = " + str(self.weights))

        self.weights = np.array([1., 1., 1., 1.])

        self.weights = dual_annealing(self._loss, bounds=[(0, 1), (0, 1), (0, 1), (0, 1)])['x']
        logging.info("RecommenderWeights: dual_annealing train done, weights = " + str(self.weights))

    def __init__(self, train_devices, event_types, train_events, is_logging=True):
        if is_logging:
            logging.info("RecommenderWeights:init: init started.")
        super(RecommenderWeights, self).__init__(None, None, None, is_logging)
        self.user_to_events_tips, self.user_to_done_tips = read_test_pairs()
        algorithms_classes = [RecommenderTopEvent, BayesianPersonalizedRanking, RecommenderWidelyUsed, RecommenderCoDis]
        algorithms_ids = [Method.TOP, Method.MATRIX_BPR, Method.WIDE, Method.CODIS]
        self.weights = np.array([1., 1., 1., 1.])
        self.algorithms = []
        for i in range(len(algorithms_classes)):
            if os.path.isfile(METHOD_TO_FILE_NAME[algorithms_ids[i]]):
                with open(METHOD_TO_FILE_NAME[algorithms_ids[i]], 'rb') as f:
                    self.algorithms.append(pickle.load(f))
                    if self.is_logging:
                        logging.info("RecommenderWeights: Algorithm " + str(algorithms_ids[i].name) + " loaded.")
            else:
                self.algorithms.append(algorithms_classes[i](train_devices, event_types, train_events, False))
                if self.is_logging:
                    logging.info("RecommenderWeights: Algorithm " + str(algorithms_ids[i].name) + " generated.")
                with open(METHOD_TO_FILE_NAME[algorithms_ids[i]], 'wb') as f:
                    pickle.dump(self.algorithms[i], f)
                    if self.is_logging:
                        logging.info("RecommenderWeights: Algorithm " + str(algorithms_ids[i].name) + " saved.")
        for algo in self.algorithms:
            algo.is_logging = False
        if self.is_logging:
            logging.info("RecommenderWeights: train starting")
        self._train()
        if self.is_logging:
            logging.info("RecommenderWeights: weights: " + str(self.weights))

    def recommend(self, test_device_events, tips):
        return self._recommend(test_device_events, tips, self.weights, True)

    def _recommend(self, test_device_events, tips, weights, is_logging):
        if is_logging:
            logging.info("RecommenderWeights:recommend: recommendation started.")

        recommendations = {}
        for i in range(len(self.algorithms)):
            recommendations[i] = self.algorithms[i].recommend(test_device_events, tips)

        added = {}
        recommended_tips = []

        while True:
            tip_to_score = {}

            for j in range(len(recommendations.keys())):
                p = 0
                tip = recommendations[j][p]
                while p < len(recommendations[j]) and (tip in added.keys()):
                    tip = recommendations[j][p]
                    p += 1
                if p == len(recommendations[j]):
                    continue
                if tip not in tip_to_score.keys():
                    tip_to_score[tip] = 0
                tip_to_score[tip] += weights[j]

            if not tip_to_score:
                break

            best_tip = max(tip_to_score.items(), key=operator.itemgetter(1))[0]
            added[best_tip] = True
            recommended_tips.append(best_tip)

        if is_logging:
            logging.info("RecommenderWeights:recommend: recommendation made.")
        return recommended_tips
