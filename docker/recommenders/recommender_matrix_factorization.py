import implicit
import logging
import numpy as np
from scipy.sparse import coo_matrix
from scipy.spatial.distance import cosine

from recommenders.recommender import Recommender, _is_intersection
from reader import event_to_tips

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


class BayesianPersonalizedRanking(Recommender):
    def _generate_indices(self):
        self.device_to_index = {}
        for i in range(len(self.train_devices)):
            self.device_to_index[self.train_devices[i]] = i

        self.event_to_index = {}
        for i in range(len(self.event_types)):
            self.event_to_index[self.event_types[i]] = i

    def _generate_user_to_event_index(self):
        self.user_to_event_index = {}
        for event in self.train_events.keys():
            device_id, group_id, event_id = event
            if self.device_to_index[device_id] not in self.user_to_event_index.keys():
                self.user_to_event_index[self.device_to_index[device_id]] = []
            self.user_to_event_index[self.device_to_index[device_id]].append(self.event_to_index[(group_id, event_id)])

    def _generate_matrix(self):
        data = []
        row_id = []
        col_id = []
        for event in self.train_events.keys():
            (device_id, group_id, event_id) = event
            data.append(1)
            row_id.append(self.event_to_index[(group_id, event_id)])
            col_id.append(self.device_to_index[device_id])

        logging.info("BayesianPersonalizedRanking: matrix data computed")

        matrix = coo_matrix((np.array(data), (np.array(row_id), np.array(col_id))),
                            dtype=float, shape=(len(self.event_types), len(self.train_devices)))
        return matrix

    def __init__(self, train_devices, event_types, train_events):
        super(BayesianPersonalizedRanking, self).__init__(train_devices, event_types, train_events)
        
        logging.info("BayesianPersonalizedRanking: init started")

        self._generate_indices()

        logging.info("BayesianPersonalizedRanking: device_to_index and event_to_index computed")

        self._generate_user_to_event_index()
         
        self.matrix = self._generate_matrix()
        logging.info("BayesianPersonalizedRanking: matrix generated")
        
        self.model = implicit.als.AlternatingLeastSquares(factors=50)
        self.model.fit(self.matrix, show_progress=True)
        logging.info("BayesianPersonalizedRanking: model fit")

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

    def _generate_test_matrix(self, test_device_events):
        data = []
        row_id = []
        col_id = []
        for event in self.train_events.keys():
            (device_id, group_id, event_id) = event
            data.append(1)
            row_id.append(self.event_to_index[(group_id, event_id)])
            col_id.append(self.device_to_index[device_id])

        for event in test_device_events.keys():
            (group_id, event_id) = event
            if (group_id, event_id) in self.event_to_index.keys():
                data.append(1)
                row_id.append(self.event_to_index[(group_id, event_id)])
                col_id.append(len(self.device_to_index.keys()))

        matrix = coo_matrix((np.array(data), (np.array(row_id), np.array(col_id))),
                            dtype=float, shape=(len(self.event_types), len(self.train_devices) + 1))

        return matrix.transpose().tocsr()

    @staticmethod
    def _check_matrix_vector_equal(recommendation_vector, recommendation_matrix):
        for i in range(len(recommendation_vector)):
            if recommendation_vector[i][0] != recommendation_matrix[i][0]:
                return False
        return True

    def recommend(self, test_device_events, tips):
        logging.info("BayesianPersonalizedRanking: matrix data computed, recommend started")

        test_vector = self.test_events_to_matrix(test_device_events)
        #test_matrix = self._generate_test_matrix(test_device_events)

        recommendation_vector = self.model.recommend(0, test_vector, N=len(self.event_types), recalculate_user=True)

      #  recommendation_matrix = self.model.recommend(len(self.device_to_index.keys()), test_matrix, N=len(self.event_types), recalculate_user=True)

       # if not self._check_matrix_vector_equal(recommendation_vector, recommendation_matrix):
       #     logging.error("MATRIX VECTOR DOES NOT MATCH")
       #     logging.info(recommendation_vector)
       #     logging.info(recommendation_matrix)

        logging.info("BayesianPersonalizedRanking: model recommend")
        recommendation_list = []
        for event, _ in recommendation_vector:
            if event_to_tips(self.event_types[event]) and\
                    _is_intersection(tips, event_to_tips(self.event_types[event])) > 0 and \
                    self.event_types[event] not in test_device_events:
                for tip in event_to_tips(self.event_types[event]):
                    if tip in tips:
                        recommendation_list.append(tip)
        return recommendation_list
