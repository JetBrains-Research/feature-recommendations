FROM python:3
ADD app.py /
ADD recommenders /recommenders
ADD resources/ /resources
ADD reader.py /
ADD util.py /
ADD recommender_system.py /
ADD constants.py /
ADD requirements.txt /
COPY models/ /models
COPY test/test_events /test/test_events
COPY test/test_labels /test/test_labels
RUN pip install -r requirements.txt
ENTRYPOINT [ "python" ]
CMD [ "/app.py" ]
