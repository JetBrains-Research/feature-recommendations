#!/usr/bin/env python
# coding: utf-8

from flask import Flask, request
import logging

import os

logging.basicConfig(filename="recommendations.log", level=logging.INFO, filemode='w')
logging.getLogger().addHandler(logging.StreamHandler())
logging.info("App started.")

import recommender_system
import reader
from constants import Method, METHODS_CNT

app = Flask(__name__)


@app.route('/', methods=['POST'])
def do_recommendation():
    content = request.get_json()
    logging.info(content)
    logging.info("JSON request received. ")

    bucket, user_events, tips = reader.read_request_json(content)
    logging.info("User events and tips read.")
    
    method_int = bucket % METHODS_CNT
    method = Method(method_int)
    logging.info("Current recommendation algorithm id: " + str(method.name))
    
    recommendation = recommender_system.recommend(user_events, tips, method)
    logging.info("Recommendation made: " + str(recommendation))

    data = {"showingOrder": recommendation,
            "usedAlgorithm": method.name}

    return data


@app.route('/hello', methods=['GET'])
def hello():
    return "Hello World!!!"


if __name__ == '__main__':
    app.run(host='0.0.0.0')
    logging.info("Recommendation service started.")

