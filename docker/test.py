#!/usr/bin/env python
# coding: utf-8

import csv
import numpy as np
from tqdm import tqdm
import operator
from scipy.sparse import csr_matrix
from sklearn.decomposition import NMF
from scipy.sparse.linalg import svds
import random

INPUT_FILE_NAME = 'log_sample_old.csv'
PREDICTED_TIME_MILLIS = 10 * 60 * 60 * 1000
TRAIN_TIME_DAYS = 30
FORGET_TIME_DAYS = 10
PRODUCTIVITY = "productivity"

class ReadEvents:
    def __init__(self, input_file_name, predicted_time_millis, train_time_days):
        self.input_file_name = input_file_name
        self.predicted_time = predicted_time_millis
        self.train_time = train_time_days * 24 * 60 * 60 * 1000
    
    def read_events_from_file(self):
        def check_group_event_id(group_id, event_id):
            return group_id not in ('performance', 'vcs.change.reminder') and event_id not in ('ui.lagging',
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
        
        events = []
        event_types = {}
        users = {}
        with open(self.input_file_name, 'r') as fin:
            isFisrt = True
            for row in tqdm(csv.reader(fin, delimiter=',')):
                if isFisrt:
                    isFisrt = False
                    continue
                count = row[12].split('.')[0]
                if count:
                    count = int(count)
                else:
                    count = 0
                
                group_id = row[5]
                event_id = row[10]
                timestamp = int(row[3])
                device_id = row[7]
                if count and check_group_event_id(group_id, event_id):
                    event_types[(group_id, event_id)] = True
                    users[device_id] = True
                    for i in range(count):
                        events.append((device_id, group_id, event_id, timestamp))
        
        self.train_users = list(users.keys())
        
        print(str(len(events)) + " event read.")
        print(str(len(self.train_users)) + " users found.")
        print(str(len(list(event_types.keys()))) + " event types found.")
        
        self.event_types = list(event_types.keys())
        self.events = events
    
    def split_test_users_events(self):
        user_to_max_time = {}
        
        for event in tqdm(self.events):
            device_id, group_id, event_id, timestamp = event
            if device_id not in user_to_max_time.keys():
                user_to_max_time[device_id] = timestamp
            else:
                user_to_max_time[device_id] = max(user_to_max_time[device_id], timestamp)
        
        self.train_events = {}
    
        for event in tqdm(self.events):
            device_id, group_id, event_id, timestamp = event
            max_time = user_to_max_time[device_id]
            if max_time - self.train_time <= timestamp:
                self.train_events[(device_id, group_id, event_id)] = True

        self.train_events = list(self.train_events.keys())

    def read_user_events(self, file):
        user_events = []
        for row in tqdm(file.readlines()):
            values = row.decode('ascii')[:-1].split(',')
            i = 0
            for i in range(0, len(self.event_types)):
                if values[i] == 1:
                    group_id, event_id = event_types[i]
                    user_events.append((group_id, event_id))
        return user_events

events_reader = ReadEvents(INPUT_FILE_NAME, PREDICTED_TIME_MILLIS, TRAIN_TIME_DAYS)

events_reader.read_events_from_file()
events_reader.split_test_users_events()


class Recommender:  
    def __init__(self, train_users, event_types, train_events):
        self.train_users = train_users
        self.event_types = event_types
        self.train_events = train_events

    def recommend(self, test_user, test_user_events):
        pass
    
    def recommend_list(self, test_users, test_users_events_dict):
        user_to_recomendation = {}
        
        for user in tqdm(test_users):
            user_to_recomendation[user] = self.recommend(user, test_users_events_dict[user])
        
        return user_to_recomendation

class RecommenderTopEvent(Recommender):
    def get_top_events(self):
        event_to_count = {}
        for (device_id, group_id, event_id) in tqdm(self.train_events):
            
            if group_id == PRODUCTIVITY:          
                if (group_id, event_id) in event_to_count.keys():
                    event_to_count[(group_id, event_id)] = event_to_count[(group_id, event_id)] + 1
                else:
                    event_to_count[(group_id, event_id)] = 1
        
        sorted_by_count_events = sorted(event_to_count.items(), key=operator.itemgetter(1), reverse=True)
        
        all_count_sum = 0
        for event_count in sorted_by_count_events:
            all_count_sum += event_count[1]
        
        self.top_events = [(x[0], x[1] / all_count_sum) for x in sorted_by_count_events]  

    def __init__(self, train_users, event_types, train_events):
        super(RecommenderTopEvent, self).__init__(train_users, event_types, train_events)
        self.get_top_events()
    
    def recommend(self, user, user_events):
        done_by_user_events = {}
        
        for (group_id, event_id) in user_events:
            done_by_user_events[(group_id, event_id)] = True

        for i in range(len(self.top_events)):
            top_event = self.top_events[i][0]
            
            if not top_event in done_by_user_events.keys():
                return top_event

        return self.top_events[0][0]

class RecommenderTopEventWithProbability(RecommenderTopEvent):
    def recommend(self, user, user_events):
        done_by_user_events = {}
        
        for (group_id, event_id) in user_events:
            done_by_user_events[(group_id, event_id)] = True
  
        not_done_event_with_prob = {}
        all_not_done_top_sum = 0
        for i in range(len(self.top_events)):
            top_event = self.top_events[i]
            if not top_event[0] in done_by_user_events.keys():
                not_done_event_with_prob[top_event] = True
                all_not_done_top_sum += top_event[1]
            
        not_done_event_with_prob = list(not_done_event_with_prob.keys())
        probs = []
        for i in range(len(not_done_event_with_prob)):
            probs.append(not_done_event_with_prob[i][1] / all_not_done_top_sum)
        
        return not_done_event_with_prob[np.random.choice(len(not_done_event_with_prob), 1, probs)[0]][0]  

class Recommendations:
    def __init__(self, algorithm, test_users, test_users_events_dict, test_labels):
        self.test_labels = test_labels
        self.user_to_recomendation = algorithm.recommend_list(test_users, test_users_events_dict)
    
    def get_recommendation(self):
        true_recommendations_cnt, all_recommendations_cnt = 0, len(list(self.user_to_recomendation.keys()))
        
        for user in self.user_to_recomendation.keys():
            group_id, event_id = self.user_to_recomendation[user]
            if group_id != PRODUCTIVITY:
                print(group_id)
            if (event_id) in self.test_labels[user]:
                true_recommendations_cnt += 1
        result = true_recommendations_cnt / all_recommendations_cnt
        print(str(result) + " predictions were correct.")
        return self.user_to_recomendation
        
    def __call__(self):
        return self.get_recommendation()

class MatrixFactorization(Recommender):  
    def __init__(self, users, event_types, events):
        super(MatrixFactorization, self).__init__(users, event_types, events)
        
        self.user_to_index = {}
        for i in range(len(users)):
            self.user_to_index[users[i]] = i
            
        self.event_to_index = {}
        for i in range(len(self.event_types)):
            self.event_to_index[self.event_types[i]] = i
         
        data = []
        row_id = []
        col_id = []
        row_col = {}
        for event in events:
            (device_id, group_id, event_id) = event
            if (self.user_to_index[device_id], self.event_to_index[(group_id, event_id)]) not in row_col.keys():
                data.append(1)
                row_id.append(self.user_to_index[device_id])
                col_id.append(self.event_to_index[(group_id, event_id)])
                row_col[(self.user_to_index[device_id], self.event_to_index[(group_id, event_id)])] = True
        
        self.matrix = csr_matrix((np.array(data), (np.array(row_id), np.array(col_id))), dtype=float, shape=(len(users), len(self.event_types)))
        u, s, vt = svds(self.matrix, k=2)
        self.predicted_matrix = np.dot(u, vt)
        

    def recommend(self, user, user_events):
        user_ind = self.user_to_index[user]
        user_values = self.predicted_matrix[user_ind]
        user_old_values = np.zeros(len(user_values))
        for (group_id, event_id) in user_events:
            user_old_values[self.event_to_index[(group_id, event_id)]] = 1
        
        diff_values = user_values - user_old_values
        for i in range(len(diff_values)):
            if user_old_values[i] > 0:
                diff_values[i] = 0
            if self.event_types[i][0] != PRODUCTIVITY:
                diff_values[i] = -1
        event_ind = np.argmax(diff_values)
        return self.event_types[event_ind]
                

from enum import Enum

class Method(Enum):
    TOP = 0
    MATRIX = 1
    PROB = 2


import os
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '.'
#global current_method, methods_cnt
current_method = 0
methods_cnt = 3

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#global user_to_recomendation, all_recomendations_dict, true_recomendations_dict
user_to_recomendation, all_recomendations_dict, true_recomendations_dict = {}, {}, {}
for i in range(methods_cnt):
    all_recomendations_dict[i] = 0
    true_recomendations_dict[i] = 0

@app.route('/', methods=['POST'])
def do_recomendation():
    global all_recomendations_dict, user_to_recomendation, current_method, methods_cnt
    method = Method(current_method).name
    file = request.files['file']
    device_id = request.form['device_id']
    if file:
        user_events = events_reader.read_user_events(file)
        if method == 'TOP':
            algorithm = RecommenderTopEvent(events_reader.train_users, events_reader.event_types, events_reader.train_events)
        if method == 'PROB':
            algorithm = RecommenderTopEventWithProbability(events_reader.train_users, events_reader.event_types, events_reader.train_events)
        if method == 'MATRIX':
            all_events = events_reader.train_events
            for (group_id, event_id, _, _) in user_events:
                all_events.append((device_id, group_id, event_id))

            all_users = events_reader.train_users
            all_users.append(device_id)
            algorithm = MatrixFactorization(all_users, events_reader.event_types, all_events)
        user_to_recomendation[device_id] = (algorithm.recommend(device_id, user_events)[1], current_method)
    current_method = (current_method + 1) % methods_cnt
    return str(user_to_recomendation[device_id][0])
        
    
@app.route('/test', methods=['POST'])
def test():
    global true_recomendations_dict, all_recomendations_dict, methods_cnt
    
    device_id = request.form['device_id']
    is_correct = request.form['is_correct']
    all_recomendations_dict[user_to_recomendation[device_id][1]] += 1
    if is_correct == 'True':
        true_recomendations_dict[user_to_recomendation[device_id][1]] += 1
    del user_to_recomendation[device_id]

    ans = ""
    for i in range(methods_cnt):
        if all_recomendations_dict[i] > 0:
            ans += str(Method(i).name) + ": " + str(true_recomendations_dict[i] / all_recomendations_dict[i]) + " "
    return ans


@app.route('/hell', methods=['GET'])
def hell():
    return "Hello World!! (Docker)"

if __name__ == '__main__':
    app.run(host='0.0.0.0')



