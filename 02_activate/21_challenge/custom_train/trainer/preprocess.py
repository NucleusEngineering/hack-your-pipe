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

from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import roc_curve
from sklearn.model_selection import train_test_split
from google.cloud import bigquery
from google.cloud import storage
from joblib import dump

import os
import pandas as pd

def download_table(bqclient, storage_client, bq_table_uri: str):

    prefix = "bq://"
    if bq_table_uri.startswith(prefix):
        bq_table_uri = bq_table_uri[len(prefix):]

    table = bigquery.TableReference.from_string(bq_table_uri)
    rows = bqclient.list_rows(
        table,
    )
    return rows.to_dataframe(create_bqstorage_client=False)

def prep_data(bqclient, storage_client, data_uri: str):

    # Download data into Pandas DataFrames, split into train / test
    df, test_df = train_test_split(download_table(bqclient, storage_client, data_uri))
    labels = df.pop("anomaly").tolist()
    data = df.values.tolist()
    test_labels = test_df.pop("anomaly").tolist()
    test_data = test_df.values.tolist()

    return data, labels, test_data, test_labels