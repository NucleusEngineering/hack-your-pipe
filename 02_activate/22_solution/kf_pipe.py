import time
from typing import Iterable, Dict, NamedTuple

import config

# import kfp
from kfp.v2 import compiler, dsl
from kfp.v2.dsl import component
from kfp.v2.components import importer_node
import google.cloud.aiplatform as aip
from google_cloud_pipeline_components import aiplatform as gcc_aip

from google_cloud_pipeline_components.v1 import endpoint, bigquery
from google_cloud_pipeline_components.types.artifact_types import VertexModel, VertexEndpoint, UnmanagedContainerModel



# TODO: Check for resources & create if needed before pipeline

def compile_pipe():
    # Define the workflow of the pipeline.
    @dsl.pipeline(
        name="anomaly-detection-test",
        pipeline_root=config.PIPELINE_ROOT_PATH)

    def pipeline(project_id: str, region: str, timestamp_id: str, artifact_staging_location:str):

        aip.init(project=config.GCP_PROJECT, location=config.GCP_REGION)

        bqml_query = f"""
                CREATE OR REPLACE MODEL
                  `poerschmann-hyp-test2.ecommerce_sink.anomaly_detection`
                OPTIONS
                  ( MODEL_TYPE='KMEANS',
                    NUM_CLUSTERS=2 ) AS
                  SELECT
                    ecommerce.purchase.tax AS tax,
                    ecommerce.purchase.shipping AS shipping,
                    ecommerce.purchase.value AS value
                  FROM `poerschmann-hyp-test2.ecommerce_sink.cloud_run` 
                  WHERE event='purchase'
                ;
        """

        bqml_model = bigquery.BigqueryCreateModelJobOp(
            project=project_id,
            location=region,
            query=bqml_query
        )

        bq_export = bigquery.BigqueryExportModelJobOp(
            project=project_id,
            location=region,
            model=bqml_model.outputs["model"],
            model_destination_path=f"{config.PIPELINE_ROOT_PATH}/bq_model-artifacts"
        )

        import_unmanaged_model_task = importer_node.importer(
            artifact_uri=f"{config.PIPELINE_ROOT_PATH}/bq_model-artifacts",
            artifact_class=UnmanagedContainerModel,
            metadata={
                "containerSpec": {
                    "imageUri": "europe-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-9:latest",
                },
            },
        ).after(bq_export)

        model_upload = gcc_aip.ModelUploadOp(
            project=project_id,
            location=region,
            display_name=f"anomaly_detection_{timestamp_id}",
            unmanaged_container_model=import_unmanaged_model_task.output,
        )

        endpoint_uri = "https://europe-west1-aiplatform.googleapis.com/v1/projects/79712439873/locations/europe-west1/endpoints/5981396031659573248"
        endpoint = dsl.importer(
            artifact_uri=endpoint_uri,
            artifact_class=VertexEndpoint,
                metadata={
                "resourceName": "projects/79712439873/locations/europe-west1/endpoints/5981396031659573248"
            }
          )
          
        # Deploy models on endpoint
        _ = gcc_aip.ModelDeployOp(
            model=model_upload.outputs["model"],
            endpoint=endpoint.output,
            dedicated_resources_min_replica_count=1,
            dedicated_resources_max_replica_count=1,
            dedicated_resources_machine_type=config.MACHINE_TYPE,
            traffic_split={"0": 100}
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
            'timestamp_id': timestamp_id,
            'artifact_staging_location': config.PIPELINE_ROOT_PATH
        }
    )

    job.submit(service_account=config.SERVICE_ACCOUNT)
