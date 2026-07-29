The processing service defines a Cloud Run Service to process each incoming datapoint.


main.py defines the public facing webserver to listen for requests.

synth_data_stream.py creates a synthetic data stream of events randomly chosen from the datalayer. It also randomly includes anomalies in the data.


Command to start data stream:
python3 synth_data_stream.py --endpoint {Pub/Sub endpoint link}'