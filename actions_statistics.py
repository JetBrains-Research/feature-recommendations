from tqdm import tqdm
import operator

from reader import read_events_raw, event_to_tips
from constants import INPUT_FILE_NAME, ACTION_INVOKED_GROUP


def _get_event_to_count(train_events):
    event_to_count = {}

    for (group_id, event_id, device_id, cnt) in tqdm(train_events):
        if (group_id, event_id) in event_to_count.keys():
            event_to_count[(group_id, event_id)] = event_to_count[(group_id, event_id)] + cnt
        else:
            event_to_count[(group_id, event_id)] = cnt
    return event_to_count


def _get_top_events(train_events):
    event_to_count = _get_event_to_count(train_events)

    sorted_by_count_events = sorted(event_to_count.items(), key=operator.itemgetter(1), reverse=True)

    all_count_sum = 0
    for event_count in sorted_by_count_events:
        all_count_sum += event_count[1]

    top_events = [x[0][1] for x in sorted_by_count_events]
    return top_events


def _split_events_by_ide(events):
    ide_to_events = {}
    for event in events:
        if ide not in ide_to_events.keys():
            ide_to_events[ide] = []
        if event.group_id == ACTION_INVOKED_GROUP and len(event_to_tips(event)) > 0:
            ide_to_events[ide].append((event.group_id, event.event_id, event.device_id, event.count))

    return ide_to_events


if __name__ == "__main__":
    events, event_types, devices = read_events_raw(INPUT_FILE_NAME)
    ide_to_events = _split_events_by_ide(events)
    ide_to_top = {}
    for ide in ide_to_events.keys():
        ide_to_top[ide] = _get_top_events(ide_to_events[ide])[:10]

    for ide in ide_to_top.keys():
        print(ide)
        print(ide_to_top[ide])
