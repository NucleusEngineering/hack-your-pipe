# Data Ingestion and Transformation

A short recap to our example use case. Let's say you have a web shop.
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
gcloud services enable compute.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com dataflow.googleapis.com run.googleapis.com pubsub.googleapis.com
```

... setting your compute zone.

```
gcloud config set compute/zone europe-west1
```

...creating a service account.
```
gcloud iam service-accounts create SA_NAME \
    --display-name="retailpipeline-hyp"
```

... with the necessary permissions.
```
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:retailpipeline-hyp@<project-id>.iam.gserviceaccount.com" \
    --role="roles/dataflow.admin"

```

```
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:retailpipeline-hyp@<project-id>.iam.gserviceaccount.com" \
    --role="roles/dataflow.worker"

```

```
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:retailpipeline-hyp@<project-id>.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

```

```
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:retailpipeline-hyp@<project-id>.iam.gserviceaccount.com" \
    --role="roles/pubsub.subscriber"

```

```
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:retailpipeline-hyp@<project-id>.iam.gserviceaccount.com" \
    --role="roles/pubsub.viewer"

```

```
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="<project-number>-compute@developer.gserviceaccount.com" \
    --role="roles/pubsub.admin"

```

### Organizational Policies

Depending on the setup within your organization you might have to [overwrite some organizational policies](https://cloud.google.com/resource-manager/docs/organization-policy/creating-managing-policies#boolean_constraints) for the examples to run.

For example, the following policies should not be enforced. 

```
constraints/sql.restrictAuthorizedNetworks
constraints/compute.vmExternalIpAccess
constraints/compute.requireShieldedVm
constraints/storage.uniformBucketLevelAccess
constraints/iam.allowedPolicyMemberDomains
```


## Challenge 0:

How would you design this pipeline based on your current knowledge? Which GCP and/or non-GCP tools would you use? 
For now focus on the ingestion part of things.

How would you collect data points and bring them into your cloud environment reliably?

No actions needed yet. Please solely think about the architecture.

<details><summary>Suggested Solution</summary>

We will track user events on our website using [Google Tag Manager](https://developers.google.com/tag-platform/tag-manager).
To receive Google Tag manager events in our cloud environment we will use [Cloud Run](https://cloud.google.com/run/docs/overview/what-is-cloud-run) to set up a proxy service.
This proxy serves as public facing endpoint which can for example be set up as [custom tag](https://support.google.com/tagmanager/answer/6107167?hl=en) in Google Tag Manager.

To distribute the collected data points for processing you will use [Pub/Sub](https://cloud.google.com/pubsub/docs/overview).

Our starting point will look something like this:

![Hack Your Pipe architecture](../../rsc/ingestion.png)

</details>

## Challenge 1.1: Building a container
[Cloud Run](https://cloud.google.com/run/docs/overview/what-is-cloud-run) allows to set up serverless services based on a container we define.
Thus, the one of the fastest, most scalable and cost-efficient ways to build our proxy is Cloud Run.

We need to build a container with the code for our proxy server.
[Cloud Container Registry](https://cloud.google.com/artifact-registry/docs/overview) is a convenient choice for a GCP artifact repository.
But of course you could use any other container repository.

The repository `01_ingest_and_transform/11_challenge/cloud-run-pubsub-proxy` contains the complete proxy code.

Create a new container repository named `pubsub-proxy`.
Build the container described by `01_ingest_and_transform/11_challenge/cloud-run-pubsub-proxy/Dockerfile` in it.

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

You can now stream website interaction data points through a Cloud Run Proxy Service into your Pub/Sub Topic.

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


## Challenge 2.1
[ELT is in!](https://cloud.google.com/bigquery/docs/migration/pipelines#elt)  Imagine you don't actually want to set up processing.
Instead, you would like to build a [modern Lakehouse structure](https://cloud.google.com/blog/products/data-analytics/open-data-lakehouse-on-google-cloud) with ELT processing.
Therefore, your  main concern at this point is to bring the incoming raw data into your Data Warehouse as cost-efficient as possible.
Data users will worry about the processing.

With your current knowledge, which would be the most lightweight architecture to support this use case?

Let's think about and discuss your architecture ideas first. Don't implement anything just yet!

<details><summary>Suggested Solution</summary>

One solution for this challenge would be to use BigQuery as Data Warehouse and a [Pub/Sub BigQuery Subscription](https://cloud.google.com/pubsub/docs/bigquery) as delivery tool.

This elegant setup completely gets rid of the cost and maintenance of a separate data processing tool set.

Our pipeline will look something like this:

![Hack Your Pipe architecture](../../rsc/pubsub_direct.png)

</details>


## Challenge 2.2
To implement our lean ELT pipeline we need:
- BigQuery Dataset
- BigQuery Table
- Pub/Sub BigQuery Subscription

### Preparation Steps

Before you continue please make sure that your Pub/Sub Service Account named something like `service-<project-number>@gcp-sa-pubsub.iam.gserviceaccount.com` has the roles `bigquery.dataEditor` and `bigquery.metadataViewer` granted. 
This permits writing to BigQuery directly.

```
gcloud iam service-accounts add-iam-policy-binding \
  --member serviceAccount:<pubsub_service_account_email> \
  --role roles/bigquery.dataEditor \
  --project <project_id>
