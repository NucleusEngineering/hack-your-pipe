import random
import time
import os

while True:
    number = random.randrange(0, 2, 1)
    print(number)

    if number > 0:
        os.system('curl POST ${CLOUD_RUN_PROXY}/json -d @datalayer/view_item.json --header "Content-Type: '
                  'application/json"')
        os.system('echo view_item')
    elif number == 0:
        os.system('curl -v POST ${CLOUD_RUN_PROXY}/json -d @datalayer/add_to_cart.json --header "Content-Type: '
                  'application/json"')
        os.system('echo add_to_cart')

    time.sleep(1.0)
