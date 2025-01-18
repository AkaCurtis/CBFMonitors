import requests
import json
import time
from datetime import datetime

API_KEY = ""
DISCORD_WEBHOOK_URL = ""

headers = {
    'Accept': 'application/json',
    'x-api-key': API_KEY
}

url = "https://developer.woot.com/feed/Clearance"

sent_offer_ids = set()

def fetch_clearance_items():
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('Items', [])
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return []

def send_to_discord(item):
    start_date = datetime.fromisoformat(item['StartDate'].replace("Z", "+00:00")).strftime("<t:%s:D>" % int(datetime.fromisoformat(item['StartDate'].replace("Z", "+00:00")).timestamp()))

    if 'ListPrice' in item and item['ListPrice'] and 'Minimum' in item['ListPrice'] and 'Maximum' in item['ListPrice']:
        msrp_min = item['ListPrice']['Minimum']
        msrp_max = item['ListPrice']['Maximum']
        msrp = f"${msrp_min:.2f}" if msrp_min == msrp_max else f"${msrp_min:.2f} - ${msrp_max:.2f}"
    else:
        msrp = "N/A"

    if 'SalePrice' in item and item['SalePrice'] and 'Minimum' in item['SalePrice'] and 'Maximum' in item['SalePrice']:
        sale_min = item['SalePrice']['Minimum']
        sale_max = item['SalePrice']['Maximum']
        discounted_price = f"${sale_min:.2f}" if sale_min == sale_max else f"${sale_min:.2f} - ${sale_max:.2f}"
    else:
        discounted_price = "N/A"

    embed = {
        "title": item.get('Title', 'No Title'),
        "url": item.get('Url', 'https://woot.com'),
        "thumbnail": {"url": item.get('Photo', '')},
        "fields": [
            {
                "name": "MSRP",
                "value": msrp,
                "inline": True
            },
            {
                "name": "Discounted Price",
                "value": discounted_price,
                "inline": True
            },
            {
                "name": "Category",
                "value": item.get('Categories', [])[0] if item.get('Categories') else "N/A",
                "inline": True
            },
            {
                "name": "Start Date",
                "value": start_date,
                "inline": True
            },
            {
                "name": "Fulfilled by Amazon",
                "value": "✅" if item.get('IsFulfilledByAmazon') else "❌",
                "inline": True
            },
        ],
        "color": 3447003
    }
    
    data = {"embeds": [embed]}
    
    response = requests.post(DISCORD_WEBHOOK_URL, headers={"Content-Type": "application/json"}, data=json.dumps(data))
    if response.status_code == 204:
        print(f"Sent: {item['Title']}")
    else:
        print(f"Failed to send item to Discord: {response.status_code}, {response.text}")


def main():
    while True:
        items = fetch_clearance_items()
        for item in items:
            offer_id = item['OfferId']
            if offer_id not in sent_offer_ids:
                send_to_discord(item)
                sent_offer_ids.add(offer_id)
        time.sleep(300)

if __name__ == "__main__":
    main()
