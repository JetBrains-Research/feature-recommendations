#!/bin/bash
rm -rf test_events
rm -rf test_labels
mkdir test_events
mkdir test_labels
python3 generate_test_files.py
python3 test_app.py