#!/bin/sh

export GCP_PROJECT="<project-id>"
export ENDPOINT_URL="<endpoint-url>" # doesn't need to be defined in the very beginning
export PUSH_ENDPOINT='<processing-endpoint-url>' # doesn't need to be defined in the very beginning
export GCP_REGION=europe-west1
export RUN_PROXY_DIR=cloud-run-pubsub-proxy
export RUN_PROCESSING_DIR=processing-service
export DATAFLOW_TEMPLATE=beam
export RUN_INFERENCE_PROCESSING_SERVICE=inf_processing_service

