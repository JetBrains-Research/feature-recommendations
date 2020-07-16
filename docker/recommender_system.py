import logging
import os
import pickle
import random
import time

import reader
from constants import Method, METHODS_CNT, METHOD_TO_FILE_NAME
from recommenders.recommender_als import AlternatingLeastSquares
from recommenders.recommender_bpr import BayesianPersonalizedRanking
from recommenders.recommender_codis import RecommenderCoDis
from recommenders.recommender_random import RecommenderRandom
from recommenders.recommender_top_event import RecommenderTopEvent
from recommenders.recommender_top_event_with_probability import RecommenderTopEventWithProbability
from recommenders.recommender_widely_used import RecommenderWidelyUsed
from recommenders.recommender_weights_lin_reg import RecommenderWeightsLinear
from recommenders.recommender_one_tip import RecommenderOneTip

logging.basicConfig(filename="recommendations.log", level=logging.INFO)


METHOD_TO_CLASS = {
    #Method.TOP: RecommenderTopEvent,
    #Method.PROB: RecommenderTopEventWithProbability,
    #Method.MATRIX_ALS: AlternatingLeastSquares,
    #Method.WIDE: RecommenderWidelyUsed,
    #Method.CODIS: RecommenderCoDis,
    #Method.RANDOM: RecommenderRandom,
    #Method.WEIGHTS_LIN_REG: RecommenderRandom,
    Method.ONE_TIP_SUMMER2020: RecommenderOneTip,
    #Method.MATRIX_BPR: BayesianPersonalizedRanking,
    #Method.WIDE_2: RecommenderWidelyUsed,
    #Method.CODIS_2: RecommenderCoDis,
    #Method.MATRIX_BPR_2: BayesianPersonalizedRanking,
    #Method.ONE_TIP_SUMMER2020_2: RecommenderOneTip,
    #Method.RANDOM_SUMMER2020_2: RecommenderRandom
    #Method.WEIGHTS_LIN_REG_2: RecommenderRandom,
    Method.RANDOM_SUMMER2020: RecommenderRandom
}

is_trained = True
#for i in range(METHODS_CNT):
#    if Method(i) != Method.RANDOM and Method(i) != Method.WEIGHTS_LIN_REG_2 and Method(i) != Method.RANDOM_SUMMER2020\
#         and Method(i) != Method.ONE_TIP_SUMMER2020 and Method(i) != Method.ONE_TIP_SUMMER2020_2 and\
#            Method(i) != Method.RANDOM_SUMMER2020_2\
#            and Method(i) != Method.WEIGHTS_LIN_REG\
#            and not os.path.isfile(METHOD_TO_FILE_NAME[Method(i)]):
#        is_trained = False
#        break

algorithms = {}

if not os.path.isdir("./models"):
    os.mkdir("./models")

if not is_trained:
    logging.info("Train data reading...")
    train_events, events_types, train_device_ids = reader.read_events_from_file()
    logging.info("Train data read.")

for i in range(METHODS_CNT):
    #if Method(i) == Method.CODIS_2:
    #    algorithms[Method(i)] = algorithms[Method.CODIS]
    #    continue
    #if Method(i) == Method.WEIGHTS_LIN_REG_2:
    #    algorithms[Method(i)] = algorithms[Method.WEIGHTS_LIN_REG]
    #    continue
    if os.path.isfile(METHOD_TO_FILE_NAME[Method(i)]):
        with open(METHOD_TO_FILE_NAME[Method(i)], 'rb') as f:
            algorithms[Method(i)] = pickle.load(f)
        logging.info("Algorithm " + str(Method(i).name) + " loaded.")
    else:
        if not is_trained:
            # noinspection PyUnboundLocalVariable
            algorithms[Method(i)] = METHOD_TO_CLASS[Method(i)](train_device_ids, events_types, train_events)
        else:
            algorithms[Method(i)] = METHOD_TO_CLASS[Method(i)](None, None, None)
        logging.info("Algorithm " + str(Method(i).name) + " generated.")
        with open(METHOD_TO_FILE_NAME[Method(i)], 'wb') as f:
            pickle.dump(algorithms[Method(i)], f)
            logging.info("Algorithm " + str(Method(i).name) + " saved.")

algo_to_average_time = {}
algo_to_request_cnt = {}
algo_to_min_time = {}
algo_to_max_time = {}
for i in range(METHODS_CNT):
    algo_to_average_time[Method(i)] = 0
    algo_to_request_cnt[Method(i)] = 0
    algo_to_max_time[Method(i)] = 0
    algo_to_min_time[Method(i)] = 100


def recommend(user_events, tips, method):
    start = time.time()
    logging.info("Recommendation process started.")

    recommendation = None

    if method in algorithms.keys():
        recommendation = algorithms[method].recommend(user_events, tips)
        logging.info(str(method.name) + " recommender done.")

    recommendation_set = set(recommendation)
    recommendation_unsorted = []
    if len(recommendation) != len(tips):
        for tip in tips:
            if tip not in recommendation_set:
                recommendation_unsorted.append(tip)
    random.shuffle(recommendation_unsorted)
    recommendation.extend(recommendation_unsorted)
    end = time.time()
    algo_to_average_time[method] += end - start
    algo_to_request_cnt[method] += 1
    algo_to_max_time[method] = max(end - start, algo_to_max_time[method])
    algo_to_min_time[method] = min(end - start, algo_to_min_time[method])
    logging.info("Recommendation process done, TIME: " + str(end - start))
    logging.info("Average time: " + str(algo_to_average_time[method] / algo_to_request_cnt[method]))
    logging.info("Max time: " + str(algo_to_max_time[method]))
    logging.info("Min time: " + str(algo_to_min_time[method]))

    return recommendation
