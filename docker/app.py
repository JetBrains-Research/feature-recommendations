#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import csv
import numpy as np
from tqdm import tqdm
import operator
from scipy.sparse import csr_matrix
from sklearn.decomposition import NMF
from scipy.sparse.linalg import svds
import random
import logging
logging.basicConfig(filename="recommendations.log", level=logging.INFO)
import json


# In[2]:


INPUT_FILE_NAME = 'log_sample.csv'
PREDICTED_TIME_MILLIS = 10 * 60 * 60 * 1000
TRAIN_TIME_DAYS = 30
FORGET_TIME_DAYS = 10


# In[3]:


def tip_to_event(tip):
    return tip
    
def event_to_tip(event):
    return event


# In[45]:


class ReadEvents:
    def __init__(self, input_file_name, predicted_time_millis, train_time_days):
        self.input_file_name = input_file_name
        self.predicted_time = predicted_time_millis
        self.train_time = train_time_days * 24 * 60 * 60 * 1000
    
    def read_events_from_file(self):
        def check_group_event_id(group_id, event_id):
            return group_id not in ('performance', 'vcs.change.reminder') and                    event_id not in ('ui.lagging',
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

        self.train_device_ids = list(devices.keys())
        
        logging.info(str(len(devices.keys())) + " devices found.")
        logging.info(str(len(list(event_types.keys()))) + " event types found.")
        
        self.event_types = list(event_types.keys())
        self.events = events
    
    def filter_train_events(self):
        #remove old events
        device_to_max_timestamp = {}
        
        for event in tqdm(self.events):
            device_id, group_id, event_id, timestamp, count = event
            
            if device_id not in device_to_max_timestamp.keys():
                device_to_max_timestamp[device_id] = timestamp
            else:
                device_to_max_timestamp[device_id] = max(device_to_max_timestamp[device_id], timestamp)
        
        self.train_events = {} #group_id, event_id, device_id --> last timestamp and count
    
        for event in tqdm(self.events):
            device_id, group_id, event_id, timestamp, count = event
            max_timestamp = device_to_max_timestamp[device_id]
            
            threshold = max_timestamp - self.train_time
            if timestamp >= threshold:
                if (device_id, group_id, event_id) in self.train_events.keys():
                    _, prev_count = self.train_events[(device_id, group_id, event_id)]
                    self.train_events[(device_id, group_id, event_id)] = (max_timestamp, prev_count + count)
                else:
                    self.train_events[(device_id, group_id, event_id)] = (max_timestamp, count)

    def read_user_events(self, data):
        user_events = {}
        tips = []
        for tip in data["tips"]:
            group_id, event_id = tip.split(",")
            tips.append((group_id, event_id))
            
        for event in data["usageInfo"].keys():
            group_id, event_id = event.split(",")
            last_timestamp = data["usageInfo"][event]["lastUsedTimestamp"]
            count = data["usageInfo"][event]["usageCount"]
            user_events[(group_id, event_id)] = (last_timestamp, count)
        
        return user_events, tips


# In[46]:


events_reader = ReadEvents(INPUT_FILE_NAME, PREDICTED_TIME_MILLIS, TRAIN_TIME_DAYS)


# In[47]:


events_reader.read_events_from_file()


# In[48]:


events_reader.filter_train_events()


# In[49]:


class Recommender:  
    def __init__(self, train_devices, event_types, train_events):
        self.train_devices = train_devices
        self.event_types = event_types
        self.train_events = train_events

    def recommend(self, test_device_events, tips):
        pass


# In[50]:


class RecommenderTopEvent(Recommender):
    def get_top_events(self):
        event_to_count = {}
        logging.info("RecommenderTopEvent: generating top events started.")
        for (device_id, group_id, event_id) in tqdm(self.train_events.keys()):
            _, cnt = self.train_events[(device_id, group_id, event_id)]
            if (group_id, event_id) in event_to_count.keys():
                event_to_count[(group_id, event_id)] = event_to_count[(group_id, event_id)] + cnt
            else:
                event_to_count[(group_id, event_id)] = cnt
        
        logging.info("RecommenderTopEvent: event_to_count computed.")
        sorted_by_count_events = sorted(event_to_count.items(), key=operator.itemgetter(1), reverse=True)
        
        all_count_sum = 0
        for event_count in sorted_by_count_events:
            all_count_sum += event_count[1]
            
        logging.info("RecommenderTopEvent: event_to_count sorted, events top list received.")
        
        self.top_events = [(x[0], x[1] / all_count_sum) for x in sorted_by_count_events]  

    def __init__(self, train_devices, event_types, train_events):
        
        logging.info("RecommenderTopEvent: started.")
        super(RecommenderTopEvent, self).__init__(train_devices, event_types, train_events)
        self.get_top_events()
    
    def recommend(self, test_device_events, tips):
        logging.info("RecommenderTopEvent: recommendation started.")
        
        for i in range(len(self.top_events)):
            top_event = self.top_events[i][0]
            
            if not top_event in test_device_events.keys() and event_to_tip(top_event) and event_to_tip(top_event) in tips:
                logging.info("RecommenderTopEvent: recommendation made.")
                return event_to_tip(top_event)
        
        logging.info("RecommenderTopEvent: recommendation made.")
        return event_to_tip(self.top_events[0][0])
    


# In[ ]:





# In[63]:


class RecommenderTopEventWithProbability(RecommenderTopEvent):
    def recommend(self, test_device_events, tips):
        
        not_done_event_with_prob = {}
        all_not_done_top_sum = 0
        logging.info("RecommenderTopEventWithProbability: recommendation started.")
        for i in range(len(self.top_events)):
            top_event = self.top_events[i]
            if not top_event[0] in test_device_events.keys() and event_to_tip(top_event[0]) and event_to_tip(top_event[0]) in tips:
                not_done_event_with_prob[top_event] = True
                all_not_done_top_sum += top_event[1]
        
        logging.info("RecommenderTopEventWithProbability: not_done_events computed")  
        not_done_event_with_prob = list(not_done_event_with_prob.keys())
        probs = []
        for i in range(len(not_done_event_with_prob)):
            probs.append(not_done_event_with_prob[i][1] / all_not_done_top_sum)
        
        logging.info("RecommenderTopEventWithProbability: probability for not_done_events computed")  
        
        return event_to_tip(not_done_event_with_prob[np.random.choice(len(not_done_event_with_prob), 1, probs)[0]][0])  
    


# In[64]:


import implicit


# In[65]:


TEST_USER_ID = -1


# In[66]:


class BayesianPersonalizedRanking(Recommender):  
    def __init__(self, train_devices, event_types, train_events):
        super(BayesianPersonalizedRanking, self).__init__(train_devices, event_types, train_events)
        
        logging.info("BayesianPersonalizedRanking: init started")
        self.device_to_index = {}
        for i in range(len(train_devices)):
            self.device_to_index[train_devices[i]] = i
            
        self.event_to_index = {}
        for i in range(len(self.event_types)):
            self.event_to_index[self.event_types[i]] = i
        
        logging.info("BayesianPersonalizedRanking: device_to_index and event_to_index computed")
         
        data = []
        row_id = []
        col_id = []
        row_col = {}
        for event in train_events.keys():
            (device_id, group_id, event_id) = event
            if (self.device_to_index[device_id], self.event_to_index[(group_id, event_id)]) not in row_col.keys():
                data.append(1)
                row_id.append(self.device_to_index[device_id])
                col_id.append(self.event_to_index[(group_id, event_id)])
                row_col[(self.device_to_index[device_id], self.event_to_index[(group_id, event_id)])] = True
        
        logging.info("BayesianPersonalizedRanking: matrix data computed")
        
        self.matrix = csr_matrix((np.array(data), (np.array(row_id), np.array(col_id))), dtype=float, shape=(len(train_devices), len(self.event_types)))
        logging.info("BayesianPersonalizedRanking: matrix generated")
        
        self.model = implicit.bpr.BayesianPersonalizedRanking(factors=50)
        self.model.fit(self.matrix, show_progress=True)
        logging.info("BayesianPersonalizedRanking: model fit")
    
    

    def recommend(self, test_device_events, tips):
        logging.info("BayesianPersonalizedRanking: matrix data computedrecommend started")
        user_items = self.matrix.T.tocsr()
        recommendation = self.model.recommend(self.device_to_index[TEST_USER_ID], user_items, N=len(self.event_types))
        logging.info("BayesianPersonalizedRanking: model recommend")
        for event, _ in recommendation:
            if event_to_tip(self.event_types[event]) and event_to_tip(self.event_types[event]) in tips:
                if self.event_types[event] not in test_device_events:
                    return event_to_tip(self.event_types[event])
        return event_to_tip(self.event_types[recommendation[0][0]])

from enum import Enum


# In[68]:


class Method(Enum):
    TOP = 0
    MATRIX = 1
    PROB = 2


# In[ ]:





# In[ ]:

import os
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
import time

UPLOAD_FOLDER = '.'
global current_method, methods_cnt
current_method = 0
methods_cnt = 3

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

global algorithmTop
algorithmTop = RecommenderTopEvent(events_reader.train_device_ids, events_reader.event_types, events_reader.train_events)
global algorithmProb
algorithmProb = RecommenderTopEventWithProbability(events_reader.train_device_ids, events_reader.event_types, events_reader.train_events)

            

@app.route('/', methods=['POST'])
def do_recomendation():
    global current_method, methods_cnt, algorithmTop, algorithmProb
    #print(current_method)
    method = Method(current_method).name
    content = request.get_json()
    device_id = TEST_USER_ID
    if content:
        start = time.time()
        logging.info("Recomendation process started.")
        user_events, tips = events_reader.read_user_events(content)
        logging.info("User events and tips read.")
        if method == 'TOP':
            logging.info("TOP recommender started")
            recommendation = algorithmTop.recommend(user_events, tips)
            logging.info("TOP recommender done")
        if method == 'PROB':
            logging.info("PROB recommender started")
            recommendation = algorithmProb.recommend(user_events, tips)
            logging.info("PROB recommender done")
        if method == 'MATRIX':
            logging.info("MATRIX recommender started")
            all_events = events_reader.train_events.copy()
            for (group_id, event_id) in user_events.keys():
                all_events[device_id, group_id, event_id] = (1, 1)
            all_devices = events_reader.train_device_ids.copy()
            all_devices.append(device_id)
            logging.info("MATRIX all_events computed")
            algorithmMatrix = BayesianPersonalizedRanking(all_devices, events_reader.event_types,all_events)
            logging.info("MATRIX algorithm generated")
            recommendation = algorithmMatrix.recommend([], tips)
            logging.info("MATRIX recommender done")
        logging.info("Recommendation process done")
        end = time.time()
        logging.info("TIME: " + str(end - start))
    data = {}
    logging.info("RECOMMENDATION MADE: " + str(recommendation[0]) + "," + str(recommendation[1]))
    data["showingOrder"] = [str(recommendation[0]) + "," + str(recommendation[1])]
    data["usedAlgorithm"] = Method(current_method).name
    current_method = (current_method + 1) % methods_cnt
    return data


@app.route('/hell', methods=['GET'])
def hell():
    return "Hello World!! (Docker)"

if __name__ == '__main__':
    app.run(host='0.0.0.0')

