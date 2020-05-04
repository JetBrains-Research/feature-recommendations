import logging
from tqdm import tqdm
from recommenders.recommender import Recommender
from util import _is_intersection
import operator
from reader import event_to_tips

logging.basicConfig(filename="recommendations.log", level=logging.INFO)

SESSION_MINUTES = 60


def _build_cf_df(event_types, train_events):
    cf_matrix = {}
    df_matrix = {}
    for i in event_types:
        cf_matrix[i] = {}
        df_matrix[i] = {}
        for j in event_types:
            cf_matrix[i][j] = 0
            df_matrix[i][j] = 0

    for (device_id, group_id, event_id) in tqdm(train_events.keys()):
        timestamps, _ = train_events[(device_id, group_id, event_id)]
        for (device_id2, group_id2, event_id2) in train_events.keys():
            timestamps2, _ = train_events[(device_id2, group_id2, event_id2)]
            if device_id == device_id2 and (group_id != group_id2 or event_id != event_id2):
                i1 = 0
                i2 = 0
                while i1 < len(timestamps) and i2 < len(timestamps2):
                    time1 = timestamps[i1]
                    time2 = timestamps2[i2]
                    if SESSION_MINUTES * 60 * 1000 > time1 - time2 > - SESSION_MINUTES * 60 * 1000:
                        cf_matrix[(group_id, event_id)][(group_id2, event_id2)] += 1
                        cf_matrix[(group_id2, event_id2)][(group_id, event_id)] += 1
                        if time1 < time2:
                            df_matrix[(group_id, event_id)][(group_id2, event_id2)] += 1
                        else:
                            if time2 < time1:
                                df_matrix[(group_id2, event_id2)][(group_id, event_id)] += 1
                    if time1 < time2:
                        i1 += 1
                    else:
                        i2 += 1

    return cf_matrix, df_matrix


def _build_cp_dp(event_types, cf_matrix, df_matrix):
    cp_matrix = {}
    dp_matrix = {}
    for i in event_types:
        cp_matrix[i] = {}
        dp_matrix[i] = {}
        sum_cf = 0
        sum_df = 0
        for k in event_types:
            sum_cf += cf_matrix[i][k]
            sum_df += df_matrix[i][k]
        for j in event_types:
            if sum_cf > 0:
                cp_matrix[i][j] = cf_matrix[i][j] / sum_cf
            else:
                cp_matrix[i][j] = 0
            if sum_df > 0:
                dp_matrix[i][j] = df_matrix[i][j] / sum_df
            else:
                dp_matrix[i][j] = 0
    return cp_matrix, dp_matrix


def _get_last_session(test_device_events):
    max_time = None
    for (group_id, event_id) in test_device_events.keys():
        timestamp, count = test_device_events[(group_id, event_id)]
        if max_time is None or timestamp > max_time:
            max_time = timestamp

    last_session_events = {}
    for (group_id, event_id) in test_device_events.keys():
        timestamp, count = test_device_events[(group_id, event_id)]
        if max_time - timestamp < SESSION_MINUTES * 60 * 1000:
            last_session_events[(group_id, event_id)] = timestamp, count

    return last_session_events


class RecommenderCoDis(Recommender):
    def __init__(self, train_devices, event_types, train_events, is_logging=True):
        if is_logging:
            logging.info("RecommenderCo+Dis:init: init started.")
        super(RecommenderCoDis, self).__init__(train_devices, event_types, train_events, is_logging)
        cf_matrix, df_matrix = _build_cf_df(event_types, train_events)
        self.cp_matrix, self.dp_matrix = _build_cp_dp(event_types, cf_matrix, df_matrix)

    def recommend_with_scores(self, test_device_events, tips):
        last_session_events = _get_last_session(test_device_events)
        event_to_score = {}
        for (group_id, event_id) in self.event_types:
            event_to_score[(group_id, event_id)] = 0
            for (group_id2, event_id2) in last_session_events.keys():
                if (group_id2, event_id2) in self.cp_matrix[(group_id, event_id)].keys():
                    event_to_score[(group_id, event_id)] += self.cp_matrix[(group_id, event_id)][(group_id2, event_id2)]
                if (group_id2, event_id2) in self.dp_matrix.keys():
                    event_to_score[(group_id, event_id)] += self.dp_matrix[(group_id2, event_id2)][(group_id, event_id)]

        sorted_by_score_events = sorted(event_to_score.items(), key=operator.itemgetter(1), reverse=True)

        tips_to_recommend = {}

        for top_event in sorted_by_score_events:
            event = top_event[0]
            score = top_event[1]
            if (event not in test_device_events.keys()) \
                    and _is_intersection(tips, event_to_tips(event[0], event[1])) > 0:
                for tip in event_to_tips(event[0], event[1]):
                    if tip in tips:
                        tips_to_recommend[tip] = score

        if self.is_logging:
            logging.info("RecommenderCo+Dis:recommend: recommendation made.")
        return tips_to_recommend



