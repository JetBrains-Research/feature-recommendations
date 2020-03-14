import logging
import time

from recommenders.recommender_top_event import RecommenderTopEvent
from recommenders.recommender_top_event_with_probability import RecommenderTopEventWithProbability
from recommenders.recommender_matrix_factorization import BayesianPersonalizedRanking
import reader
from constants import Method, METHODS_CNT

logging.basicConfig(filename="recommendations.log", level=logging.INFO)

METHOD_TO_CLASS = {
    Method.TOP: RecommenderTopEvent,
    Method.PROB: RecommenderTopEventWithProbability,
    Method.MATRIX: BayesianPersonalizedRanking
}
logging.info("Train data reading...")
train_events, events_types, train_device_ids = reader.read_events_from_file()
logging.info("Train data read.")

algorithms = {}
for i in range(METHODS_CNT):
    algorithms[Method(i)] = METHOD_TO_CLASS[Method(i)](train_device_ids, events_types, train_events)
    logging.info("Algorithm " + str(Method(i).name) + " generated.")


def recommend(user_events, tips, method):
    start = time.time()
    logging.info("Recommendation process started.")

    recommendation = None

    if method in algorithms.keys():
        recommendation = algorithms[method].recommend(user_events, tips)
        logging.info(str(method.name) + " recommender done.")

    end = time.time()
    logging.info("Recommendation process done, TIME: " + str(end - start))
    return recommendation
