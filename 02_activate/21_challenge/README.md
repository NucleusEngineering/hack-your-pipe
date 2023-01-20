# Activate

Data quality and infrastructure is key to make data useful. In the ingest and transform chapter we looked at how to collect, transport, transform and store data efficiently.

Once you have the data in the right quality and place you can start thinking about what to do with it.
Reporting in dashboards, advanced analytics or machine learning inference are just some examples of things that could be done. 

A common use case in the machine learning field is anomaly detection.

In this chapter you are going to train productionize an anomaly detection machine learning model.
As previously you will look at various sets of requirements and build efficient solutions for each of them.

## Set-up Cloud Environment

### Initialize your account and project

If you are using the Google Cloud Shell you can skip this step.

```
gcloud init
```

### Set Google Cloud Project

```
export GCP_PROJECT=<project-id>
gcloud config set project $GCP_PROJECT
```

### Enable Google Cloud APIs

```
gcloud services enable aiplatform.googleapis.com storage.googleapis.com notebooks.googleapis.com dataflow.googleapis.com artifactregistry.googleapis.com 
```

### Set compute zone

```
gcloud config set compute/zone europe-west1
```

### Create a service account.
```
gcloud iam service-accounts create SA_NAME \
    --display-name="retailpipeline-hyp"
```

### ... with the necessary permissions.
```
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:retailpipeline-hyp@<project-id>.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

```

```
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:retailpipeline-hyp@<project-id>.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

```

```
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:retailpipeline-hyp@<project-id>.iam.gserviceaccount.com" \
    --role="roles/automl.serviceAgent"

```

### Organisational Policies

Depending on the setup within your organization you might have to [overwrite some organisational policies](https://cloud.google.com/resource-manager/docs/organization-policy/creating-managing-policies#boolean_constraints) for the examples to run.

For example, the following policies should not be enforced. 

```
constraints/sql.restrictAuthorizedNetworks
constraints/compute.vmExternalIpAccess
constraints/compute.requireShieldedVm
constraints/storage.uniformBucketLevelAccess
constraints/iam.allowedPolicyMemberDomains
```


## Challenge 0: Architecture

Before starting into the building, think about how you are envisioning the soltuion architecture.
Based on the datapipeline you alreadu implemented we are looking for ways to train an ML model, save and version it, deploy it to an API and ideally orchestrate and automat the entire process.

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
  `poerschmann-hyp-test2.ecommerce_sink.anomaly_detection`
OPTIONS
  ( MODEL_REGISTRY = 'VERTEX_AI',
    MODEL_TYPE='KMEANS',
    NUM_CLUSTERS=2 ) AS
  SELECT
    ecommerce.purchase.tax AS tax,
    ecommerce.purchase.shipping AS shipping,
    ecommerce.purchase.value AS value
  FROM `poerschmann-hyp-test2.ecommerce_sink.cloud_run` 
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
gcloud ai endpoints create
    --project=<project-id>
    --region=europe-west1
    --display-name=<endpoint-name>
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
gcloud ai endpoints deploy-model <model-name>
    --project=<project-id>
    --region=europe-west1
    --model=<model-id (numeric)>
    --display-name=<model-display-name (string)>
```

</details>


## Challenge 4: Inference Pipeline

Now that your model is deployed and ready to make predictions you will include it into your Cloud Run processing pipeline.

`21_challenge/inf_processing_service.py` is the template for your adapted inference processing container.
However, the file is missing some code snippets.

Finish coding up the inference processing service.

<details><summary>Hint</summary>

Check the docs for
* [aiplatform SDK initialization](https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform#google_cloud_aiplatform_init)
* [Endpoint definition](https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform.Endpoint)
* [Calling endpoint for prediction](https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform.Endpoint#google_cloud_aiplatform_Endpoint_predict)
* [BigQuery Insert](https://cloud.google.com/python/docs/reference/bigquery/latest)

</details>

<details><summary>Suggested Solution</summary>

Aiplatform SDK initialisation
```
aiplatform.init(project=config.project_id, location=config.location)
```

Endpoint definition
```
endpoint = aiplatform.Endpoint(
    endpoint_name=f"projects/{config.project_id}/locations/{config.location}/endpoints/{config.endpoind_id}",
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
export RUN_INFERENCE_PROCESSING_SERVICE=inf_processing_service
export GCP_PROJECT=poerschmann-hyp-test2
```



```
gcloud builds submit $RUN_INFERENCE_PROCESSING_SERVICE --tag gcr.io/$GCP_PROJECT/inference-processing-service
```

```
gcloud run deploy hyp-run-service-data-processing --image=gcr.io/poerschmann-hyp-test2/inference-processing-service:latest --region=europe-west1
```


</details>


## Challenge 5: Custom Model Training

Train custom model

<details><summary>Hint</summary>

Hint

</details>

<details><summary>Suggested Solution</summary>

Solution

</details>


## Challange 6: Custom Model Deployment

Deploy custom model

<details><summary>Hint</summary>

Hint

</details>

<details><summary>Suggested Solution</summary>

Solution

</details>


## Challenge 5: Custom Model Inference

Connect custom model inference to dataflow pipeline

<details><summary>Hint</summary>

Hint

</details>

<details><summary>Suggested Solution</summary>

Solution

</details>



<!-- TODO: Cloud Run model endpoint -->