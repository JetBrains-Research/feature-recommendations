import logging
import time
import os
import pickle
import random

from recommenders.recommender_top_event import RecommenderTopEvent
from recommenders.recommender_top_event_with_probability import RecommenderTopEventWithProbability
from recommenders.recommender_matrix_factorization import BayesianPersonalizedRanking
from recommenders.recommender_random import RecommenderRandom

import reader
from constants import Method, METHODS_CNT, METHOD_TO_FILE_NAME

logging.basicConfig(filename="recommendations.log", level=logging.INFO)

METHOD_TO_CLASS = {
    Method.TOP: RecommenderTopEvent,
    Method.PROB: RecommenderTopEventWithProbability,
    Method.MATRIX: BayesianPersonalizedRanking,
    Method.EMPTY_0: RecommenderRandom,
    Method.EMPTY_1: RecommenderRandom,
    Method.EMPTY_2: RecommenderRandom,
    Method.EMPTY_3: RecommenderRandom,
    Method.EMPTY_4: RecommenderRandom,
}

is_trained = True
for i in range(METHODS_CNT):
    if not os.path.isfile(METHOD_TO_FILE_NAME[Method(i)]):
        is_trained = False
        break

algorithms = {}

if not os.path.isdir("./models"):
    os.mkdir("./models")

if is_trained:
    for i in range(METHODS_CNT):
        with open(METHOD_TO_FILE_NAME[Method(i)], 'rb') as f:
            algorithms[Method(i)] = pickle.load(f)
        logging.info("Algorithm " + str(Method(i).name) + " loaded.")

else:
    logging.info("Train data reading...")
    train_events, events_types, train_device_ids = reader.read_events_from_file()
    logging.info("Train data read.")

    for i in range(METHODS_CNT):
        if os.path.isfile(METHOD_TO_FILE_NAME[Method(i)]):
            with open(METHOD_TO_FILE_NAME[Method(i)], 'rb') as f:
                algorithms[Method(i)] = pickle.load(f)
                logging.info("Algorithm " + str(Method(i).name) + " loaded.")
        else:
            algorithms[Method(i)] = METHOD_TO_CLASS[Method(i)](train_device_ids, events_types, train_events)
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
