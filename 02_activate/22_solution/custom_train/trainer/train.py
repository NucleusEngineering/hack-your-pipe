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

def train_model(data, labels, test_data, test_labels, storage_client):
    
    # Define and train the Scikit model
    skmodel = DecisionTreeClassifier()
    skmodel.fit(data, labels)
    score = skmodel.score(test_data, test_labels)
    print('accuracy is:',score)
    
    # Storage location
    model_directory = f"{os.environ['AIP_STORAGE_URI']}/model_dir"
    storage_path = os.path.join(model_directory, "model.joblib")

    # Save the model to a local file
    dump(skmodel, 'model.joblib')

    blob = storage.blob.Blob.from_string(storage_path, client=storage_client)
    blob.upload_from_filename("model.joblib")

    return(skmodel)