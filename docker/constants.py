from enum import Enum
import os

ACTION_INVOKED_GROUP = "actions.action.invoked"
TIPS_GROUP = "ui.tips.tip.shown"
FORGET_TIME_DAYS = 10


class Method(Enum):
    TOP = 0
    PROB = 1
    MATRIX_ALS = 2
    WIDE = 3
    CODIS = 4
    RANDOM = 5
    WEIGHTS_LIN_REG = 6
    PROB_2 = 7
    MATRIX_BPR = 8
    WIDE_2 = 9
    CODIS_2 = 10
    WEIGHTS_LIN_REG_2 = 11
    WEIGHTS_LIN_REG_3 = 12
    MATRIX_BPR_2 = 13
    WIDE_3 = 14
    CODIS_3 = 15


METHODS_CNT = 16

PATH = os.path.split(__file__)[0]
INPUT_FILE_NAME = PATH + '/resources/' + 'new_mar_2.csv'
TIP_TO_EVENT_FILE_NAME = PATH + "/resources/html_to_action_id.csv"

PREDICTED_TIME_MILLIS = 2 * 60 * 60 * 1000
TRAIN_TIME_DAYS = 30
TRAIN_TIME_MILLIS = TRAIN_TIME_DAYS * 24 * 60 * 60 * 1000

TOP_MODEL_FILE = PATH + "/models/top.pickle"
PROB_MODEL_FILE = PATH + "/models/prob.pickle"
MATRIX_ALS_MODEL_FILE = PATH + "/models/matrix_als.pickle"
MATRIX_BPR_MODEL_FILE = PATH + "/models/matrix_bpr.pickle"
RANDOM_MODEL_FILE = PATH + "/models/random.pickle"

WIDE_MODEL_FILE = PATH + "/models/wide.pickle"
CODIS_MODEL_FILE = PATH + "/models/codis.pickle"
WEIGHTS_MODEL_FILE = PATH + "/models/weights_complicated.pickle"
WEIGHTS_LIN_REG_FILE = PATH + "/models/weights_lin_reg.pickle"


METHOD_TO_FILE_NAME = {
    Method.TOP: TOP_MODEL_FILE,
    Method.PROB: PROB_MODEL_FILE,
    Method.MATRIX_ALS: MATRIX_ALS_MODEL_FILE,
    Method.WIDE: WIDE_MODEL_FILE,
    Method.CODIS: CODIS_MODEL_FILE,
    Method.RANDOM: RANDOM_MODEL_FILE,
    Method.WEIGHTS_LIN_REG: WEIGHTS_LIN_REG_FILE,
    Method.PROB_2: PROB_MODEL_FILE,
    Method.MATRIX_BPR: MATRIX_BPR_MODEL_FILE,
    Method.WIDE_2: WIDE_MODEL_FILE,
    Method.CODIS_2: CODIS_MODEL_FILE,
    Method.MATRIX_BPR_2: MATRIX_BPR_MODEL_FILE,
    Method.WIDE_3: WIDE_MODEL_FILE,
    Method.CODIS_3: CODIS_MODEL_FILE,
    Method.WEIGHTS_LIN_REG_2: WEIGHTS_LIN_REG_FILE,
    Method.WEIGHTS_LIN_REG_3: WEIGHTS_LIN_REG_FILE
}

LABELS_DATA_SOURCE = PATH + "/resources/labeled_data_source"
LABELS_DATA_SOURCE_FILES = os.listdir(LABELS_DATA_SOURCE)

TEST_EVENTS_DIR = PATH + "/resources/test_events"
TEST_EVENTS_DIR_FILES = os.listdir(TEST_EVENTS_DIR)
TRAIN_EVENTS_DIR = PATH + "/resources/train_events"
TRAIN_EVENTS_DIR_FILES = os.listdir(TRAIN_EVENTS_DIR)
TEST_LABELS_POSITIVE_DIR = PATH + "/resources/test_labels_positive"
TRAIN_LABELS_POSITIVE_DIR = PATH + "/resources/train_labels_positive"
TEST_LABELS_NEGATIVE_DIR = PATH + "/resources/test_labels_negative"
TRAIN_LABELS_NEGATIVE_DIR = PATH + "/resources/train_labels_negative"
