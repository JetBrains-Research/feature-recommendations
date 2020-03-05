#!/usr/bin/env python
# coding: utf-8

from flask import Flask, request
import logging

import os


def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))


logging.basicConfig(filename="recommendations.log", level=logging.INFO, filemode='w')
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
    logging.info(f"Current recommendation algorithm id: {method.name}")
    
    recommendation = recommender_system.recommend(user_events, tips, method)
    logging.info(f"Recommendation made: {recommendation}")

    data = {"showingOrder": recommendation,
            "usedAlgorithm": method.name}

    return data


@app.route('/hello', methods=['GET'])
def hello():
    return "Hello World!!!"


if __name__ == '__main__':
    app.run(host='0.0.0.0')
    logging.info("Recommendation service started.")

