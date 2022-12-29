import os
import time
import base64
import json

import numpy as np
import pandas as pd

from flask import Flask, request, jsonify

from google.cloud import bigquery

app = Flask(__name__)


@app.route("/hw", methods=['GET', 'POST'])
def hello_world():
    world = request.args.get('world')
    return f"Hello {world}!"


@app.route("/", methods=["POST"])
def index():
    envelope = request.get_json()
    print(envelope)
    print(type(envelope))


    if not envelope:
        msg = "no Pub/Sub message received"
        print(f"error: {msg}")
        return f"Bad Request: {msg}", 400

    ps_message = envelope['message']
    print(ps_message)
    print(type(ps_message))

    record = base64.b64decode(ps_message["data"]).decode("utf-8").strip()
    record = json.loads(record)

    print(record)
    print(type(record))

    rows_to_insert = [record]


    client = bigquery.Client(project='poerschmann-hackyourpipe', location='europe-west1')
    table_id = "poerschmann-hackyourpipe.retail_dataset.ecomm_events_run"

    errors = client.insert_rows_json(table_id, rows_to_insert)  # Make an API request.
    if errors == []:
        print(f"{time.time()} New rows have been added.")
        return ("", 204)
    else:
        print("Encountered errors while inserting rows: {}".format(errors))
        return f"Bad Request: {envelope}", 400

    # print(f"Hello {name}!")

    



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