```

```
gcloud iam service-accounts add-iam-policy-binding \
  --member serviceAccount:<pubsub_service_account_email> \
  --role roles/bigquery.metadataViewer \
  --project <project_id>
```

### Challenge

Once permissions are set up start with creating a BigQuery Dataset named `ecommerce_sink`. The Dataset should contain a table named `pubsub_direct`.

Continue by setting up a Pub/Sub Subscription named `hyp_subscription_bq_direct` that directly streams incoming messages in the BigQuery Table you created. 


<details><summary>Hint</summary>

This [documentation](https://cloud.google.com/pubsub/docs/create-subscription#subscription) might help.

</details>


<details><summary>Suggested Solution</summary>

```

gcloud pubsub subscriptions create hyp_subscription_bq_direct \
  --topic=hyp-pubsub-topic \
  --bigquery-table=<project-id>:ecommerce_sink.pubsub_direct

```

Alternatively, the [documentation](https://cloud.google.com/pubsub/docs/create-subscription#pubsub_create_bigquery_subscription-console) walks step-by-step through the creation of a BigQuery subscription in the console.

</details>

## Validate ELT Pipeline implementation

You can now stream website interaction data points through your Cloud Run Proxy Service, Pub/Sub Topic & Subscription all the way up to your BigQuery destination table.

Run 

```
python3 ./datalayer/synth_data_stream.py --endpoint=$ENDPOINT_URL
```

to direct an artificial click stream at your pipeline.

After a minute or two you should find your BigQuery destination table populated with data points. 
The metrics of Pub/Sub topic and Subscription should also show the throughput.
Take a specific look at the un-acknowledged message metrics in Pub/Sub.
If everything works as expected it should be 0.


# Part 3: Apply simple transformations and bring data to BigQuery as cost-efficient as possible
ELT is a great new concept. Although sometimes it just makes sense to apply transformation on incoming data directly. 
What if we need to apply some general cleaning, or would like to apply machine learning inference on the incoming data at the soonest point possible?

Traditional [ETL](https://cloud.google.com/bigquery/docs/migration/pipelines#etl) is a proven concept to do just that.

But ETL tools are maintenance overhead. You do not want to manage a Spark, GKE cluster or similar.
Specifically your requirement is a serverless ETL and elastic ETL pipeline.
That means your pipeline should scale down to 0 when unused or up to whatever is needed to cope with a higher load.

## Challenge 3.1
Based on your current knowledge of GCP and non-GCP tools. What would be the ideal architecture to fulfill these requirements?

Don't implement anything just yet. Let's only discuss the architecture for now.

<details><summary>Suggested Solution</summary>

![Hack Your Pipe architecture](../../rsc/cloudrun_processing.png)

</details>



## Challenge 3.2
First component of our lightweight ETL pipeline is a BigQuery Table named `cloud_run`.
The BigQuery Table should make use of the schema file `./datalayer/ecommerce_events_bq_schema.json`.
The processing service will stream the transformed data into this table.

<details><summary>Hint</summary>

The [BigQuery documentation](https://cloud.google.com/bigquery/docs/tables) might be helpful to follow. 

</details>

<details><summary>Suggested Solution</summary>

Run this command

```
bq mk --table <project-id>:ecommerce_sink.cloud_run --schema ./datalayer/ecommerce_events_bq_schema.json 
```

OR follow the documentation on how to [create a BigQuery table with schema through the console](https://cloud.google.com/bigquery/docs/tables#console).

</details>


## Challenge 3.3
Second, let's set up your Cloud Run Processing Service. `./01_ingest_and_transform/11_challenge/processing-service` contains all necessary files.

Inspect the `Dockerfile` to understand how the container will be build.

`main.py` defines the web server that handles the incoming data points. Inspect `main.py` to understand the web server logic.
As you can the `main.py` is missing two code snippets.

Complete the web server with the BigQuery client and Client API call to insert rows to BigQuery from a json object.
Use the BigQuery Python SDK.

Before you start coding replace the required variables in `config.py` so you can access them safely in `main.py`.

<details><summary>Hint</summary>

[Documentation for the BigQuery Python Client](https://cloud.google.com/python/docs/reference/bigquery/latest)

</details>

<details><summary>Suggested Solution</summary>

Define the [BigQuery Python Client](https://cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.client.Client#google_cloud_bigquery_client_Client_insert_rows_json) as followed:
```
client = bigquery.Client(project=config.project_id, location=config.location)
```

Insert rows form JSON via [the Client's insert_rows_json method](https://cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.client.Client#google_cloud_bigquery_client_Client_insert_rows_json):
```
errors = client.insert_rows_json(table_id, rows_to_insert)  # Make an API request.
```

</details>

# TODO: Add data transformation as additional challenge

Once the code is completed build the container from `./01_ingest_and_transform/11_challenge/processing-service` into a new [Container Repository](https://cloud.google.com/artifact-registry/docs/overview) named `data-processing-service`.

<details><summary>Suggested Solution</summary>

```
export PROCESSING_SERVICE_DIR=processing-service

