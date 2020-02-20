FROM python:3
ADD app.py /
ADD log_sample.csv /
RUN mkdir -p /test_labels
RUN mkdir -p /test_events
RUN pip install numpy
RUN pip install tqdm
RUN pip install scipy
RUN pip install sklearn
RUN pip install flask
RUN pip install implicit
ENTRYPOINT [ "python" ]
CMD [ "/app.py" ]