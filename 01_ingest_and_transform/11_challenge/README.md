# Data Ingestion and Transformation

A short recap to our example use case. Let's say you have a webshop.
As Data Engineer you want to set up a solution to collect and analyze user interactions as shown below.  

![Hack Your Pipe architecture](../../rsc/hyp_architecture.png)

## Challenge Preparation

Before you jump into the challenges make sure you GCP project is prepared by: 

... initializing your account and project.

```
gcloud init
```

... setting your Google Cloud Project.

```
export GCP_PROJECT=<project-id>
gcloud config set project $GCP_PROJECT
```

... enabling your Google Cloud APIs.

```
gcloud services enable compute.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com dataflow.googleapis.com
```

... setting your compute zone.

```
gcloud config set compute/zone europe-west1
```


## Challenge 0:

How would you design this pipeline based on your current knowledge? Which GCP and/or non-GCP tools would you use? 
For now focus on the ingestion part of things.

How would you collect datapoints and bring them into your cloud environment reliably?

No actions needed yet. Please solely think about the architecture.

<details><summary>Suggested Solution</summary>

We will track user events on our website using [Google Tag Manager](https://developers.google.com/tag-platform/tag-manager).
To receive Google Tag manager events in our cloud environment we will use [Cloud Run](https://cloud.google.com/run/docs/overview/what-is-cloud-run) to set up a proxy service.
This proxy serves as public facing endpoint which can for example be set up as [custom tag](https://support.google.com/tagmanager/answer/6107167?hl=en) in Google Tag Manager.

To distribute the collected datapoints for processing you will use [Pub/Sub](https://cloud.google.com/pubsub/docs/overview).

Our starting point will look something like this:

![Hack Your Pipe architecture](../../rsc/ingestion.png)

</details>

## Challenge 1.1: Building a container
[Cloud Run](https://cloud.google.com/run/docs/overview/what-is-cloud-run) allows to set up serverless services based on a container we define.
Thus, the one of the fastest, most scalable and cost-efficient ways to build our proxy is Cloud Run.

We need to build a container with the code for our proxy server.
[Cloud Source Repository](https://cloud.google.com/source-repositories/docs/features) is a convenient choice for a GCP artifact repository.
But of course you could use any other container repository.

The repository `01_ingest_and_transform/11_challenge/cloud-run-proxy` contains the complete proxy code.

Create a new container repository named `pubsub-proxy`.
Build the container described by `01_ingest_and_transform/11_challenge/cloud-run-proxy/Dockerfile` in it.

You will have to use the [gcloud builds submit](https://cloud.google.com/sdk/gcloud/reference/builds/submit) command.

<details><summary>Suggested Solution</summary>

```
export RUN_PROXY_DIR=cloud-run-pubsub-proxy

gcloud builds submit $RUN_PROXY_DIR --tag gcr.io/$GCP_PROJECT/pubsub-proxy
```

Validate the successful build with:

```
gcloud container images list
```

You should see something like:
```
NAME: gcr.io/<project-id>/pubsub-proxy
Only listing images in gcr.io/<project-id>. Use --repository to list images in other repositories.
```

</details>

## Challenge 1.2:
You created a new container for our proxy server.
Create a new Cloud Run Service named `hyp-run-service-pubsub-proxy` based on the container you built.

Then save the endpoint URL for your service as environment variable `$ENDPOINT_URL`.

You can use the [Cloud Run Documentation](https://cloud.google.com/run/docs/deploying#service).

<details><summary>Suggested Solution</summary>

To deploy a new Cloud Run service from your container you can use:

```

gcloud run deploy hyp-run-service-pubsub-proxy --image gcr.io/<project-id>/pubsub-proxy:latest

```

To save the service endpoint URL in the environment variable `$ENDPOINT_URL` run: 

```
export ENDPOINT_URL=https://pubsub-proxy-my-service-<id>-uc.a.run.app
```

</details>


## Challenge 1.3: 
Next, a messaging queue with [Pub/Sub](https://cloud.google.com/pubsub/docs/overview) will allow us to collect all messages centrally to then distribute them for processing.

Set up a Pub/Sub topic named `hyp-pubsub-topic`.

The [documentation](https://cloud.google.com/pubsub/docs/admin#pubsub_create_topic-Console) will help to create the topic via console or command line.

<details><summary>Suggested Solution</summary>

Use this command in the Cloud Shell to create the topic via command line.

```gcloud pubsub topics create hyp-pubsub-topic```

OR follow [these](https://cloud.google.com/pubsub/docs/admin#pubsub_create_topic-Console) steps to create the topic via Cloud Console.

</details>

## Validate Event Ingestion

You can now stream website interaction datapoints through a Cloud Run Proxy Service into your Pub/Sub Topic.

The folder `01_ingest_and_transform/11_challenge/datalayer` contains everything you need to simulate a click-stream.
You will find four .json files that define different types of messages.
Furthermore, you can find the script `synth_data_stream.py`.

Run to direct an artificial click stream at your pipeline.

```
python3 ./datalayer/synth_data_stream.py --endpoint=$ENDPOINT_URL
```

After a minute or two validate that your solution is working by inspecting the [metrics](https://cloud.google.com/pubsub/docs/monitor-topic) of your Pub/Sub topic.
Of course the topic does not have any consumers yet. Thus, you should find that messages are queuing up.


# Part 2: Bring raw data to BigQuery as efficient as possible

Now that your data ingestion is working correctly we move on to set up your processing infrastructure.
Data processing infrastructures often have vastly diverse technical and business requirements. 
We will find the right setup for three completely different settings.


## Challenge 2.1:
ELT is in! Imagine you don't actually want to set up processing.
Instead, you would like to build a modern Lakehouse structure with ELT procesing.
Therefore, your  main concern at this point is to bring the incoming raw data into your Data Warehouse as cost-efficient as possible.
Data users will worry about the processing.

With your current knowledge, which would be the most lightweight architecture to support this use case?

Let's think about and discuss your architecture ideas first. Don't implement anything just yet!

<details><summary>Suggested Solution</summary>

One solution for this challenge would be to use BigQuery as Data Warehouse and a [Pub/Sub BigQuery Subscription](https://cloud.google.com/pubsub/docs/bigquery) as delivery tool.

This elegant setup completely gets rid of the cost and maintenance of a separate data processing toolset.

Our pipeline will look something like this:

![Hack Your Pipe architecture](../../rsc/pubsub_direct.png)

</details>


## Challenge 2.2:
Implement it

<details><summary>Suggested Solution</summary>

Challenge Solution

</details>


# Part 3: Apply transformation and bring data to BigQuery as efficient as possible

## Challenge 3.1:
Chose best architecture

<details><summary>Suggested Solution</summary>

Challenge Solution

</details>


## Challenge 3.2:
Implement it

<details><summary>Suggested Solution</summary>

Challenge Solution

</details>


# Part 4: Apply transformation, apply aggregation & bring data to BigQuery as efficient as possible

## Challenge 4.1:
Chose best architecture

<details><summary>Suggested Solution</summary>

Challenge Solution

</details>


## Challenge 4.2: 
Implement it

<details><summary>Suggested Solution</summary>

Challenge Solution

</details>




