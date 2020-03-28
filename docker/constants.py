from enum import Enum
import os
ACTION_INVOKED_GROUP = "actions.action.invoked"
TIPS_GROUP = "ui.tips.tip.shown"
FORGET_TIME_DAYS = 10


class Method(Enum):
    TOP = 0
    PROB = 1
    MATRIX = 2
    RANDOM_0 = 3
    RANDOM_1 = 4
    RANDOM_2 = 5
    RANDOM_3 = 6
    RANDOM_4 = 7


METHODS_CNT = 8

PATH = os.path.split(__file__)[0]
INPUT_FILE_NAME = PATH + '/resources/' + 'log_sample_with_answers.csv'
TIP_TO_EVENT_FILE_NAME = PATH + "/resources/html_to_action_id.csv"

PREDICTED_TIME_MILLIS = 2 * 60 * 60 * 1000
TRAIN_TIME_DAYS = 30
TRAIN_TIME_MILLIS = TRAIN_TIME_DAYS * 24 * 60 * 60 * 1000

TOP_MODEL_FILE = PATH + "/models/top.pickle"
PROB_MODEL_FILE = PATH + "/models/prob.pickle"
MATRIX_MODEL_FILE = PATH + "/models/matrix.pickle"
RANDOM_MODEL_FILE = PATH + "/models/random.pickle"

METHOD_TO_FILE_NAME = {
    Method.TOP: TOP_MODEL_FILE,
    Method.PROB: PROB_MODEL_FILE,
    Method.MATRIX: MATRIX_MODEL_FILE,
    Method.RANDOM_0: RANDOM_MODEL_FILE,
    Method.RANDOM_1: RANDOM_MODEL_FILE,
    Method.RANDOM_2: RANDOM_MODEL_FILE,
    Method.RANDOM_3: RANDOM_MODEL_FILE,
    Method.RANDOM_4: RANDOM_MODEL_FILE,
}
