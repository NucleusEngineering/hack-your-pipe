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


from fastapi import Request, FastAPI
import json
import os
from joblib import load
import sys
import pandas as pd
from google.cloud import storage
from tempfile import TemporaryFile
import os
import config

app = FastAPI()

model_directory = f"{os.environ['AIP_STORAGE_URI']}/model_dir"
storage_path = os.path.join(model_directory, "model.joblib")

storage_client = storage.Client(project=config.PROJECT_ID)
blob = storage.blob.Blob.from_string(storage_path, client=storage_client)

blob.download_to_filename("model.joblib")
model =load(open("model.joblib",'rb'))

@app.get('/')
def get_root():
    return {'message': 'Welcome to custom anomaly detection'}

@app.get('/health_check')
def health():
    return 200

if os.environ.get('AIP_PREDICT_ROUTE') is not None:
    method = os.environ['AIP_PREDICT_ROUTE']
else:
    method = '/predict'

@app.post(method)
async def predict(request: Request):
    print("----------------- PREDICTING -----------------")
    body = await request.json()
    # prepare data
    instances = pd.DataFrame(body["instances"])
    
    # retrieving predictions
    outputs = "<3. add the code that predicts anomalies, using the model, and the input from the app>"
    
    response = outputs.tolist()
    print("----------------- OUTPUTS -----------------")
    return {"predictions": response}