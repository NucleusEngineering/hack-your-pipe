# Activate

Data quality and infrastructure is key to make data useful. In the ingest and transform chapter we looked at how to collect, transport, transform and store data efficiently.

Once you have the data in the right quality and place you can start thinking about what to do with it.
Reporting in dashboards, advanced analytics or machine learning inference are just some examples of things that could be done. 

A common use case in the machine learning field is anomaly detection.

In this chapter you are going to train productionize an anomaly detection machine learning model.
As previously you will look at various sets of requirements and build efficient solutions for each of them.

## Set Google Cloud Project

Please make sure to start this challenge in a cleaned up GCP environment. (restart your lab)

Clone the github repo.
```
git clone https://github.com/NucleusEngineering/hack-your-pipe.git
```

Enter your GCP Project ID as `GCP_PROJECT` in `./config_env.sh` & set the environment variables.
```
source config_env.sh
```

Set default GCP Project
```
gcloud config set project $GCP_PROJECT
```

Set compute zone
```
gcloud config set compute/zone $GCP_REGION
```

Set your GCP project id in `./processing_service/config.py`.

Build pipeline service containers.
```
gcloud builds submit $RUN_PROXY_DIR --tag gcr.io/$GCP_PROJECT/pubsub-proxy
gcloud builds submit $RUN_PROCESSING_DIR --tag gcr.io/$GCP_PROJECT/data-processing-service
```

Set your GCP project id in `./terraform.tfvars`.

Create the PubSub Service Account. 
```
gcloud beta services identity create --project $GCP_PROJECT --service pubsub
```

Build Ingestion & Transformation Infrastructure via Terraform
```
terraform init
```

```
terraform apply -var-file terraform.tfvars
```

<!-- 
### Organizational Policies

