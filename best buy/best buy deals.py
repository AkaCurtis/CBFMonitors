import aiohttp
import asyncio
import json
import os
import requests
import time
from datetime import datetime, timedelta
import urllib.parse

API_KEYS = [
    'qhqws47nyvgze2mq3qx4jadt',
    'Q7rwdCDZnWPly3KzbG1KNR5F',
    'bsxgt8s4ytx7ywvg33c8tdzy',
    '08JJS1ffSirGzNn7hMjRcjBN',
    'bvn7tg3ftneqbun2h67ae7nu',
    'zbjjfx6y76g5mmp3znsetnqn',
    '0j7iapqW9cMtP87GqDaxc2Um',
    'xlTM7AGGKuDAXQEGNYD9xlY7',
    'xZzirguQPULirOqbS2fmmGuG',
    'Wh7VlBmPrUz0MoDD7PvT0072'
]

BASE_URL = "https://api.bestbuy.com/v1/products"

api_key_index = 0
api_call_counts = {key: 0 for key in API_KEYS}
KEY_DAILY_LIMIT = 50000
REQUEST_DELAY = 1

if os.path.exists('sku_tracker.json'):
    with open('sku_tracker.json', 'r') as f:
        sku_tracker = json.load(f)
else:
    sku_tracker = {}

async def fetch_json(session, url):
    async with session.get(url) as response:
        return await response.json()

async def fetch_products(session, category_id):
    global api_key_index

    while True:
        current_key = API_KEYS[api_key_index]
        if api_call_counts[current_key] >= KEY_DAILY_LIMIT:
            print(f"API key {current_key} reached daily limit, switching keys.")
            api_key_index = (api_key_index + 1) % len(API_KEYS)
            current_key = API_KEYS[api_key_index]

        url = f"{BASE_URL}(onSale=true&onlineAvailability=true&percentSavings>70&(categoryPath.id={category_id}))?apiKey={current_key}&sort=name.asc&show=url,name,image,regularPrice,onSale,salePrice,upc,percentSavings,dollarSavings&pageSize=100&format=json"

        try:
            data = await fetch_json(session, url)
            api_call_counts[current_key] += 1

            if ('errorCode' in data and data['errorCode'] == '403') or (
                'errorMessage' in data and "daily" in data['errorMessage'].lower()):
                
                print(f"API key {current_key} rate-limited. Response: {data}")
                api_key_index = (api_key_index + 1) % len(API_KEYS)
                await asyncio.sleep(5)

            else:
                await asyncio.sleep(REQUEST_DELAY)
                return data

        except Exception as e:
            print(f"Failed to fetch data: {e}")
            await asyncio.sleep(5)

async def send_to_discord(product, webhooks, category_id):
    sku = product['upc']
    discount_percentage = product['percentSavings']
    dollar_savings = product['dollarSavings']

    if sku in sku_tracker and sku_tracker[sku] == discount_percentage:
        return

    embed = {
        "title": product['name'],
        "url": product['url'],
        "thumbnail": {"url": product['image']},
        "fields": [
            {"name": "MSRP", "value": f"${product['regularPrice']:.2f}", "inline": True},
            {"name": "Sale Price", "value": f"${product['salePrice']:.2f}", "inline": True},
            {"name": "Percent Savings", "value": f"{product['percentSavings']}%", "inline": True},
            {"name": "Dollar Savings", "value": f"${dollar_savings:.2f}", "inline": True},
            {"name": "Category ID", "value": category_id, "inline": True},
            {
                "name": "Other Stores",
                "value": f"[Amazon](https://www.amazon.com/s?k={product['upc']}) | "
                        f"[Walmart](https://www.walmart.com/search?q={urllib.parse.quote(product['name'])}) | "
                        f"[eBay](https://www.ebay.com/sch/i.html?_nkw={product['upc']}&LH_Sold=1)",
                "inline": False
            }
        ],
        "footer": {
            "text": "Best Buy Deals Monitor",
            "icon_url": "https://logodownload.org/wp-content/uploads/2020/05/best-buy-logo.png"
        },
        "color": 0xFFFF00
    }

    for webhook_url in webhooks:
        try:
            response = requests.post(webhook_url, json={"embeds": [embed]})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to send to webhook: {webhook_url}\nError: {e}")

    sku_tracker[sku] = discount_percentage
    with open('sku_tracker.json', 'w') as f:
        json.dump(sku_tracker, f)

async def scrape_best_buy_deals_from_txt():
    async with aiohttp.ClientSession() as session:
        with open('ids.txt', 'r') as idfile:
            category_ids = [line.strip() for line in idfile.readlines()]

        with open('webhooks.txt', 'r') as f:
            webhooks = [line.strip() for line in f.readlines() if line.strip()]

        for category_id in category_ids:
            while True:
                await asyncio.sleep(REQUEST_DELAY)

                data = await fetch_products(session, category_id)
                if 'errorCode' not in data or data['errorCode'] != '403':
                    break
                
                print(f"Rate-limited for category {category_id}, switching keys and retrying...")
                await asyncio.sleep(5)

            deals_in_category = data.get('products', [])
            for deal in deals_in_category:
                await send_to_discord(deal, webhooks, category_id)

async def main():
    while True:
        await scrape_best_buy_deals_from_txt()
        print("Waiting for the next check...")
        await asyncio.sleep(1200)

if __name__ == "__main__":
    asyncio.run(main())