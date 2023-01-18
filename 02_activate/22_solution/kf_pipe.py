import time
from typing import Iterable, Dict, NamedTuple

import config

# import kfp
from kfp.v2 import compiler, dsl
from kfp.v2.dsl import component
import google.cloud.aiplatform as aip
from google_cloud_pipeline_components import aiplatform as gcc_aip

from google_cloud_pipeline_components.v1 import endpoint 
from google_cloud_pipeline_components.types.artifact_types import VertexModel, VertexEndpoint, UnmanagedContainerModel


# TODO: Check for resources & create if needed before pipeline

def compile_pipe():
    # Define the workflow of the pipeline.
    @dsl.pipeline(
        name="anomaly-detection-test",
        pipeline_root=config.PIPELINE_ROOT_PATH)

    def pipeline(project_id: str, region: str, timestamp_id: str):

        # Import Dataset
        # dataset = dsl.importer(
        #     artifact_uri=f"bq://{project_id}.ecommerce_sink.cloud_run",
        #     artifact_class=dsl.Dataset)
        
        # Train BQ Model

        # Train Custom Model

        # Get endpoint through sdk.
        # endpoint = aip.Endpoint(endpoint_name="test_endpoint2")

        aip.init(project=config.GCP_PROJECT, location=config.GCP_REGION)

        endpoint_uri = "https://europe-west1-aiplatform.googleapis.com/v1/projects/79712439873/locations/europe-west1/endpoints/5981396031659573248"
        endpoint = dsl.importer(
            artifact_uri=endpoint_uri,
            artifact_class=VertexEndpoint,
                metadata={
                "resourceName": "projects/79712439873/locations/europe-west1/endpoints/5981396031659573248"
            }
          )
        
        # Model Import
        # model = dsl.importer(
        #     artifact_uri=f"anomaly_detection2",
        #     artifact_class=dsl.Model)
        
        model_uri = "gs://poerschmann-hyp-test2/cloud_trained_model/anomaly_detection2/"
        model = dsl.importer(
            artifact_uri=model_uri,
            artifact_class=VertexModel
          )

        # Deploy models on endpoint
        model_deploy_op = gcc_aip.ModelDeployOp(
            model=model.output,
            endpoint=endpoint.output,
            automatic_resources_min_replica_count=1,
            automatic_resources_max_replica_count=1
        )

    compiler.Compiler().compile(pipeline_func=pipeline, package_path="hyp-anomaly-detection.json")


if __name__ == "__main__":
    # Initialize aiplatform credentials.
    aip.init(project=config.GCP_PROJECT, location=config.GCP_REGION)

    # Compile pipeline code.
    compile_pipe()

    # Unique ident for pipeline run
    timestamp_id = str(int(time.time()))

    # Prepare the pipeline job.
    job = aip.PipelineJob(
        display_name=f"{timestamp_id}-hyp-anomaly-detection",
        template_path="hyp-anomaly-detection.json",
        pipeline_root=config.PIPELINE_ROOT_PATH,
        parameter_values={
            'project_id': config.GCP_PROJECT,
            'region': config.GCP_REGION,
            'timestamp_id': timestamp_id
        }
    )

    job.submit(service_account=config.SERVICE_ACCOUNT)
