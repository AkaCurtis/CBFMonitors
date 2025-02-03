import requests
import json
import time
from datetime import datetime
import configparser
import os

url = "https://developer.woot.com/feed/all"

SENT_OFFERS_FILE = 'sent_offers.txt'
sent_offer_ids = set()

def load_sent_offer_ids():
    if os.path.exists(SENT_OFFERS_FILE):
        with open(SENT_OFFERS_FILE, 'r') as file:
            for line in file:
                sent_offer_ids.add(line.strip())

def save_sent_offer_id(offer_id):
    with open(SENT_OFFERS_FILE, 'a') as file:
        file.write(f"{offer_id}\n")

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

def fetch_clearance_items(api_key):
    headers = {
        'Accept': 'application/json',
        'x-api-key': api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('Items', [])
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return []

def send_to_discord(item, webhook_url, discount_threshold, amz_fulfilled):
    list_price = item.get('ListPrice') or {}
    sale_price = item.get('SalePrice') or {}

    msrp_min = list_price.get('Minimum', 0)
    sale_min = sale_price.get('Minimum', 0)

    if msrp_min and sale_min and msrp_min > sale_min:
        discount_percent = ((msrp_min - sale_min) / msrp_min) * 100
        dollar_savings = msrp_min - sale_min

        if discount_percent < float(discount_threshold):
            return

        is_fulfilled_by_amazon = item.get('IsFulfilledByAmazon', False)
        if amz_fulfilled == 'Y' and not is_fulfilled_by_amazon:
            return

        start_date = datetime.fromisoformat(item['StartDate'].replace("Z", "+00:00"))
        formatted_date = f"<t:{int(start_date.timestamp())}:D>"

        end_date = datetime.fromisoformat(item['EndDate'].replace("Z", "+00:00"))
        formatted_end_date = f"<t:{int(end_date.timestamp())}:D>"

        embed = {
            "title": item.get('Title', 'No Title'),
            "url": item.get('Url', 'https://woot.com'),
            "thumbnail": {"url": item.get('Photo', '')},
            "fields": [
                {"name": "MSRP", "value": f"${msrp_min:.2f}", "inline": True},
                {"name": "Discounted Price", "value": f"${sale_min:.2f}", "inline": True},
                {"name": "Dollar Savings", "value": f"${dollar_savings:.2f}", "inline": True},
                {"name": "Discount Percent", "value": f"{discount_percent:.2f}%", "inline": True},
                {"name": "Category", "value": item.get('Categories', ["N/A"])[0], "inline": True},
                {"name": "Start Date", "value": formatted_date, "inline": True},
                {"name": "End Date", "value": formatted_end_date, "inline": True},
                {"name": "Fulfilled by Amazon", "value": "✅" if is_fulfilled_by_amazon else "❌", "inline": True},
            ],
            "color": 3447003
        }

        data = {"embeds": [embed]}
        response = requests.post(webhook_url, headers={"Content-Type": "application/json"}, data=json.dumps(data))

        ### THIS WILL SPAM YOUR CONSOLE YOU'RE WELCOME TO UNCOMMIT IT

        #if response.status_code == 204:
            #print(f"Sent: {item['Title']} to {webhook_url}")
        #else:
            #print(f"Failed to send item to Discord: {response.status_code}, {response.text}")

def main():
    load_sent_offer_ids()
    while True:
        config = load_config()
        api_key = config['DEFAULT'].get('API_KEY')
        items = fetch_clearance_items(api_key)

        for item in items:
            offer_id = item['OfferId']
            if offer_id not in sent_offer_ids:
                for section in config.sections():
                    webhook_url = config[section].get('webhook')
                    discount_threshold = config[section].get('discount', 0)
                    amz_fulfilled = config[section].get('AMZFulfilled', 'N')
                    send_to_discord(item, webhook_url, discount_threshold, amz_fulfilled)
                sent_offer_ids.add(offer_id)
                save_sent_offer_id(offer_id)

        time.sleep(300)

if __name__ == "__main__":
    main()
