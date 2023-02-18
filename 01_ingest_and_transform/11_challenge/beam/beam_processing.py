# Copyright 2023 Google

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import time

import config

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.transforms import trigger
from apache_beam.io.gcp.pubsub import ReadFromPubSub
from apache_beam.io.gcp.bigquery import BigQueryDisposition, WriteToBigQuery
from apache_beam.runners import DataflowRunner

# Defining event filter functions.


def is_item_view(event):
    return event['event'] == 'view_item'


def is_add_to_cart(event):
    return event['event'] == 'add_to_cart'


def is_purchase(event):
    return event['event'] == 'purchase'


class ExtractValueFn(beam.DoFn):
    def process(self, element):
        print(f"ExtractValueFn: {element['ecommerce']['purchase']['value']}")
        return [element['ecommerce']['purchase']['value']]


class ExtractAndSumValue(beam.PTransform):
    """A transform to extract key/score information and sum the scores.
  The constructor argument `field` determines whether 'team' or 'user' info is
  extracted.
  """

    def expand(self, pcoll):
        sum_val = (
            pcoll
            | beam.Map(lambda elem: (elem['user_id'], elem['ecommerce']['purchase']['value']))
            | beam.CombinePerKey(sum))
        return(sum_val)


class FormatByRow(beam.PTransform):
    """A transform to reformat the data to column name/value format.
  """

    def expand(self, pcoll):
        row_val = (
            pcoll
            | beam.Map(lambda elem: {'user_id': elem[0],
                                     'summed_value': elem[1]
                                     })
        )
        return(row_val)


def streaming_pipeline(project, region):

    subscription = "projects/{}/subscriptions/hyp_subscription_dataflow".format(
        project)

    bucket = "gs://{}-ecommerce-events/tmp_dir".format(project)

    # Defining pipeline options.
    options = PipelineOptions(
        streaming=True,
        project=project,
        region=region,
        staging_location="%s/staging" % bucket,
        temp_location="%s/temp" % bucket,
        subnetwork='regions/europe-west1/subnetworks/terraform-network',
        service_account_email='retailpipeline-hyp@{}.iam.gserviceaccount.com'.format(
            project),
        max_num_workers=1
    )

    # Defining pipeline.
    p = beam.Pipeline(DataflowRunner(), options=options)

    # Receiving message from Pub/Sub & parsing json from string.
    json_message = (p
                    # Listining to Pub/Sub.
                    | "Read Topic" >> ReadFromPubSub(subscription=subscription)
                    # Parsing json from message string.
                    | "Parse json" >> beam.Map(json.loads)
                    )

    # Extracting Item Views.
    item_views = (json_message
                  | 'Filter for item views' >> beam.Filter(is_item_view)
                  | "item view row" >> beam.Map(lambda input: {'event_datetime': input['event_datetime'],  # Dropping and renaming columns.
                                                               'event': input['event'],
                                                               'user_id':  input['user_id'],
                                                               'client_id': input['client_id'],
                                                               'page': input['page'],
                                                               'page_previous': input['page_previous'],
                                                               "item_name": input['ecommerce']['items'][0]["item_name"],
                                                               "item_id": input['ecommerce']['items'][0]["item_id"],
                                                               "price": input['ecommerce']['items'][0]["price"],
                                                               "item_brand": input['ecommerce']['items'][0]["item_brand"],
                                                               "item_category": input['ecommerce']['items'][0]["item_category"],
                                                               "item_category_2": input['ecommerce']['items'][0]["item_category_2"],
                                                               "item_category_3": input['ecommerce']['items'][0]["item_category_3"],
                                                               "item_category_4": input['ecommerce']['items'][0]["item_category_4"],
                                                               "item_variant": input['ecommerce']['items'][0]["item_variant"],
                                                               "item_list_name": input['ecommerce']['items'][0]["item_list_name"],
                                                               "item_list_id": input['ecommerce']['items'][0]["item_list_id"],
                                                               "quantity": input['ecommerce']['items'][0]["quantity"]
                                                               })
                  )

    fixed_windowed_items = (json_message
                            | 'Filter for purchase' >> beam.Filter(is_purchase)
                            | 'Global Window' >> beam.WindowInto(beam.window.GlobalWindows(),
                                                                 trigger=trigger.Repeatedly(
                                                                     trigger.AfterCount(10)),
                                                                 accumulation_mode=trigger.AccumulationMode.ACCUMULATING)
                            | 'ExtractAndSumValue' >> ExtractAndSumValue()
                            | 'FormatByRow' >> FormatByRow()
                            )

    # Writing summed values to BigQuery
    aggregated_schema = "user_id:STRING, summed_value:FLOAT"
    aggregated_table = "{}:ecommerce_sink.beam_aggregated".format(project)

    fixed_windowed_items | "Write Summed Values To BigQuery" >> WriteToBigQuery(table=aggregated_table, schema=aggregated_schema,
                                                                                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                                                                                write_disposition=BigQueryDisposition.WRITE_APPEND)

    # Writing the PCollections to two differnt BigQuery tables.
    item_views_table = "{}:ecommerce_sink.beam_item_views".format(project)
    schema = "event_datetime:DATETIME, event:STRING, user_id:STRING, client_id:STRING, page:STRING, page_previous:STRING, " \
        "item_name:STRING, item_id:STRING, price:STRING, item_brand:STRING, item_category:STRING, item_category_2:STRING, item_category_3:STRING, " \
        "item_category_4:STRING, item_variant:STRING, item_list_name:STRING, item_list_id:STRING, quantity:STRING"

    item_views | "Write Items Views To BigQuery" >> WriteToBigQuery(table=item_views_table, schema=schema,
                                                                    create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                                                                    write_disposition=BigQueryDisposition.WRITE_APPEND)

    return p.run()


if __name__ == '__main__':
    GCP_PROJECT = config.project_id
    GCP_REGION = config.location

    streaming_pipeline(project=GCP_PROJECT, region=GCP_REGION)
