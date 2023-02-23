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

PROJECT_ID = os.environ['GCP_PROJECT']
REGION = os.environ['GCP_REGION']
PIPELINE_ROOT_PATH=f'gs://{PROJECT_ID}-ai-bucket/pipeline_root_custom/'

TRAIN_IMAGE_URI=os.environ['TRAIN_IMAGE_URI']
PREDICT_IMAGE_URI=os.environ['PREDICT_IMAGE_URI']
AIP_STORAGE_URI=f'gs://{PROJECT_ID}-ai-bucket/vtx-artifacts'

SERVICE_ACCOUNT=f"retailpipeline-hyp@{PROJECT_ID}.iam.gserviceaccount.com"
MACHINE_TYPE = "n1-standard-4"
DATA_URI=f"{PROJECT_ID}.ecommerce_sink.anomaly_data"