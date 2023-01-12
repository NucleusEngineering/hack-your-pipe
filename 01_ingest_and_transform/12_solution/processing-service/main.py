# Copyright 2023 Google

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import time
import base64
import json
import datetime
import config

from flask import Flask, request

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

    record = base64.b64decode(ps_message["data"]).decode("utf-8").strip()
    record = json.loads(record)

    record["weekday"] = datetime.datetime.strptime(record["event_datetime"], "%Y-%m-%d %H:%M:%S").strftime('%A')

    rows_to_insert = [record]

    client = bigquery.Client(project=config.project_id, location=config.location)
    table_id = config.project_id + '.' + config.bq_dataset + '.' + config.bq_table

    errors = client.insert_rows_json(table_id, rows_to_insert)  # Make an API request.
    if errors == []:
        print(f"{time.time()} New rows have been added.")
        return ("", 204)
    else:
        print("Encountered errors while inserting rows: {}".format(errors))
        return f"Bad Request: {envelope}", 400


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

