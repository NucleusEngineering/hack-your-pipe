/**
 * Copyright 2022 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "4.31.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.gcp_region
}

resource "google_compute_network" "vpc_network" {
  name = "terraform-network"  
}

resource "google_compute_firewall" "vpc_network_firewall" {
  name    = "firewall"
  
  network = google_compute_network.vpc_network.name
  
  source_service_accounts = ["${google_service_account.data_pipeline_access.email}"]

  allow {
    protocol = "tcp"
    ports    = ["12345", "12346"]
  }
}

resource "google_service_account" "data_pipeline_access" {
  project = var.project_id
  account_id = "retailpipeline-hyp"
  display_name = "Retail app data pipeline access"
}


# Set permissions.

resource "google_project_iam_member" "dataflow_admin_role" {
  project = var.project_id
  role = "roles/dataflow.admin"
  member = "serviceAccount:${google_service_account.data_pipeline_access.email}"
}

resource "google_project_iam_member" "dataflow_worker_role" {
  project = var.project_id
  role = "roles/dataflow.worker"
  member = "serviceAccount:${google_service_account.data_pipeline_access.email}"
}

resource "google_project_iam_member" "dataflow_bigquery_role" {
  project = var.project_id
  role = "roles/bigquery.dataEditor"
  member = "serviceAccount:${google_service_account.data_pipeline_access.email}"
}

resource "google_project_iam_member" "dataflow_pub_sub_subscriber" {
  project = var.project_id
  role = "roles/pubsub.subscriber"
  member = "serviceAccount:${google_service_account.data_pipeline_access.email}"
}

resource "google_project_iam_member" "dataflow_pub_sub_viewer" {
  project = var.project_id
  role = "roles/pubsub.viewer"
  member = "serviceAccount:${google_service_account.data_pipeline_access.email}"
}


# Enabling APIs

resource "google_project_service" "compute" {
  service = "compute.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_service" "run" {
  service = "run.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_service" "dataflow" {
  service = "dataflow.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_service" "pubsub" {
  service = "pubsub.googleapis.com"
  disable_on_destroy = false
}


# Define common resources used by all pipeline options.

# Cloud Run Proxy
resource "google_cloud_run_service" "pubsub_proxy_hyp" {
  name     = "pubsub-proxy-hyp"
  location = var.gcp_region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/pubsub-proxy"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.run]
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = google_cloud_run_service.pubsub_proxy_hyp.location
  project     = google_cloud_run_service.pubsub_proxy_hyp.project
  service     = google_cloud_run_service.pubsub_proxy_hyp.name
  policy_data = data.google_iam_policy.noauth.policy_data
}

output "cloud_run_proxy_url" {
  value = google_cloud_run_service.pubsub_proxy_hyp.status[0].url
}

# BigQuery Dataset
resource "google_bigquery_dataset" "bq_dataset" {
  dataset_id                  = "ecommerce_sink"
  friendly_name               = "ecommerce sink"
  description                 = "Destination dataset for all pipeline options"
  location                    = var.gcp_region

  delete_contents_on_destroy = true

  labels = {
    env = "default"
  }
}

# Pub/Sub Topic
resource "google_pubsub_topic" "ps_topic" {
  name = "ecommerce-events"

  labels = {
    created = "terraform"
  }

  depends_on = [google_project_service.pubsub]
}


# Pipeline 1: Cloud Run Proxy -> Pub/Sub -> Dataflow -> BigQuery
resource "google_pubsub_subscription" "hyp_sub_dataflow" {
  name  = "hyp_subscription_bq_direct"
  topic = google_pubsub_topic.ps_topic.name

  labels = {
    created = "terraform"
  }
  
  retain_acked_messages      = false

  ack_deadline_seconds = 20


  retry_policy {
    minimum_backoff = "10s"
  }

  enable_message_ordering    = false
}

resource "google_bigquery_table" "bq_table_dataflow" {
  dataset_id = google_bigquery_dataset.bq_dataset.dataset_id
  table_id   = "ecommerce_events"
  deletion_protection = false

  time_partitioning {
    type = "DAY"
    field = "event_datetime"
  }

  labels = {
    env = "default"
  }

  schema = file("ecommerce_events_bq_schema.json")

}

resource "google_storage_bucket" "dataflow_gcs_bucket" {
    name = "${var.project_id}-ecommerce-events"
    location = var.gcp_region
    force_destroy = true
}

resource "google_dataflow_job" "dataflow_stream" {
    name = "ecommerce-events-ps-to-bq-stream"
    template_gcs_path = "gs://dataflow-templates/latest/PubSub_Subscription_to_BigQuery"
    temp_gcs_location = "${google_storage_bucket.dataflow_gcs_bucket.url}/tmp_dir"

    parameters = {
      inputSubscription = google_pubsub_subscription.hyp_sub_dataflow.id
      outputTableSpec   = "${google_bigquery_table.bq_table_dataflow.project}:${google_bigquery_table.bq_table_dataflow.dataset_id}.${google_bigquery_table.bq_table_dataflow.table_id}"
    }

    transform_name_mapping = {
        name = "test_job"
        env = "dev"
    }

    on_delete = "cancel"
    service_account_email = "${google_service_account.data_pipeline_access.email}"
    network = "${google_compute_network.vpc_network.name}"
    depends_on = [google_project_service.compute, google_project_service.dataflow]
}


# Pipeline 2: Cloud Run Proxy -> Pub/Sub -> BigQuery
resource "google_bigquery_table" "bq_table" {
  dataset_id = google_bigquery_dataset.bq_dataset.dataset_id
  table_id   = "ecommerce_events"
  deletion_protection = false

  time_partitioning {
    type = "DAY"
    field = "event_datetime"
  }

  labels = {
    env = "default"
  }

  schema = <<EOF
[
  {
    "name": "data",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "The data"
  }
]
EOF
}

resource "google_pubsub_subscription" "sub_bqdirect" {
  name  = "hyp_subscription_bq_direct"
  topic = google_pubsub_topic.ps_topic.name

  labels = {
    created = "terraform"
  }

  bigquery_config {
    table = "${google_bigquery_table.bq_table.project}:${google_bigquery_table.bq_table.dataset_id}.${google_bigquery_table.bq_table.table_id}"
  }

#  depends_on = [google_project_iam_member.viewer, google_project_iam_member.editor]

  retain_acked_messages      = false

  ack_deadline_seconds = 20

  retry_policy {
    minimum_backoff = "10s"
  }

  enable_message_ordering    = false
}





# TODO:  Create Pipeline via Cloud Run Processing Service
# -> BQ Table to sink
# -> PubSub Subscription to receive
# -> Cloud Run Service to process

# TODO: Create Pipeline via direct PubSub BQ Subscription
# -> PubSub Subscription to receive & process
# -> BQ Table to sink