from enum import Enum
import os

ACTION_INVOKED_GROUP = "actions.action.invoked"
TIPS_GROUP = "ui.tips.tip.shown"
FORGET_TIME_DAYS = 10


class Method(Enum):
    TOP = 0
    PROB = 1
    MATRIX = 2
    WIDE = 3
    CODIS = 4
    RANDOM = 5
    TOP_2 = 6
    PROB_2 = 7
    MATRIX_2 = 8
    WIDE_2 = 9
    CODIS_2 = 10
    RANDOM_2 = 11
    PROB_3 = 12
    MATRIX_3 = 13
    WIDE_3 = 14
    CODIS_3 = 15


METHODS_CNT = 16

PATH = os.path.split(__file__)[0]
INPUT_FILE_NAME = PATH + '/resources/' + 'new_mar_1.csv'
INPUT_FILE_NAME_TEST = PATH + '/resources/' + 'new_feb_03.csv'
TIP_TO_EVENT_FILE_NAME = PATH + "/resources/html_to_action_id.csv"

PREDICTED_TIME_MILLIS = 2 * 60 * 60 * 1000
TRAIN_TIME_DAYS = 30
TRAIN_TIME_MILLIS = TRAIN_TIME_DAYS * 24 * 60 * 60 * 1000

TOP_MODEL_FILE = PATH + "/models/top.pickle"
PROB_MODEL_FILE = PATH + "/models/prob.pickle"
MATRIX_MODEL_FILE = PATH + "/models/matrix.pickle"
RANDOM_MODEL_FILE = PATH + "/models/random.pickle"

WIDE_MODEL_FILE = PATH + "/models/wide.pickle"
CODIS_MODEL_FILE = PATH + "/models/codis.pickle"

METHOD_TO_FILE_NAME = {
    Method.TOP: TOP_MODEL_FILE,
    Method.PROB: PROB_MODEL_FILE,
    Method.MATRIX: MATRIX_MODEL_FILE,
    Method.WIDE: WIDE_MODEL_FILE,
    Method.CODIS: CODIS_MODEL_FILE,
    Method.RANDOM: RANDOM_MODEL_FILE,
    Method.TOP_2: TOP_MODEL_FILE,
    Method.PROB_2: PROB_MODEL_FILE,
    Method.MATRIX_2: MATRIX_MODEL_FILE,
    Method.WIDE_2: WIDE_MODEL_FILE,
    Method.CODIS_2: CODIS_MODEL_FILE,
    Method.RANDOM_2: RANDOM_MODEL_FILE,
    Method.PROB_3: PROB_MODEL_FILE,
    Method.MATRIX_3: MATRIX_MODEL_FILE,
    Method.WIDE_3: WIDE_MODEL_FILE,
    Method.CODIS_3: CODIS_MODEL_FILE,
}
