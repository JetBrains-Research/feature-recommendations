import logging
import operator
from tqdm import tqdm
from sklearn.linear_model import *


from recommenders.recommender import Recommender
from util import _is_intersection

from recommenders.recommender_weights_base import RecommenderWeightsBase

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


class RecommenderWeightsLinear(RecommenderWeightsBase):
    def train(self):
        X = []
        y = []

        for device_id in tqdm(self.recommend_input_done.keys()):
            test_device_events, tips = self.recommend_input_done[device_id]
            recommendations = {}
            for i in range(len(self.algorithms)):
                recommendations[i] = self.algorithms[i].recommend_with_scores(test_device_events, tips)
                recommendations[i] = Recommender.normalize(recommendations[i])

            for tip in tips:
                x_value = []
                for i in range(len(self.algorithms)):
                    if tip in recommendations[i].keys():
                        x_value.append(recommendations[i][tip])
                    else:
                        x_value.append(0)
                if _is_intersection(self.user_to_done_tips[device_id], [tip]):
                    X.append(x_value)
                    y.append(1)

        cnt = 0
        for device_id in tqdm(self.recommend_input_not_done.keys()):
            if cnt == 300:
                break
            cnt += 1
            test_device_events, tips = self.recommend_input_not_done[device_id]
            recommendations = {}
            for i in range(len(self.algorithms)):
                recommendations[i] = self.algorithms[i].recommend_with_scores(test_device_events, tips)
                recommendations[i] = Recommender.normalize(recommendations[i])

            for tip in tips:
                x_value = []
                for i in range(len(self.algorithms)):
                    if tip in recommendations[i].keys():
                        x_value.append(recommendations[i][tip])
                    else:
                        x_value.append(0)
                if _is_intersection(self.user_to_not_done_tips[device_id], [tip]):
                    X.append(x_value)
                    y.append(0)
        self.model.fit(X, y)

    def __init__(self, train_devices, event_types, train_events, is_logging=True):
        if is_logging:
            logging.info("RecommenderWeightsLinear:init: init started.")
        self.model = BayesianRidge()

        super(RecommenderWeightsLinear, self).__init__(train_devices, event_types, train_events, is_logging)

    def recommend(self, test_device_events, tips):
        recommendations = {}
        for i in range(len(self.algorithms)):
            recommendations[i] = self.algorithms[i].recommend_with_scores(test_device_events, tips)
            recommendations[i] = Recommender.normalize(recommendations[i])

        tip_to_score = {}
        for tip in tips:
            x_value = []
            for i in range(len(self.algorithms)):
                if tip in recommendations[i].keys():
                    x_value.append(recommendations[i][tip])
                else:
                    x_value.append(0)
            tip_to_score[tip] = self.model.predict([x_value])[0]

        sorted_tips = sorted(tip_to_score.items(), key=operator.itemgetter(1), reverse=True)

        sorted_tips = [tip[0] for tip in sorted_tips]
        return list(sorted_tips)
