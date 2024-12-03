import asyncio
import aiohttp
import json
from datetime import datetime

SENT_CAMPAIGNS_FILE = 'campaigns.json'
WEBHOOKS_CONFIG_FILE = 'webhooks_config.json'

async def load_sent_campaigns():
    try:
        with open(SENT_CAMPAIGNS_FILE, 'r') as file:
            return set(json.load(file))
    except FileNotFoundError:
        return set()

async def save_sent_campaigns(sent_campaigns):
    with open(SENT_CAMPAIGNS_FILE, 'w') as file:
        json.dump(list(sent_campaigns), file)

async def load_webhooks_config():
    try:
        with open(WEBHOOKS_CONFIG_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: {WEBHOOKS_CONFIG_FILE} not found.")
        return {"webhooks": []}

async def fetch_featured_campaigns(session, url, params):
    try:
        async with session.get(url, params=params) as response:
            return await response.json()
    except Exception as e:
        print(f"Error fetching featured campaigns: {e}")
        return None

async def send_raffle_embed(session, campaign, webhook):
    end_time = campaign['ends_at'].split('.')[0]
    formatted_end_time = datetime.fromisoformat(end_time).timestamp()

    campaign_type = campaign['campaign_type']
    if campaign_type == "ContestGroup":
        campaign_type = "Contest Group"

    embed_data = {
        "title": campaign['title'],
        "url": campaign['url'],
        "fields": [
            {"name": "Ends at", "value": f"<t:{int(formatted_end_time)}:D>", "inline": True},
            {"name": "Campaign Type", "value": campaign_type, "inline": True}
        ],
        "thumbnail": {"url": campaign['logo']},
        "image": {"url": campaign['large_photo']},
        "color": webhook.get("color", 0xBE9F55),
        "author": {
            "name": webhook['author'].get("name", ""),
            "icon_url": webhook['author'].get("icon_url", "")
        },
        "footer": {
            "text": webhook['footer'].get("text", ""),
            "icon_url": webhook['footer'].get("icon_url", "")
        }
    }

    embed_data = {k: v for k, v in embed_data.items() if v}

    payload = {"embeds": [embed_data]}
    headers = {"Content-Type": "application/json"}

    success = False

    try:
        async with session.post(webhook['url'], data=json.dumps(payload), headers=headers) as response:
            if response.status == 204:
                success = True
            else:
                print(f"Failed to send the embed to Discord. Status Code: {response.status}")
    except Exception as e:
        print(f"Error sending raffle embed: {e}")

    if success:
        print("Successfully sent the embed to Discord.")


async def check_and_send_raffle():
    SENT_CAMPAIGNS = await load_sent_campaigns()
    webhooks_config = await load_webhooks_config()

    url = 'https://api.tunespeak.com/featured_campaigns'
    params = {'limit': '6'}

    async with aiohttp.ClientSession() as session:
        while True:
            data = await fetch_featured_campaigns(session, url, params)
            if not data:
                await asyncio.sleep(3600)
                continue

            new_campaigns = [campaign for campaign in data['featured_campaigns'] if campaign['id'] not in SENT_CAMPAIGNS]

            if new_campaigns:
                print(f"New campaigns found: {len(new_campaigns)}")
                for campaign in new_campaigns:
                    for webhook in webhooks_config['webhooks']:
                        await send_raffle_embed(session, campaign, webhook)
                    SENT_CAMPAIGNS.add(campaign['id'])
                await save_sent_campaigns(SENT_CAMPAIGNS)
            else:
                print("No new campaigns found.")

            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(check_and_send_raffle())
