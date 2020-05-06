import implicit
import logging
import numpy as np
from scipy.sparse import coo_matrix

from recommenders.recommender_matrix_factorization_base import BaseMatrixRecommender

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


class AlternatingLeastSquares(BaseMatrixRecommender):
    def __init__(self, train_devices, event_types, train_events, is_logging=True):
        model = implicit.als.AlternatingLeastSquares(factors=50)
        super(AlternatingLeastSquares, self).__init__(train_devices, event_types, train_events, model,
                                                      "AlternatingLeastSquares", is_logging)

    def test_events_to_matrix(self, test_device_events):
        data = []
        row_id = []
        col_id = []
        for event in test_device_events.keys():
            (group_id, event_id) = event
            if (group_id, event_id) in self.event_to_index.keys():
                data.append(1)
                row_id.append(self.event_to_index[(group_id, event_id)])
                col_id.append(0)

        matrix = coo_matrix((np.array(data), (np.array(row_id), np.array(col_id))),
                            dtype=float, shape=(len(self.event_types), len(self.train_devices)))

        return matrix.transpose().tocsr()

    def recommend_with_scores(self, test_device_events, tips):
        if self.is_logging:
            logging.info("AlternatingLeastSquares: matrix data computed, recommend started")

        test_vector = self.test_events_to_matrix(test_device_events)

        recommendation_vector = self.model.recommend(0, test_vector, N=len(self.event_types), recalculate_user=True)

        if self.is_logging:
            logging.info("AlternatingLeastSquares: model recommend")

        return self._generate_recommendation_list(recommendation_vector, test_device_events, tips)
