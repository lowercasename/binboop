import os
import time
import datetime
from dateutil import parser
import schedule
import requests
from dotenv import load_dotenv

load_dotenv()

alert_time = "21:00"
location_id = os.getenv('LOCATION_ID')
number_of_collections = 1
bin_collections_url = f'https://servicelayer3c.azure-api.net/wastecalendar/collection/search/{location_id}/?numberOfCollections={number_of_collections}'

round_types = {
    'ORGANIC': 'garden waste',
    'RECYCLE': 'recycling',
    'DOMESTIC': 'rubbish',
}

pushover_url = 'https://api.pushover.net/1/messages.json'
pushover_params = {
    "token": os.getenv('PUSHOVER_TOKEN'),
    "user": os.getenv('PUSHOVER_USER'),
}

# Helper functions for logging
def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(message):
    print(f"[{get_current_time()}] {message}")

# Send an alert via Pushover
def send_alert(payload):
    log("Sending alert")
    try:
        params = {**pushover_params, **payload}
        response = requests.post(pushover_url, params=params)
    except Exception as e:
        log(f"Error sending alert: {e}")

def check_bin_collections():
    log("Checking bin collection times")
    try:
        # Fetch the API data
        response = requests.get(url=bin_collections_url)
        data = response.json()

        # Parse the data from the next collection into friendly formats
        next_collection = data['collections'][0]
        log(next_collection)
        collection_date = parser.parse(next_collection['date']).date()
        collection_types = [round_types[x] for x in next_collection['roundTypes']]
        collection_types_string = ' and '.join(collection_types)

        # Check if the collection date is tomorrow (we want to be alerted
        # the night before)
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        if collection_date == tomorrow:
            payload = {
                "message": f"Don't forget to put the {collection_types_string} {'bins' if len(collection_types) > 1 else 'bin'} out tonight.",
            }
            send_alert(payload)
    except Exception as e:
        log(f"Error getting bin collection times: {e}")

log("BinBoop running!")

schedule.every().day.at(alert_time).do(check_bin_collections)

while True:
    schedule.run_pending()
    time.sleep(1)
