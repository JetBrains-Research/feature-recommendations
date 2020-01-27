FROM python:3
ADD test.py /
ADD log_sample_old.csv /
RUN mkdir -p /test_labels
RUN mkdir -p /test_events
RUN pip install numpy
RUN pip install tqdm
RUN pip install scipy
RUN pip install sklearn
RUN pip install flask
ENTRYPOINT [ "python" ]
CMD [ "/test.py" ]