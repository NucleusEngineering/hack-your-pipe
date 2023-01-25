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

import random
import requests
import json
import time
import argparse


def main(endpoint):
    draw = round(random.uniform(0, 1), 2)

    uid = f'UID0000{int(round(random.uniform(0, 5), 0))}'

    if 0 <= draw < 1 / 3:
        # get view payload
        view_item_f = open('./datalayer/view_item.json')
        view_item_payload = json.load(view_item_f)

        view_item_payload['user_id'] = uid

        # send view
        r = requests.post(endpoint, json=view_item_payload)

    elif 1 / 3 <= draw < 2 / 3:
        # get add to cart payload
        add_to_cart_f = open('./datalayer/add_to_cart.json')
        add_to_cart_payload = json.load(add_to_cart_f)

        add_to_cart_payload['user_id'] = uid

        # send add to cart
        r = requests.post(endpoint, json=add_to_cart_payload)

    else:
        # decide between anomaly or no anomaly
        if draw < 0.95:
            # get payload
            purchase_f = open('./datalayer/purchase.json')
            purchase_payload = json.load(purchase_f)

            purchase_payload['user_id'] = uid

            # send request
            r = requests.post(endpoint, json=purchase_payload)
        else:
            # get payload
            purchase_anomaly_f = open('./datalayer/purchase_anomaly.json')
            purchase_anomaly_payload = json.load(purchase_anomaly_f)

            purchase_anomaly_payload['user_id'] = uid

            # send request
            r = requests.post(endpoint, json=purchase_anomaly_payload)

    # print(r.text)
    print(f'{time.time()} -- {r.status_code}')


if __name__ == "__main__":
    # Parse Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", help="Target Endpoint")

    args = parser.parse_args()

    endpoint = args.endpoint + '/json'

    while True:
        main(endpoint)
        time.sleep(2)
