from enum import Enum

ACTION_INVOKED_GROUP = "actions.action.invoked"
FORGET_TIME_DAYS = 10


# TODO: add matrix method
class Method(Enum):
    TOP = 0
    PROB = 1


METHODS_CNT = 2

PATH = __file__[:-12]
INPUT_FILE_NAME = PATH + 'resources/' + 'log_sample_with_answers.csv'
TIP_TO_EVENT_FILE_NAME = PATH + "resources/html_to_action_id.csv"

PREDICTED_TIME_MILLIS = 10 * 60 * 60 * 1000
TRAIN_TIME_DAYS = 30
TRAIN_TIME_MILLIS = TRAIN_TIME_DAYS * 24 * 60 * 60 * 1000
