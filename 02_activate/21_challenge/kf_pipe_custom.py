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

import time
from typing import Iterable, Dict, NamedTuple

import config_custom

# import kfp
from kfp.v2 import compiler, dsl
from kfp.v2.dsl import component
from kfp.v2.components import importer_node
import google.cloud.aiplatform as aip
from google_cloud_pipeline_components import aiplatform as gcc_aip

from google_cloud_pipeline_components.types import artifact_types
from google_cloud_pipeline_components.v1.custom_job import CustomTrainingJobOp

## Training Worker Specs
WORKER_POOL_SPECS = [
    {
        "machine_spec": {
            "machine_type": "n1-standard-4"
        },
        "replica_count": "1",
        "container_spec": {
            "image_uri": config_custom.TRAIN_IMAGE_URI,
            "env": [
                {
                    "name": "AIP_STORAGE_URI",
                    "value": config_custom.AIP_STORAGE_URI
                },
            ]
        }
    }
]

def compile_pipe():
    # Define the workflow of the pipeline.
    @dsl.pipeline(
        name="anomaly-detection-custom-test",
        pipeline_root=config_custom.PIPELINE_ROOT_PATH)

    def pipeline(
        project_id: str, 
        region: str, 
        timestamp_id: str, 
        artifact_staging_location:str,
        bq_source: str,
        aip_storage_uri: str,
        predict_image_uri: str
        ):
        
        # Model training
        train_job = '<1. Add the training job with a display name, project, location and worker pool defined.>'

        # Model evaluation
        # Ideally here you can evaluate the model and decide on deployment/or not for CI/CD purposes
        # example: https://www.cloudskillsboost.google/focuses/21234?parent=catalog

        # Import with the custom predict container
        import_unmanaged_model_op = importer_node.importer(
            artifact_uri=aip_storage_uri,
            artifact_class=artifact_types.UnmanagedContainerModel,
            metadata={
                "containerSpec": {
                    "imageUri": predict_image_uri,
                    "env": [
                        {
                            "name": "PROJECT_ID",
                            "value": project_id},
                    ],
                    "predictRoute": "/predict",
                    "healthRoute": "/health_check",
                    "ports": [
                        {
                            "containerPort": 8080
                        }
                    ]
                },
            },
        ).after(train_job)
        
        # Upload the model into the registry
        custom_model_upload_job = gcc_aip.'<. Find the correct operator>'(
            project=project_id,
            location=region,
            display_name=f"anomaly-detection-custom-model_{timestamp_id}",
            unmanaged_container_model=import_unmanaged_model_op.outputs["artifact"],
            ).after(import_unmanaged_model_op)
        
        # Create an endpoint where the model will be deployed
        endpoint_create_job = gcc_aip.'<3. Find the correct operator>'(
            project=project_id,
            display_name="anomaly-detection-custom-endpoint",
            location=region
        )

        # Deploy the model on the endpoint
        _ = gcc_aip.'<4. Find the correct operator>'(
            model=custom_model_upload_job.outputs["model"],
            endpoint=endpoint_create_job.outputs["endpoint"],
            deployed_model_display_name="anomaly-detection-custom-deploy",
            dedicated_resources_min_replica_count=1,
            dedicated_resources_max_replica_count=1,
            dedicated_resources_machine_type="n1-standard-2",
            traffic_split={"0": 100}
        )
        
    compiler.Compiler().compile(pipeline_func=pipeline, package_path="hyp-custom-anomaly-detection.json")

if __name__ == "__main__":
    # Initialize aiplatform credentials.
    aip.init(project=config_custom.PROJECT_ID, location=config_custom.REGION)

    # Compile pipeline code.
    compile_pipe()

    # Unique ident for pipeline run
    timestamp_id = str(int(time.time()))

    # Prepare the pipeline job.
    job = aip.PipelineJob(
        display_name=f"{timestamp_id}-hyp-custom-anomaly-detection",
        template_path="hyp-custom-anomaly-detection.json",
        pipeline_root=config_custom.PIPELINE_ROOT_PATH,
        parameter_values={
            'project_id': config_custom.PROJECT_ID,
            'region': config_custom.REGION,
            'timestamp_id': timestamp_id,
            'bq_source': config_custom.DATA_URI,
            'aip_storage_uri' : config_custom.AIP_STORAGE_URI,
            'predict_image_uri' : config_custom.PREDICT_IMAGE_URI,
            'artifact_staging_location': config_custom.PIPELINE_ROOT_PATH
        }
    )

    job.submit(service_account=config_custom.SERVICE_ACCOUNT)
