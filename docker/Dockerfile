FROM python:3
ADD app.py /
ADD recommenders /recommenders
ADD resources/ /resources
ADD reader.py /
ADD recommender_system.py /
ADD constants.py /
ADD requirements.txt /
RUN pip install -r requirements.txt
ENTRYPOINT [ "python" ]
CMD [ "/app.py" ]