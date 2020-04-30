import implicit
import logging
import numpy as np
from scipy.spatial.distance import cosine

from recommenders.recommender_matrix_factorization_base import BaseMatrixRecommender

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


class BayesianPersonalizedRanking(BaseMatrixRecommender):
    def __init__(self, train_devices, event_types, train_events, is_logging=True):
        model = implicit.bpr.BayesianPersonalizedRanking(factors=50)
        super(BayesianPersonalizedRanking, self).__init__(train_devices, event_types, train_events, model,
                                                          "BayesianPersonalizedRanking", is_logging)

    def _get_indices_by_events(self, events):
        indices = []
        for event in events.keys():
            group_id, event_id = event
            if (group_id, event_id) in self.event_to_index.keys():
                index = self.event_to_index[(group_id, event_id)]
                indices.append(index)
        return indices

    def _ids_to_1_0(self, ids):
        answer = np.array([0.0] * len(self.event_types))
        answer[ids] = 1.0
        return answer

    def _find_closest_device(self, test_device_indices):
        test_device_indices = self._ids_to_1_0(test_device_indices)
        best_index = 0
        indices = self._ids_to_1_0(self.user_to_event_index[0])
        min_distance = cosine(test_device_indices, indices)
        for index in self.user_to_event_index.keys():
            indices = self._ids_to_1_0(self.user_to_event_index[index])
            dist = cosine(test_device_indices, indices)
            if dist < min_distance:
                min_distance = dist
                best_index = index
        return best_index

    def recommend(self, test_device_events, tips):
        if self.is_logging:
            logging.info("BayesianPersonalizedRanking: matrix data computed, recommend started")

        test_device_indices = self._get_indices_by_events(test_device_events)

        closest_device_index = self._find_closest_device(test_device_indices)

        user_items = self.matrix.transpose().tocsr()

        recommendation = self.model.recommend(closest_device_index, user_items, N=len(self.event_types))
        if self.is_logging:
            logging.info("BayesianPersonalizedRanking: model recommend")

        return self._generate_recommendation_list(recommendation, test_device_events, tips)