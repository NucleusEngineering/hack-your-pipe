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

import preprocess
import train
import config

import os
import pandas as pd
import sys

# data uri
data_uri = config.DATA_URI

# bq client
bqclient = bigquery.Client(project=config.PROJECT_ID)
storage_client = storage.Client(project=config.PROJECT_ID)

## Download & prep data
print('[INFO] ------ Preparing Data', file=sys.stderr)
train_data, train_labels, test_data, test_labels = preprocess.prep_data(bqclient, storage_client, data_uri)

## Train model and save it in Google Cloud Storage
print('[INFO] ------ Training & Saving Model', file=sys.stderr)
train.train_model(train_data, train_labels, test_data, test_labels, storage_client)