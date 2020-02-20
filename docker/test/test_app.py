#!/usr/bin/env python
# coding: utf-8

# In[49]:


from tqdm import tqdm


# In[50]:


import os
import json
dir_name = "./test_events"
label_dir_name = "./test_labels"
file_names = os.listdir(dir_name)


# In[51]:


def read_user_events(file):
    with open("./test_events/" + file, 'r') as fin:
        data = json.load(fin)
        return data


# In[54]:


import requests
url = "http://0.0.0.0:5000/"

user_to_recommendation = {}

for file_name in tqdm(file_names):
    #print(file_name[:-4])
    if not (file_name[-5:] == '.json'):
        continue
    json_events = read_user_events(file_name)
    #print(json_events)
    r = requests.post(url, json=json_events)
    #print(r.text)
    user_to_recommendation[file_name[:-5]] = json.loads(str(r.text))
    #print(r.text)


# In[55]:


all_recommendations = {}
true_recommendations = {}

for file_name in tqdm(file_names):
    if not (file_name[-5:] == '.json'):
        continue
        
    recommended_event = user_to_recommendation[file_name[:-5]]["showingOrder"][0].split(",")
    algorithm = user_to_recommendation[file_name[:-5]]["usedAlgorithm"]
    if algorithm not in all_recommendations.keys():
        all_recommendations[algorithm] = 1
        true_recommendations[algorithm] = 0
    else:
        all_recommendations[algorithm] += 1

    for row in open(label_dir_name + "/" + file_name[:-5] + ".csv", 'r'):
        event = row[:-1].split(",")
        #print(str(event) + " " + str(recommended_event))
        if event[0] == recommended_event[0] and event[1] == recommended_event[1]:
            true_recommendations[algorithm] += 1
            break
    


# In[56]:


print("TOP: " + str(true_recommendations["TOP"] / all_recommendations["TOP"]))
print("PROB: " + str(true_recommendations["PROB"] / all_recommendations["PROB"]))
print("MATRIX: " + str(true_recommendations["MATRIX"] / all_recommendations["MATRIX"]))


# In[ ]:




