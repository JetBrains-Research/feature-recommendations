# Feature Recommendation Engine for IntelliJ IDEA	
## About the project
Integrated developer environments provide their users with many different features, but the developers usually know these features not well enough. To make developers more productive, they should be taught to use these features. IntelliJ IDEA provides a teaching mechanism called Tips of the Day. But this mechanism shows recommendations in random order and does not consider the individual needs of developers. In this work, we researched different recommendation algorithms, which allowed us to choose the best algorithms for improving Tips of the Day in IntelliJ IDEA. The result of this work is a recommender system implemented as an external web service, containing various algorithms, receiving requests from IntelliJ IDEA, and sending a sorted list of recommendations as a response. The service was evaluated on the test data collected from real  users, that allowed to compare the implemented algorithms.

## Usage
For algorithms' training we used IntelliJ IDEA users' logs. These logs are stored as a csv file. When reading the logs the relevant fields are parsed and not relevant are ignored. Please request the input file example if you need it.

The format example can be found in the table below. In this project not all the fields are used. We need only fields with names ```group_id```, ```event_id```, ```device_id```, ```event_data```, ```event_count```, ```time_epoch```, ```bucket``` and ```product_code```.

| country_code | internal | recorder_version | time_epoch | product_build| group_id | group_version | device_id | session_id | bucket | event_id | event_data | event_count | state| project_id| date_year| date_month| date_day | recorder_code | product_code | product_code | product_build |
| :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- |
| CN | False | 31 | 1577836800 | 193.5662.61 | ui.tips | 3 | 67890 | 11111 | 79 | dialog.shown |{""created"":1,""type"":""automatically""} | 1.0 | False | None | 2020 | 01 | 01 | FUS | PC | PC | 193.5662.61

One more example can be found in ```tst.csv``` file.

### Running the service
To run the implemented service the following steps should be done:
1. Put the input file with logs in ```docker/resources```
2. Change the ```INPUT_FILE_NAME``` value in ```docker/constants.py``` to match the input file name
3. Install the requirements from ```docker/requirements.txt```
4. Run ```docker/app.py```

For now 7 different algorithms are used to generate the recommendation. The service choose which algorithm to use depending on the ```bucket``` field, passed in request.

Alternatively, the service can be run without the input file. To do this it should have all the algorithms in a ```*.pickle``` files, in ```docker/models```.

Docker can be used too. After putting the input file or the ```*.pickle``` files two steps should be done:
1. ```docker image build -t recommendations .```
2. ```docker run -p 127.0.0.1:5000:5000 recommendations```

### Sending a request

The service should receive a JSON file as a request. JSON files examples can be found in ```docker/request_examples```.
The request example:

```
curl -X POST -H "Content-Type: application/json" -d @request_examples/request.json http://127.0.0.1:5000/tips/v1
```
where ```request.json``` is a JSON file name.

### Implemented algorithms
7 different algorithms are implemented:

1. Recommending the most popular tip
2. Recommending the random tip with the higher probability for more popular tips
3. Recommending most widely used tip
4. Matrix factorization with Alternating Least Squares
5. Matrix factorization with Bayesian Personalized Ranking
6. Co+Dis algorithm
7. Random recommendations

There is also implemented an algorithm, which assign weights to the algorithms above and then use linear regression to learn the weights. This algorithms is now testing, but you can try to use it. For this modify ```METHOD_TO_CLASS``` dictionary in ```docker/recommender_system.py```, to have ```Method.WEIGHTS_LIN_REG``` matching ```RecommenderWeightsLinear``` instead of ```RecommenderRandom```.

If you do not have a precomputed version of this algorithm (```weights_lin_reg.pickle```), you should have the extra input data. This data is generated from logs too, and used in testing. The information about how to generate this data can be found in the section below. 

### Additional input data

For testing and for weights learning you should have an additional data. This data contains the pairs (action history, tip), with the information about tip's relevance. With these pairs we can send the action history as a request and then check how far the tip is from the beginning and if the distance corresponds with tip's relevance.

These pairs are build from logs in the same format as in the input file below. The problem here was that only 0.004 tips in logs were relevant, so we have to process a bigger amount of logs to get more positive examples. 

To generate the pairs from logs the following steps should be done:
1. Put all the input files with logs (you can put more then 1, all will pe processed) in ```docker/resources/labeled_data_source```
2. Run ```docker/generate_labeled_test_files.py```

All the files will be generated and could be used after for testing or for learning weights. How to learn weight was described in a section above, no extra steps required after generating these files. How to run the testing is described below.

### Testing offline
The recommendation systems can be tested online and offline. Online testing is done on the real users after deployment. Offline testing is done with a test data. In this section offline testing is described. Some more information about online testing can be found in a next section.

In this work offline testing is done with the test files, which were described in a previous section. 7 different metrics are computed. To run the testihg there are three steps to follow:
1. Generate test files as described above.
2. Run the service as described above.
3. Run ```docker/test/test_app.py```

The results will be in stdout and will contain the metrics' values for all the implemented algorithms.

### Testing online

Online testing is done by processing the logs, collected after the deployment. The service returns the algorithm name in a response, and this name is written in logs to evaluate the algorithm by logs later.

Steps to run the online testing:
1. Put a file with logs for evaluation in root (```feature-recommendations```)
2. Modify ```INPUT_FILE_NAME``` in ```quality_evaluation.py``` to match the name of the file with logs to evaluate
3. Run ```quality_evaluation.py```
4. Sometimes it will not work. The problem found was that logs for evaluation have different format for some reasons. To try reading different formats modify ```is_eval``` parameter when calling ```read_events_raw``` from ```quality_evaluation.py```

### Some extra information from logs

In root you can find three more files:
1. ```actions_statistics.py``` can be used to find out if the popular events in different IDEs are the same
2. ```activity_period.ipynb``` is computing the average activity period, where activity period is a time period when user did some actions with an intervals less than 30 minutes between the actions
3. ```get_probability_to_remember.ipynb	``` is computing the probability for a user to remember the action if the used have not done the action for N days

We will not give the detailed description of these files, because they are not required for all the other parts. 
