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


PROJECT_ID="hyp-test-laurahp-03"
REGION="europe-west1"
AIP_STORAGE_URI=f'gs://{PROJECT_ID}-ai-bucket/vtx-artifacts'
# training data:
DATA_URI=f"{PROJECT_ID}.ecommerce_sink.anomaly_data"