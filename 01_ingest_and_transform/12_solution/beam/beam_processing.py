import json
import time

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
  def __init__(self):
    beam.PTransform.__init__(self)
    # self.field = field

  def expand(self, pcoll):
    print('expanding!')
    return(
        pcoll
        | beam.Map(lambda elem: (elem['client_id'], elem['ecommerce']['purchase']['value']))
        | beam.CombinePerKey(sum))


def streaming_pipeline(project, region):
    topic = "projects/poerschmann-hyp-test2/topics/hyp-pubsub-topic"
    subscription = "projects/poerschmann-hyp-test2/subscriptions/hyp_test"
    item_views_table = "{}:ecommerce_sink.beam_test_views".format(project)
    add_to_carts_table = "{}:ecommerce_sink.beam_test_carts".format(project)
    schema = "event_datetime:DATETIME, event:STRING, user_id:STRING, client_id:STRING, page:STRING, page_previous:STRING, " \
        "item_name:STRING, item_id:STRING, price:STRING, item_brand:STRING, item_category:STRING, item_category_2:STRING, item_category_3:STRING, " \
        "item_category_4:STRING, item_variant:STRING, item_list_name:STRING, item_list_id:STRING, quantity:STRING"
    bucket = "gs://poerschmann-hyp-test2-ecommerce-events/tmp_dir"

    # Defining pipeline options.
    options = PipelineOptions(
        streaming=True,
        project=project,
        region=region,
        staging_location="%s/staging" % bucket,
        temp_location="%s/temp" % bucket,
        subnetwork='regions/europe-west1/subnetworks/terraform-network',
        service_account_email='retailpipeline-hyp@poerschmann-hyp-test2.iam.gserviceaccount.com',
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

    # Extracting Add To Carts.
    add_to_carts = (json_message
                    | 'Filter for add to cart' >> beam.Filter(is_add_to_cart)
                    | "add to cart row" >> beam.Map(lambda input: {'event_datetime': input['event_datetime'],  # Dropping and renaming columns.
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

    # class LogElementFn(beam.DoFn):
    def LogElementFn(element):
        print(
            f"LogElementFn: {type(element)}; {element} #### {type(element['ecommerce'])}; {element['ecommerce']}  #### {type(element['ecommerce']['purchase'])}; {element['ecommerce']['purchase']} #### {type(element['ecommerce']['purchase']['value'])}; {element['ecommerce']['purchase']['value']}")
        return element

    def LogWindowedElements(element):
        print(f'LogWindowFn: {type(element)}; {element}')
        return element

    fixed_windowed_items = (json_message
                            # | 'Print Pcoll' >> beam.ParDo(print)
                            | 'Filter for purchase' >> beam.Filter(is_purchase)
                            # | 'Log Input' >> beam.ParDo(lambda x: ExtractValueFn(x))
                            | 'Global Window' >> beam.WindowInto(beam.window.GlobalWindows(),
                                                                 trigger=trigger.Repeatedly(
                                                                     trigger.AfterCount(10)),
                                                                 accumulation_mode=trigger.AccumulationMode.ACCUMULATING)
                            # | 'Sum per window' >> beam.CombineGlobally(sum)
                            # | 'Log Per Summed Window' >> beam.ParDo(lambda x: LogWindowedElements(x))
                            #   | 'ExtractAndSumValue' >> ExtractAndSumValue()
                            #   | 'Count' >> beam.transforms.combiners.Count.Globally()
                            # | 'Extract Value' >> beam.ParDo(ExtractValueFn())
                              | 'Print PColl' >> beam.ParDo(print) # -> working without pre steps!
                            # | 'Log Windowed' >> beam.Map(lambda x: LogWindowedElements(x))
                            # | 'Count elements by key' >> beam.combiners.Count.PerKey()
                            )

    # Writing summed values to BigQuery
    test_schema = "user_id:STRING, summed_value:FLOAT"
    test_value_table = "{}:ecommerce_sink.beam_test_value".format(project)
    
    # fixed_windowed_items | "Write Summed Values To BigQuery" >> WriteToBigQuery(table=test_value_table, schema=test_schema,
    #                                                                 create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
    #                                                                 write_disposition=BigQueryDisposition.WRITE_APPEND)


    # Writing the PCollections to two differnt BigQuery tables.
    item_views | "Write Items Views To BigQuery" >> WriteToBigQuery(table=item_views_table, schema=schema,
                                                                    create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                                                                    write_disposition=BigQueryDisposition.WRITE_APPEND)

    add_to_carts | "Write Add To Carts To BigQuery" >> WriteToBigQuery(table=add_to_carts_table, schema=schema,
                                                                       create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                                                                       write_disposition=BigQueryDisposition.WRITE_APPEND)

    return p.run()


if __name__ == '__main__':
    GCP_PROJECT = "poerschmann-hyp-test2"
    GCP_REGION = "europe-west1"

    streaming_pipeline(project=GCP_PROJECT, region=GCP_REGION)
