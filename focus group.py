import requests
import json
import html
from discord import Webhook, Embed, RequestsWebhookAdapter
import base64
from datetime import datetime, timedelta
import time

webhook_urls = [
    'WEBHOOKS HERE'
]

sent_focus_groups_file = 'sent_focus_groups.json'

bot_image_url = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQPDvWfbQKRrZ-8ucuSu370Pg4zPudgoOeckAxcfuqtLwOe3Tv2GZ3mX9ixb3TG2P3zVXw&usqp=CAU'
bot_name = 'Focus Groups Monitor'

def load_sent_focus_groups():
    try:
        with open(sent_focus_groups_file, 'r') as file:
            return set(json.load(file))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_sent_focus_groups(sent_focus_groups):
    with open(sent_focus_groups_file, 'w') as file:
        json.dump(list(sent_focus_groups), file)

def fetch_data():
    url = 'https://focusgroups.org/c-api/v1/focusgroups/active/'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None

def create_discord_embed(focusgroup_data, bot_name, bot_image_url):
    title = focusgroup_data.get("title")
    url = focusgroup_data.get("registration_link")
    description = html.unescape(focusgroup_data.get("long_description", ""))
    description = description.replace("<p>", "").replace("</p>", "").replace("<em>", "").replace("</em>", "").replace("<br />", "\n")
    payout = focusgroup_data.get("pay_display")
    image_url = focusgroup_data.get("image_dims_2x1", {}).get("1072x563", "")
    
    expire_at = focusgroup_data.get("expire_at")
    publish_at = focusgroup_data.get("publish_at")

    embed = Embed(
        title=title,
        description=description,
        url=url,
        color=0x7289da
    )

    embed.set_author(name=bot_name, icon_url=bot_image_url)

    embed.add_field(name="Payout", value=f"{payout}", inline=True)
    embed.add_field(name="Publish Date", value=f"<t:{int(datetime.fromisoformat(publish_at).timestamp())}:f>", inline=True)
    embed.add_field(name="Expire Date", value=f"<t:{int(datetime.fromisoformat(expire_at).timestamp())}:f>", inline=True)
    embed.set_image(url=image_url)

    return embed



def send_discord_message(webhook_url, embed, username, avatar_url):
    try:
        webhook = Webhook.from_url(webhook_url, adapter=RequestsWebhookAdapter())
        webhook.send(embed=embed, username=username, avatar_url=avatar_url)
    except Exception as e:
        print(f"Error sending Discord message: {e}")

def image_to_base64(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        return base64.b64encode(response.content).decode('utf-8')
    return None

def check_and_send_new_focus_groups():
    print("Checking for new focus groups...")
    sent_focus_groups = load_sent_focus_groups()
    data = fetch_data()

    if data:
        for focusgroup_id, focusgroup_data in data.get("focusgroups", {}).items():
            if focusgroup_id not in sent_focus_groups:
                print(f"New focus group found! {focusgroup_id} added to the JSON file")
                sent_focus_groups.add(focusgroup_id)

                save_sent_focus_groups(sent_focus_groups)

                print(f"Sending Discord embed for focus group: {focusgroup_id}")

                embed = create_discord_embed(focusgroup_data, bot_name, bot_image_url)

                for idx, webhook_url in enumerate(webhook_urls):
                    print(f"Using webhook index: {idx}")
                    print(f"Webhook URL: {webhook_url}")

                    send_discord_message(webhook_url, embed, bot_name, bot_image_url)



def main():
    check_and_send_new_focus_groups()

    while True:
        check_and_send_new_focus_groups()
        time.sleep(30)

if __name__ == "__main__":
    main()