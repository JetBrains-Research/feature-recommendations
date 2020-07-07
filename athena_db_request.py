from pyathena import connect
import os
import shutil
from tqdm import tqdm
import csv

PATH = os.path.split(__file__)[0]
PER_DEVICE_LOG_DIR = PATH + "/per_device_per_month_logs/"
DEVICE_IDS_FILE = PATH + "/device_ids_06.csv"
DEVICE_IDS_DONE_FILE = PATH + "/device_ids_06_done.csv"


def device_query(month):
    return """
    select distinct device_id from fus_lion_v3_prod.fus_lion_v3_parquet_prod
    where date_year = '2020' and date_month = '""" + month + """'
    and recorder_code = 'FUS' and internal = false
    and ((group_id = 'ui.tips' and event_id = 'tip.shown'
    and (not json_extract_scalar(event_data, '$.algorithm') = 'validation.unmatched_rule')))
    """


def log_query(device_id, month):
    return """
    select * from fus_lion_v3_prod.fus_lion_v3_parquet_prod
    where
    date_year = '2020' and date_month = '""" + month + """'
    and device_id = '""" + device_id + """'
    and recorder_code = 'FUS' and internal = false
    and ((group_id = 'ui.tips' and event_id = 'tip.shown'
         and (not json_extract_scalar(event_data, '$.algorithm') = 'validation.unmatched_rule'))
    or (group_id = 'actions' and event_id = 'action.invoked' ))
    """


def get_cursor():
    return connect(s3_staging_dir='s3://fus-peacock-athena-query-results-prod',
                     region_name='eu-west-1',
                     profile_name='FUSUserDataS3Qa').cursor()


def generate_logs_per_user_per_month():
    if not os.path.isdir(PER_DEVICE_LOG_DIR):
        os.mkdir(PER_DEVICE_LOG_DIR)
    done_devices = {}
    with open(DEVICE_IDS_DONE_FILE, 'r') as fin:
        for line in fin:
            done_devices[line[:-1]] = True
    fin.close()
    print(done_devices)
    with open(DEVICE_IDS_FILE, 'r') as fin:
        for line in fin:
            device_id = line[1:-2]
            if device_id == 'device_id':
                continue
            if device_id in done_devices.keys():
                continue
            print(device_id)
            month = '06'
            cursor = get_cursor()
            query = log_query(device_id, month)
            cursor.execute(query)
            with open(PER_DEVICE_LOG_DIR + device_id + "_" + month + ".csv", 'w') as fout:
                csv_out = csv.writer(fout)
                for line in cursor:
                    csv_out.writerow(line)
            with open(DEVICE_IDS_DONE_FILE, 'a') as fout:
                fout.write(device_id + "\n")


if __name__ == '__main__':
    generate_logs_per_user_per_month()