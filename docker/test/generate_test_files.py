#!/usr/bin/env python
# coding: utf-8

# In[1]:


import csv
import numpy as np
from tqdm import tqdm
import operator
from scipy.sparse import csr_matrix
from sklearn.decomposition import NMF
from scipy.sparse.linalg import svds
import random
import json


# In[2]:


INPUT_FILE_NAME = '../log_sample.csv'
PREDICTED_TIME_MILLIS = 2 * 60 * 60 * 1000
TRAIN_TIME_DAYS = 30
FORGET_TIME_DAYS = 10


# In[3]:


def tip_to_action(tip):
    return tip
    
def action_to_tip(action):
    return action


# In[4]:


class ReadEvents:
    def __init__(self, input_file_name, predicted_time_millis, train_time_days):
        self.input_file_name = input_file_name
        self.predicted_time = predicted_time_millis
        self.train_time = train_time_days * 24 * 60 * 60 * 1000
    
    def read_events_from_file(self):
        def check_group_event_id(group_id, event_id):
                return group_id not in ('performance', 'vcs.change.reminder') and                        event_id not in ('ui.lagging',
                                        'ide.error',
                                        'ide.freeze',
                                        'ui.latency',
                                        'registered',
                                        'invoked',
                                        'TsLintLanguageService',
                                        'whitelist.updated',
                                        'logs.send',
                                        'notification.shown',
                                        'ESLintLanguageService')
        
        events = [] #all events from logs: group_id, event_id, device_id, last timestamp and count
        event_types = {} #(group_id, event_id) pairs
        devices = {} #device_id
        with open(self.input_file_name, 'r') as fin:
            is_fisrt = True
            for event_data in tqdm(csv.reader(fin, delimiter=',')):
                if is_fisrt:
                    #first row is a title
                    is_fisrt = False
                    continue
                count = event_data[12].split('.')[0]
                if count:
                    count = int(count)
                else:
                    count = 0
                
                group_id = event_data[5]
                event_id = event_data[10]
                if group_id == 'actions' and event_id == "action.invoked":
                   # print(event_id)
                    event_info = json.loads(event_data[11])
                    #print(event_info)
                    event_id += "." + event_info["action_id"]
                timestamp = int(event_data[3])
                device_id = event_data[7]
                
                if count and check_group_event_id(group_id, event_id):
                    event_types[(group_id, event_id)] = True
                    devices[device_id] = True
                    events.append((device_id, group_id, event_id, timestamp, count))
        
        devices = list(devices.keys())
        test_device_indexes = random.sample(range(len(devices)), len(devices) // 3)
        
        self.event_types = list(event_types.keys())
        self.events = events
        
        self.test_devices = list([devices[i] for i in test_device_indexes])
        self.event_types = list(event_types.keys())
        self.events = events
    
    def split_test_users_events(self):
        device_to_min_timestamp = {}
        device_to_max_timestamp = {}
        
        for event in tqdm(self.events):
            device_id, group_id, event_id, timestamp, count = event
            if device_id in self.test_devices:
                if device_id not in device_to_min_timestamp.keys():
                    device_to_min_timestamp[device_id] = timestamp
                else:
                    device_to_min_timestamp[device_id] = min(device_to_min_timestamp[device_id], timestamp)
            
                if device_id not in device_to_max_timestamp.keys():
                    device_to_max_timestamp[device_id] = timestamp
                else:
                    device_to_max_timestamp[device_id] = max(device_to_max_timestamp[device_id], timestamp)
        
        self.test_events = {}
        self.test_labels = {}
    
        for event in tqdm(self.events):
            device_id, group_id, event_id, timestamp, count = event
            if device_id in self.test_devices:
                min_timestamp = device_to_min_timestamp[device_id]
                max_timestamp = device_to_max_timestamp[device_id]
                
                if (max_timestamp - min_timestamp) < self.predicted_time:
                    continue
            
                if device_id not in self.test_events.keys():
                    self.test_events[device_id] = {}
                if device_id not in self.test_labels.keys():
                    self.test_labels[device_id] = {}
            
                threshold = max_timestamp - self.predicted_time
            
                if timestamp <= threshold:
                    if threshold - self.train_time <= timestamp:
                        if (group_id, event_id) in self.test_events[device_id].keys():
                            _, prev_count = self.test_events[device_id][(group_id, event_id)]
                            self.test_events[device_id][(group_id, event_id)] = (max_timestamp, prev_count + count)
                        else:
                            self.test_events[device_id][(group_id, event_id)] = (max_timestamp, count)
                else:
                    self.test_labels[device_id][(group_id, event_id)] = True

    def write_test_users(self):
        data = {}
        data["tips"] = []
        for elem in self.event_types:
            tip = action_to_tip(elem)
            if tip:
                data["tips"].append(tip[0] + "," + tip[1])
                #change when tip to action ready
        data["usageInfo"] = {}
        data["ideName"] = ""
        data["bucket"] = 0 #why do we need bucket?
        for device_id in self.test_events.keys():
            if (len(list(self.test_events[device_id]))) > 0:
                data["usageInfo"] = {}
                with open("./test_events/" + device_id + ".json", 'w') as fout:
                    for i in range(len(self.event_types)):
                        if self.event_types[i] in self.test_events[device_id].keys():
                            event = self.event_types[i]
                            max_timestamp, count = self.test_events[device_id][event]
                            data["usageInfo"][event[0] + "," + event[1]] = {}
                            data["usageInfo"][event[0] + "," + event[1]]["usageCount"] = count
                            data["usageInfo"][event[0] + "," + event[1]]["lastUsedTimestamp"] = max_timestamp
                    json.dump(data, fout)
                
                with open("./test_labels/" + device_id + ".csv", 'w') as fout:
                    for (group_id, event_id) in self.test_labels[device_id]:
                        fout.write(str(group_id) + "," + str(event_id) + "\n")   


# In[5]:


events_reader = ReadEvents(INPUT_FILE_NAME, PREDICTED_TIME_MILLIS, TRAIN_TIME_DAYS)


# In[6]:


events_reader.read_events_from_file()
events_reader.split_test_users_events()


# In[7]:


events_reader.write_test_users()


# In[ ]:





# In[ ]:




