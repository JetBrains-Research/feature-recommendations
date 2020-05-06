import logging
import operator
from scipy.optimize import basinhopping, brute, differential_evolution, shgo, dual_annealing
import numpy as np
from tqdm import tqdm

from metrics import compute_map_k
from recommenders.recommender_weights_base import RecommenderWeightsBase

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


class RecommenderWeightsComplicated(RecommenderWeightsBase):
    def _loss(self, weights):
        user_to_recommended = {}
        for device_id in tqdm(self.recommend_input_done.keys()):
            test_device_events, tips = self.recommend_input_done[device_id]
            recommended_tips = self._recommend(test_device_events, tips, weights, False)
            user_to_recommended[device_id] = recommended_tips
        return -compute_map_k(self.user_to_done_tips, user_to_recommended, 10)

    def train(self):
        self.weights = brute(self._loss, ranges=[(0, 1), (0, 1), (0, 1), (0, 1)])[0]
        logging.info("RecommenderWeightsComplicated: brute train done, weights = " + str(self.weights))

        self.weights = np.array([1., 1., 1., 1.])

        self.weights = shgo(self._loss, bounds=[(0, 1), (0, 1), (0, 1), (0, 1)])['x']
        logging.info("RecommenderWeightsComplicated: shgo train done, weights = " + str(self.weights))

        self.weights = np.array([1., 1., 1., 1.])

        self.weights = basinhopping(self._loss, np.array([1., 1., 1., 1.]), niter=1).x
        logging.info("RecommenderWeightsComplicated: basinhopping train done, weights = " + str(self.weights))

        self.weights = np.array([1., 1., 1., 1.])

        self.weights = differential_evolution(self._loss, bounds=[(0, 1), (0, 1), (0, 1), (0, 1)])['x']
        logging.info("RecommenderWeightsComplicated: differential_evolution train done, weights = " + str(self.weights))

        self.weights = np.array([1., 1., 1., 1.])

        self.weights = dual_annealing(self._loss, bounds=[(0, 1), (0, 1), (0, 1), (0, 1)])['x']
        logging.info("RecommenderWeightsComplicated: dual_annealing train done, weights = " + str(self.weights))

    def __init__(self, train_devices, event_types, train_events, is_logging=True):
        if is_logging:
            logging.info("RecommenderWeightsComplicated:init: init started.")
        self.weights = np.array([1., 1., 1., 1.])
        super(RecommenderWeightsComplicated, self).__init__(train_devices, event_types, train_events, is_logging)

        if self.is_logging:
            logging.info("RecommenderWeightsComplicated: weights: " + str(self.weights))

    def recommend(self, test_device_events, tips):
        return self._recommend(test_device_events, tips, self.weights, True)

    def _recommend(self, test_device_events, tips, weights, is_logging):
        if is_logging:
            logging.info("RecommenderWeightsComplicated:recommend: recommendation started.")

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
            logging.info("RecommenderWeightsComplicated:recommend: recommendation made.")
        return recommended_tips
