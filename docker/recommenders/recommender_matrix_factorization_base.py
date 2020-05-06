import logging
import numpy as np
from scipy.sparse import coo_matrix

from recommenders.recommender import Recommender
from util import _is_intersection
from reader import event_to_tips

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


class BaseMatrixRecommender(Recommender):
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

        logging.info("BaseMatrixRecommender: matrix data computed")

        matrix = coo_matrix((np.array(data), (np.array(row_id), np.array(col_id))),
                            dtype=float, shape=(len(self.event_types), len(self.train_devices)))
        return matrix

    def __init__(self, train_devices, event_types, train_events, model, model_name, is_logging):
        super(BaseMatrixRecommender, self).__init__(train_devices, event_types, train_events, is_logging)

        logging.info("BaseMatrixRecommender: init started")

        self._generate_indices()

        logging.info("BaseMatrixRecommender: device_to_index and event_to_index computed")

        self._generate_user_to_event_index()

        self.matrix = self._generate_matrix()
        logging.info("BaseMatrixRecommender: matrix generated")

        self.model = model
        self.model.fit(self.matrix, show_progress=True)
        logging.info("BaseMatrixRecommender: model " + model_name + " fit")

    def _generate_recommendation_list(self, recommendations, test_device_events, tips):
        recommendation_map = {}
        for event, score in recommendations:
            if event_to_tips(self.event_types[event][0], self.event_types[event][1]) and \
                    _is_intersection(tips, event_to_tips(self.event_types[event][0], self.event_types[event][1])) > 0 \
                    and self.event_types[event] not in test_device_events:
                for tip in event_to_tips(self.event_types[event][0], self.event_types[event][1]):
                    if tip in tips:
                        recommendation_map[tip] = max(0, score)
        return recommendation_map
