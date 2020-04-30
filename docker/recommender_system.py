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
from recommenders.recommender_weights import RecommenderWeights

logging.basicConfig(filename="recommendations.log", level=logging.INFO)

METHOD_TO_CLASS = {
    Method.TOP: RecommenderTopEvent,
    Method.PROB: RecommenderTopEventWithProbability,
    Method.MATRIX_ALS: AlternatingLeastSquares,
    Method.WIDE: RecommenderWidelyUsed,
    Method.CODIS: RecommenderCoDis,
    Method.RANDOM: RecommenderRandom,
    Method.TOP_2: RecommenderTopEvent,
    Method.PROB_2: RecommenderTopEventWithProbability,
    Method.MATRIX_BPR: BayesianPersonalizedRanking,
    Method.WIDE_2: RecommenderWidelyUsed,
    Method.CODIS_2: RecommenderCoDis,
    Method.MATRIX_BPR_2: BayesianPersonalizedRanking,
    Method.WIDE_3: RecommenderWidelyUsed,
    Method.CODIS_3: RecommenderCoDis,
    Method.WEIGHTS: RecommenderRandom,  # Replace when weights are ready
    Method.WEIGHTS_2: RecommenderRandom  # Replace when weights are ready
}

is_trained = True
for i in range(METHODS_CNT):
    if Method(i) != Method.RANDOM and Method(i) != Method.WEIGHTS and Method(i) != Method.WEIGHTS_2 \
            and not os.path.isfile(METHOD_TO_FILE_NAME[Method(i)]):
        is_trained = False
        break

algorithms = {}

if not os.path.isdir("./models"):
    os.mkdir("./models")

if not is_trained:
    logging.info("Train data reading...")
    train_events, events_types, train_device_ids = reader.read_events_from_file()
    logging.info("Train data read.")

for i in range(METHODS_CNT):
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
    logging.info("Recommendation process done, TIME: " + str(end - start))

    return recommendation
