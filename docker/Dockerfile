FROM python:3
ADD app.py /
ADD recommenders /recommenders
ADD resources/ /resources
ADD reader.py /
ADD recommender_system.py /
ADD constants.py /
RUN pip install numpy
RUN pip install tqdm
RUN pip install scipy
RUN pip install sklearn
RUN pip install flask
RUN pip install implicit
ENTRYPOINT [ "python" ]
CMD [ "/app.py" ]