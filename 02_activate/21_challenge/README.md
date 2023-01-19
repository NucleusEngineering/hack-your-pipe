# Activate

Data quality and infrastructure is key to make data useful. In the ingest and transform chapter we looked at how to collect, transport, transform and store data efficiently.

Once you have the data in the right quality and place you can start thinking about what to do with it.
Reporting in dashboards, advanced analytics or machine learning inference are just some examples of things that could be done. 

A common use case in the machine learning field is anomaly detection.

In this chapter you are going to train productionize an anomaly detection machine learning model.
As previously you will look at various sets of requirements and build efficient solutions for each of them.

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

create a bigquery ml model per query & save it in model registry


<details><summary>Hint</summary>

Hint

</details>

<details><summary>Suggested Solution</summary>

Solution

</details>


## Challenge 2: Endpoint Creation

create an endpoint

<details><summary>Hint</summary>

Hint

</details>

<details><summary>Suggested Solution</summary>

Solution

</details>


## Challenge 3: Model deployment

deploy the created model to the endpoint


<details><summary>Hint</summary>

Hint

</details>

<details><summary>Suggested Solution</summary>

Solution

</details>


## Challenge 4: Inference Pipeline

connect inference to cloud run pipeline 

<details><summary>Hint</summary>

Hint

</details>

<details><summary>Suggested Solution</summary>

Solution

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