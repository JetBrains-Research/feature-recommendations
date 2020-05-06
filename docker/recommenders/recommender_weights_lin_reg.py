import logging
import operator
from tqdm import tqdm
from sklearn.linear_model import LinearRegression


from recommenders.recommender import Recommender
from util import _is_intersection

from recommenders.recommender_weights_base import RecommenderWeightsBase

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


class RecommenderWeightsLinear(RecommenderWeightsBase):
    def train(self):
        X = []
        y = []

        print(self.recommend_input_done)

        for device_id in tqdm(self.recommend_input_done.keys()):
            test_device_events, tips = self.recommend_input_done[device_id]
            recommendations = {}
            for i in range(len(self.algorithms)):
                recommendations[i] = self.algorithms[i].recommend_with_scores(test_device_events, tips)
                recommendations[i] = Recommender.normalize(recommendations[i])
            print(recommendations[i])

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
            if cnt == 10:
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
        print(X)
        print(y)
        self.model.fit(X, y)

    def __init__(self, train_devices, event_types, train_events, is_logging=True):
        if is_logging:
            logging.info("RecommenderWeightsLinear:init: init started.")
        self.model = LinearRegression()

        super(RecommenderWeightsLinear, self).__init__(train_devices, event_types, train_events, is_logging)

        if self.is_logging:
            logging.info("RecommenderWeightsLinear: weights: " + str(self.model.coef_))

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
            logging.info(str(x_value) + " " + str(tip_to_score[tip]))

        logging.info(str(tip_to_score))

        sorted_tips = sorted(tip_to_score.items(), key=operator.itemgetter(1), reverse=True)

        logging.info(str(list(sorted_tips)))
        sorted_tips = [tip[0] for tip in sorted_tips]
        return list(sorted_tips)
