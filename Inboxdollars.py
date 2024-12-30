import requests
import json
import time
import random

def read_webhook_urls(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

def send_offer_to_discord(webhook_url, offer):
    offer['copy'] = offer['copy'].replace('<br>', '\n')

    payout_dollars = int(offer['points']) // 100
    payout_cents = int(offer['points']) % 100
    formatted_payout = f"${payout_dollars}.{payout_cents:02}"

    embed = {
        "title": offer['title'],
        "url": offer['url'],
        "description": offer['copy'],
        "fields": [
            {"name": "__Things to Know__", "value": "\n".join(f"- {item}" for item in offer['thingstoknow']), "inline": False},
            {"name": "__SIGN UP FOR INBOXDOLLARS FOR A $5 BONUS!__", "value": "https://www.inboxdollars.com/?rb=105207779", "inline": False},
            {"name": "__Payout__", "value": formatted_payout, "inline": False}
        ],
        "image": {"url": offer['modalimage']},
        "color": 0xfa8072,
        "author": {
            "name": "InboxDollars Monitor",
            "icon_url": "https://play-lh.googleusercontent.com/UvbDywk_Hni3GNX4Eh54X8ImqN8Lt9NGWt59TjYenz22ZgF3ID6SJINAbT2-9tmYSD-v"
        }
    }

    payload = {
        "username": "InboxDollars Bot",
        "avatar_url": "https://play-lh.googleusercontent.com/UvbDywk_Hni3GNX4Eh54X8ImqN8Lt9NGWt59TjYenz22ZgF3ID6SJINAbT2-9tmYSD-v",
        "embeds": [embed]
    }

    response = requests.post(webhook_url, json=payload)

    if response.status_code != 204:
        print(f"Failed to send offer to Discord ({webhook_url}): {response.status_code}, {response.text}")

def get_offers():
    url = 'https://api.inboxdollars.com/'
    headers = {
        'authority': 'api.inboxdollars.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.inboxdollars.com',
        'referer': 'https://www.inboxdollars.com/',
        'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    }
    params = {
        'cmd': 'mp-dis-offer-list',
    }
    data = {
        'placementType': '4800',
        'attribute': '',
        'pageSize': '1000',
        '_ajax': '1',
    }

    response = requests.post(url, headers=headers, params=params, data=data)

    if response.status_code == 200:
        return json.loads(response.text)['offers']
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return []

def check_and_send_random_offer():
    webhook_urls = read_webhook_urls('webhook_urls.txt')

    offers = get_offers()

    if not offers:
        return

    random_offer = random.choice(offers)

    offer_sent = False

    for webhook_url in webhook_urls:
        send_offer_to_discord(webhook_url, random_offer)

        offer_sent = True

    if offer_sent:
        print(f"Sent Offer: {random_offer['title']}")
        print("-" * 40)

if __name__ == "__main__":
    while True:
        check_and_send_random_offer()
        time.sleep(21600)
