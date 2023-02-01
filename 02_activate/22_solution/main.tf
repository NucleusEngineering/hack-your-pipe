/**
 * Copyright 2023 Google
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
      version = "4.32.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.gcp_region
}

data "google_project" "project" {
}

resource "google_bigquery_table" "bq_table_run_anomaly" {
  dataset_id = "ecommerce_sink"
  table_id   = "cloud_run_anomaly"
  deletion_protection = false

  labels = {
    env = "default"
  }

  schema = <<EOF
[
  {
    "name": "tax",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "The data"
  },
    {
    "name": "shipping",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "The data"
  },
    {
    "name": "value",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "The data"
  },
    {
    "name": "anomaly",
    "type": "BOOL",
    "mode": "NULLABLE",
    "description": "The data"
  }
  
]
EOF
}