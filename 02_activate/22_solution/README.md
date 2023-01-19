# Developing and deploying Machine Leaning Models on GCP

Welcome to the second part of Hack Your Pipe!

So far you discovered multiple options to ingest and transform data most efficiently.
In this section you go one step further with your data, but constantly build on the previous learnings.
You will train and deploy Machine Learning models that detect anomalies in the incoming click stream.

Hereby we will focus on automation, simplicity and reliability of every step in the Machine Learning Lifecycle.

The architecture you are going to implement will look something like this:

![Hack Your Pipe architecture](../../rsc/hyp_ml_architecture.png)



## Git clone repo 

```
git clone https://github.com/jakobap/HackYourPipe.git
cd HackYourPipe
```

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

### Create Synthetic Data

You will use the clickstream data from the ingest and transform section as an example.

If you havent worked through the ingest and transform chapter follow `01_ingest_and_transform/12_solution/README.md`.

Before moving on make sure that your BigQuery project has a dataset `ecommerce_sink` with the tables `cloud_run`, `dataflow` and `pubsub_direct`.
The tables should be populated with at least 1000 datapoints each.


### Set pipeline config options

Set the config options in `02_activate/22_solution/config.py`. 


### Run Kubeflow Pipeline in Vertex

[Vertex Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines/introduction) is an end-to-end and serverless ML orchestration tool. It's supports the open source frameworks [Kubeflow](https://www.kubeflow.org/) and [TFX](https://www.tensorflow.org/tfx).

The full process from model training to deployment can be orchestrated using Vertex Pipelines. 

To kick of the pipeline simply install the dependencies
```
pip install -r ./requirements.txt
```

and then run

```
python3 kf_pipe.py
```