Depending on the setup within your organization you might have to [overwrite some organizational policies](https://cloud.google.com/resource-manager/docs/organization-policy/creating-managing-policies#boolean_constraints) for the examples to run.

For example, the following policies should not be enforced. 

```
constraints/sql.restrictAuthorizedNetworks
constraints/compute.vmExternalIpAccess
constraints/compute.requireShieldedVm
constraints/storage.uniformBucketLevelAccess
constraints/iam.allowedPolicyMemberDomains
``` -->


### Make some data for the ML models

Update the `ENDPOINT_URL` with the pubsub-proxy Cloud Run endpoint in the `config_env.sh` and run `source config_env.sh` again. Then run the simulation for minimum 5 minutes.

```
python3 ./datalayer/synth_data_stream.py --endpoint=$ENDPOINT_URL
```

## Challenge 0: Architecture

Before starting into the building, think about how you are envisioning the solution architecture.
Based on the datapipeline you already implemented we are looking for ways to train an ML model, save and version it, deploy it to an API and ideally orchestrate and automat the entire process.

With your current GCP and non-GCP knowledge, how would your solution architecture approximately look like?

<details><summary>Suggested Solution</summary>

We suggest using:
* [BigQuery ML](https://cloud.google.com/bigquery-ml/docs/introduction#:~:text=BigQuery%20ML%20lets%20you%20create,the%20need%20to%20move%20data.) and/or [Vertex Custom Model Training](https://cloud.google.com/vertex-ai/docs/training/understanding-training-service) for model training
* [Vertex AI Model Registry](https://cloud.google.com/vertex-ai/docs/model-registry/introduction) to save and version the trained models
* [Vertex AI Endpoints](https://cloud.google.com/vertex-ai/docs/predictions/overview#get_predictions_from_custom_trained_models) to deploy your model to an API 
* [Vertex AI Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines/introduction) to orchestrate the training and deployment process 

The solution you will develop in the following will look something like this:

![Hack Your Pipe architecture](../../rsc/hyp_ml_architecture.png)

</details>


## Challenge 1: BigQuery ML Training

In your GCP console, go to BigQuery and look at your `ecommerce_sink.cloud_run` table. 

Train BigQuery ML clustering model to identify anomalies within in the `purchase` events.

Check here if you need a brushup in [Clustering](https://developers.google.com/machine-learning/clustering/overview).

<details><summary>Hint</summary>

The [BigQuery ML k-means](https://cloud.google.com/bigquery-ml/docs/reference/standard-sql/bigqueryml-syntax-create-kmeans) implementation would be a great fit for this challenge.

To decide on some of the crucial hyperparameters such as `NUM_CLUSTERS` [take a deeper look at the purchase value data distribution](https://cloud.google.com/bigquery/docs/visualize-looker-studio).

</details>

<details><summary>Suggested Solution</summary>

To detect the synthetic anomalies in the purchase data you should train the k-means clustering algorithm to detect two clusters.

[Enter the following query](https://cloud.google.com/bigquery-ml/docs/create-machine-learning-model) in the BigQuery console.

```
CREATE OR REPLACE MODEL
  `<project-id>.ecommerce_sink.anomaly_detection`
OPTIONS
  ( MODEL_REGISTRY = 'VERTEX_AI',
    MODEL_TYPE='KMEANS',
    NUM_CLUSTERS=2 ) AS
  SELECT
    ecommerce.purchase.tax AS tax,
    ecommerce.purchase.shipping AS shipping,
    ecommerce.purchase.value AS value
  FROM `<project-id>.ecommerce_sink.cloud_run` 
  WHERE event='purchase'
;
```
The query will train the BQML model and automatically register it in the Vertex AI Model Registry for versioning and deployment.

</details>


## Challenge 2: Endpoint Creation

create an endpoint

<details><summary>Hint</summary>

Check the docs how to create a model endpoint through the [Console](https://cloud.google.com/vertex-ai/docs/tabular-data/classification-regression/get-online-predictions#google-cloud-console), [CLI](https://cloud.google.com/sdk/gcloud/reference/ai/endpoints/create) or [programmatically](https://cloud.google.com/vertex-ai/docs/samples/aiplatform-create-endpoint-sample).

</details>

<details><summary>Suggested Solution</summary>

Run the following command to create a model endpoint in Vertex.

```
gcloud ai endpoints create \
    --project=$GCP_PROJECT \
    --region=$GCP_REGION \
    --display-name=my_hyp_endpoint
```

</details>


## Challenge 3: Model deployment

Before moving on make sure that you can find your trained BQML model in the [Vertex Model Registry](https://cloud.google.com/vertex-ai/docs/model-registry/introduction).

If so, deploy the trained and saved model to the Vertex Endpoint you just created.

<details><summary>Hint</summary>

Check the docs how to create a model endpoint through the [Console](https://cloud.google.com/vertex-ai/docs/tabular-data/classification-regression/get-online-predictions#deploy-model), [CLI](https://cloud.google.com/sdk/gcloud/reference/ai/endpoints/deploy-model) or [programmatically](https://cloud.google.com/vertex-ai/docs/samples/aiplatform-deploy-model-sample).

</details>

<details><summary>Suggested Solution</summary>

To deploy your model run the following command. 

```
gcloud ai endpoints deploy-model <endpoint-id> \
    --project=$GCP_PROJECT \
    --region=$GCP_REGION \
    --model=anomaly_detection \
    --display-name=anomaly_detection
```

</details>

## Challenge 4: Inference Pipeline

Now that your model is deployed and ready to make predictions you will include it into your Cloud Run processing pipeline.

First create a BigQuery table named `bq_table_run_anomaly` and the schema `tax:FLOAT, shipping:FLOAT, value:FLOAT, anomaly:BOOL` as prediction destination.

<details><summary>Hint</summary>

[bq mk documentation](https://cloud.google.com/bigquery/docs/reference/bq-cli-reference#bq_mk)

</details>


<details><summary>Suggested Solution</summary>
To create the BigQuery destination table run.

```
bq mk --location=europe-west1 -t $GCP_PROJECT:ecommerce_sink.cloud_run_anomaly tax:FLOAT,shipping:FLOAT,value:FLOAT,anomaly:BOOL
```

</details>


`21_challenge/inf_processing_service` is the template for your adapted inference processing container.
However, the file is missing some code snippets.

Finish coding up the inference processing service. Don't forget to adjust the configuration.

<details><summary>Hint</summary>

Check the docs for
* [AI Platform SDK initialization](https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform#google_cloud_aiplatform_init)
* [Endpoint definition](https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform.Endpoint)
* [Calling endpoint for prediction](https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform.Endpoint#google_cloud_aiplatform_Endpoint_predict)
* [BigQuery Insert](https://cloud.google.com/python/docs/reference/bigquery/latest)

</details>

<details><summary>Suggested Solution</summary>

Adjust the project-id and endpoint_id in `./inf_processing_service/config.py`.

You can find the correct endpoint id on the Vertex AI page under Endpoints.

AI Platform SDK initialization
```
aiplatform.init(project=config.project_id, location=config.location)
```

Endpoint definition
```
endpoint = aiplatform.Endpoint(
    endpoint_name=f"projects/{config.project_id}/locations/{config.location}/endpoints/{config.endpoint_id}",
    project = config.project_id,
    location=config.location,
    )
```

Calling endpoint for prediction
```
endpoint_response = endpoint.predict(
    instances=record_to_predict
)
```

BigQuery insert
```
client = bigquery.Client(project=config.project_id, location=config.location)
table_id = config.project_id + '.' + config.bq_dataset + '.' + config.bq_table_anomaly
errors_an = client.insert_rows_json(table_id, rows_to_insert)  # Make an API request.
```

Build Container
```
gcloud builds submit $RUN_INFERENCE_PROCESSING_SERVICE --tag gcr.io/$GCP_PROJECT/inference-processing-service
```

```
gcloud run deploy hyp-run-service-data-processing --image=gcr.io/$GCP_PROJECT/inference-processing-service:latest --region=$GCP_REGION
```

</details>


## Challenge 5: Custom Model Training

### 5.1. Preparation

Let's imagine that once you find a sufficient anomaly detection split with K-Means clustering, you'd like to build a custom [classification model](https://developers.google.com/machine-learning/glossary#binary-classification) on your now labeled historical dataset, so that you can start classifying anomalies arising in the new data coming in. 
Your explanatory variables will be `tax`, `shipping` and `value` and you will try to predict if the anomaly is `true` or `false`.

For this exercise, save your labelled historical data as a table called `anomaly_data` in BigQuery, resembling the table you created in Challenge 4 to capture data.

<details><summary>Hint</summary>

Here's an [example](https://cloud.google.com/bigquery-ml/docs/linear-regression-tutorial#step_five_use_your_model_to_predict_outcomes).

```
CREATE TABLE
    ecommerce_sink.anomaly_data AS (
SELECT
    ("<substitute with query that takes TRUE value when the CENTROID_ID = 1, FALSE otherwise>") AS anomaly,
    tax,
    shipping,
    value
FROM
    ML.PREDICT(MODEL <full path model_id>,
    (
    SELECT
        ecommerce.purchase.tax AS tax,
        ecommerce.purchase.shipping AS shipping,
        ecommerce.purchase.value AS value
    FROM
        `<project_id>.ecommerce_sink.cloud_run`
    WHERE
        event='purchase') ) )
;
```

</details>

<details><summary>Suggested Solution</summary>

```
CREATE TABLE
    ecommerce_sink.anomaly_data AS (
SELECT
    (CASE
        WHEN CENTROID_ID = 1 THEN TRUE
    ELSE
    FALSE
    END
    ) AS anomaly,
    tax,
    shipping,
    value
FROM
    ML.PREDICT(MODEL `<project_id>.ecommerce_sink.anomaly_detection`,
    (
    SELECT
        ecommerce.purchase.tax AS tax,
        ecommerce.purchase.shipping AS shipping,
        ecommerce.purchase.value AS value
    FROM
        `<project_id>.ecommerce_sink.cloud_run`
    WHERE
        event='purchase') ) )
;
```
</details>

You will use this data to train a custom classifier model that will allow you to find anomalies in incoming new data points. 

Create a bucket called `$GCP_PROJECT-ai-bucket` for custom training artifacts that Vertex aI will store later.

<details><summary>Hint</summary>

[CLI-link](https://cloud.google.com/storage/docs/gsutil/commands/mb)

</details>

<details><summary>Suggested Solution</summary>

```
gsutil mb -l $GCP_REGION gs://$GCP_PROJECT-ai-bucket
```

</details>

### 5.2. Creating custom training and prediction containers

We start by preparing the code to create custom training and prediction containers.
Containers are providing you a way to write your own preferred data processing and model training with your preferred library and environment.
Inspect the provided code in in the `custom_train` folder.

Start by updating the `project_id` in the `custom_train/trainer/config.py` and `custom_train/prediction/config.py` files.

You will need to complete the code by filling in the missing snippets (3 altogether, 2 in training, 1 in prediction) in the `custom_train/trainer/train.py`, `custom_train/trainer/main.py` and `custom_train/prediction/main.py` files.

<details><summary>Hint 1 - Custom training</summary>

Use the [scikit-learn documentation](https://scikit-learn.org/stable/modules/tree.html#classification).

</details>

<details><summary>Suggested Solution 1 - Custom training</summary>

```
# Define and train the Scikit model
skmodel = DecisionTreeClassifier()
skmodel.fit(data, labels)
```

</details>

<details><summary>Hint 2 - Custom training</summary>

Find the model training function in the `custom_train/trainer/train.py` file and call it with the arguments.

</details>

<details><summary>Suggested Solution 2 - Custom training</summary>

```
train.train_model(train_data, train_labels, test_data, test_labels, storage_client)
```

</details>

</details>

<details><summary>Hint 3 - Custom prediction</summary>

Use the [scikit-learn documentation](https://scikit-learn.org/stable/modules/tree.html#classification).

</details>

<details><summary>Suggested Solution 3 - Custom prediction</summary>

```
outputs = model.predict(instances)
```

</details>

Build the custom train and prediction container images.

<details><summary>Hint</summary>

You can use the [gcloud builds submit](https://cloud.google.com/sdk/gcloud/reference/builds/submit) command.

</details>

<details><summary>Suggested Solution</summary>

```
gcloud builds submit custom_train/trainer/. --tag $TRAIN_IMAGE_URI
```
```
gcloud builds submit  custom_train/prediction/. --tag $PREDICT_IMAGE_URI 
```

</details>

### 5.3. Creating the pipeline

Now, you will create a [training pipeline](https://cloud.google.com/vertex-ai/docs/training/create-training-pipeline) in Vertex AI, using code and the containers you created.
The files `kf_pipe_custom.py` and `config_custom.py` are prepared for you with 4 snippets to fix.

Running this pipeline will run the sequence of Model training (custom) > Import custom prediction container > Upload the model into the model registry > Creating an endpoint > Deploying the model on the endpoint.

<details><summary>Hint 1</summary>

Look into the [job component](https://cloud.google.com/vertex-ai/docs/pipelines/customjob-component#customjobop) that gives full functionalities.

</details>

<details><summary>Suggested Solution 1</summary>

```
train_job = CustomTrainingJobOp(
            display_name="pipeline-anomaly-custom-train",
            project=project_id,
            location=region,
            worker_pool_specs=WORKER_POOL_SPECS
        )
```

</details>

<details><summary>Hints 2 - 4</summary>

Find the relevant operators in the [documentation](https://cloud.google.com/vertex-ai/docs/pipelines/model-endpoint-component).

</details>

<details><summary>Suggested Solution 2</summary>

```
custom_model_upload_job = gcc_aip.ModelUploadOp(
            project=project_id,
            location=region,
            display_name=f"anomaly-detection-custom-model_{timestamp_id}",
            unmanaged_container_model=import_unmanaged_model_op.outputs["artifact"],
            ).after(import_unmanaged_model_op)
```

</details>

<details><summary>Suggested Solution 3</summary>

```
# Create an endpoint where the model will be deployed
        endpoint_create_job = gcc_aip.EndpointCreateOp(
            project=project_id,
            display_name="anomaly-detection-custom-endpoint",
            location=region
        )
```

</details>

<details><summary>Suggested Solution 4</summary>

```
# Deploy the model on the endpoint
        _ = gcc_aip.ModelDeployOp(
            model=custom_model_upload_job.outputs["model"],
            endpoint=endpoint_create_job.outputs["endpoint"],
            deployed_model_display_name="anomaly-detection-custom-deploy",
            dedicated_resources_min_replica_count=1,
            dedicated_resources_max_replica_count=1,
            dedicated_resources_machine_type="n1-standard-2",
            traffic_split={"0": 100}
        )
```

</details>

Once you finished the code, install the dependencies, then run it:

```
pip install -r ./requirements.txt
```

```
python3 kf_pipe_custom.py
```

It can take up to 15-20 minutes for the pipeline to compile and start running.

You can monitor your pipeline on the link you receive in the terminal after running the pipeline code.


## Challenge 6: Custom Model Inference

Create a new BigQuery destination table, as you did earlier, but this time let's call it `bq_table_run_anomaly_custom`.

```
bq mk --location=europe-west1 -t $GCP_PROJECT:ecommerce_sink.bq_table_run_anomaly_custom tax:FLOAT,shipping:FLOAT,value:FLOAT,anomaly:BOOL
```

Connect custom model inference into the data processing pipeline (see `inf_processing_service_custom`).

<details><summary>Hint</summary>

Find the endpoint id of your custom model, and fill it in `inf_processing_service_custom/config.py` together with your project id.
Then build the container and deploy it on Cloud Run.

</details>

<details><summary>Suggested Solution</summary>

Find the endpoint id of your custom model

```
gcloud ai endpoints list
```

Build the container, and deploy on Cloud Run 

```
gcloud builds submit $RUN_INFERENCE_PROCESSING_SERVICE_CUSTOM --tag gcr.io/$GCP_PROJECT/inference-processing-service-custom
```

```
gcloud run deploy hyp-run-service-data-processing-custom --image=gcr.io/$GCP_PROJECT/inference-processing-service-custom:latest --region=$GCP_REGION
```

</details>

## Challenge 7: Testing the inference pipelines

Now that both models are deployed and connected into the respective inference pipelines, run the streaming data simulation again, and check your destination tables in BigQuery, to see if you are receiving data with the anomaly classifications.

```
python3 ./datalayer/synth_data_stream.py --endpoint=$ENDPOINT_URL
```