gcloud builds submit $PROCESSING_SERVICE_DIR --tag gcr.io/$GCP_PROJECT/data-processing-service
```

Validate the successful build with:

```
gcloud container images list
```

You should see something like:
```
NAME: gcr.io/<project-id>/pubsub-proxy
NAME: gcr.io/<project-id>/data-processing-service
Only listing images in gcr.io/<project-id>. Use --repository to list images in other repositories.
```

</details>

## Challenge 3.4
Define a Pub/Sub subscription named `hyp_subscription_cloud_run` that can forward incoming messages to an endpoint.
The actual endpoint will be defined in the next challenge.

<details><summary>Hint</summary>

Read about [types of subscriptions](https://cloud.google.com/pubsub/docs/subscriber) and [how to create them](https://cloud.google.com/pubsub/docs/create-subscription#create_subscriptions).

</details>

<details><summary>Suggested Solution</summary>

You will need to create a Push Subscription to the Pub/Sub topic we already defined.

Use this command: 

```
gcloud pubsub subscriptions create hyp_subscription_cloud_run \
    --topic=hyp-pubsub-topic \
    --push-endpoint=PUSH_ENDPOINT
```

OR 

read it can be [defined via the console](https://cloud.google.com/pubsub/docs/create-subscription#pubsub_create_push_subscription-console).

</details>


## Validate lightweight ETL pipeline implementation

You can now stream website interaction data points through your Cloud Run Proxy Service, Pub/Sub Topic & Subscription, Cloud Run Processing and all the way up to your BigQuery destination table.

Run 

```
python3 ./datalayer/synth_data_stream.py --endpoint=$ENDPOINT_URL
```

to direct an artificial click stream at your pipeline.

After a minute or two you should find your BigQuery destination table populated with data points. 
The metrics of Pub/Sub topic and Subscription should also show the throughput.
Take a specific look at the un-acknowledged message metrics in Pub/Sub.
If everything works as expected it should be 0.


# Part 4: Apply transformation, apply aggregation & bring data to BigQuery as efficient as possible
Cloud Run works smooth to apply simple data transformations. On top of that it scales to 0. So why not stop right there?

Let's think one step further. Imagine for example you need to apply aggregations, not only transformations. 
For example, you might need the sum of all purchases made every hour.
You might not want to manage Data Warehouse queries for that.
You might want to have these aggregations directly computed on ingestion or use them to directly feed ML inference.

Since Cloud Run handles incoming data points one-by-one it won't be able to do the job here.
This is where [Apache Beam](https://beam.apache.org/documentation/basics/) comes to shine!

## Challenge 4.1
Based on your current GCP and non-GCP knowledge.
How would the ideal architecture to satisfy above requirements look like?

Don't start building just yet, lets discuss the architecture ideas first.

<details><summary>Suggested Solution</summary>

Dataflow is a great tool to integrate into your pipeline for high volume data streams with complex transformations and aggregations.
It is based on the open-source data processing framework Apache Beam.

![Hack Your Pipe architecture](../../rsc/dataflow.png)

</details>


## Challenge 4.2 
First component of our dataflow ETL pipeline is a BigQuery Table named `dataflow`.
The BigQuery Table should make use of the schema file `./datalayer/ecommerce_events_bq_schema.json`.
The processing service will stream the transformed data into this table.

<details><summary>Suggested Solution</summary>

Run this command

```
bq mk --table <project-id>:ecommerce_sink.dataflow --schema ./datalayer/ecommerce_events_bq_schema.json 
```

OR follow the documentation on how to [create a BigQuery table with schema through the console](https://cloud.google.com/bigquery/docs/tables#console).

</details>


Second component is the connection between Pub/Sub topic and Dataflow job.

Define a Pub/Sub subscription named `hyp_subscription_dataflow` that can serve this purpose.
You will define the actual dataflow job in the next step.

<details><summary>Hint</summary>

Read about [types of subscriptions](https://cloud.google.com/pubsub/docs/subscriber) and [how to create them](https://cloud.google.com/pubsub/docs/create-subscription#create_subscriptions).

</details>

<details><summary>Suggested Solution</summary>

You will need to create a Pull Subscription to the Pub/Sub topic we already defined.
This is a fundamental difference to the Push subscriptions we encountered in the previous two examples.
Dataflow will pull the data points from the queue independently, depending on worker capacity.

Use this command: 

```
gcloud pubsub subscriptions create hyp_subscription_dataflow \
    --topic=hyp-pubsub-topic \
```

OR 

read how it can be [defined via the console](https://cloud.google.com/pubsub/docs/create-subscription#pull_subscription).

</details>



## Challenge 4.3
Finally, the last piece we are missing is your Dataflow job to apply transformations, aggregations and connect Pub/Sub queue with BigQuery Sink.

Define a Dataflow job that transports data from your Pub/Sub Subscription to BigQuery

<details><summary>Hint</summary>

The easiest way to solve this is by using the [Pub/Sub Subscription to BigQuery](https://cloud.google.com/dataflow/docs/guides/templates/provided-streaming#console) template.

</details>


<details><summary>Suggested Solution</summary>

Use this command to define a Dataflow Job based on the Pub/Sub Subscription to BigQuery template:

```

gcloud dataflow jobs run ecommerce-events-ps-to-bq-stream \
    --gcs-location gs://dataflow-templates/VERSION/PubSub_Subscription_to_BigQuery \
    --region europe-west1 \
    --staging-location TEMP_LOCATION \
    --parameters \
inputSubscription=projects/<project-id>/subscriptions/hyp_subscription_dataflow,\
outputTableSpec=<project-id>:DATASET.TABLE_NAME,\

```

[//]: # (# TODO: temp bucket)

</details>




