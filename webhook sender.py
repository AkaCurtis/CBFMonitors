import asyncio
from discord_webhook import DiscordWebhook, DiscordEmbed

common_info = {
    "title": input("Enter Title: "),
    "msrp": input("Enter MSRP: $"),
    "lowest_price": input("Enter Lowest Price: $"),
    "sku": input("Enter SKU: "),
    "upc": input("Enter UPC: "),
    "image_url": input("Enter Image URL: "),
    "store": input("Enter the Store: ")
}



webhook_settings = [
    {
        "url": "WEBHOOK_URL",
        "author_text": "AUTHOR_TEXT_HERE",
        "footer_text": "FOOTER_TEXT_HERE",
        "author_icon_url": "IMAGE URL HERE",
        "footer_icon_url": "IMAGE URL HERE",
        "color": 0xfffff
    },
]

async def send_embed(webhook_url, author_text, footer_text, author_icon_url, footer_icon_url, color):
    webhook = DiscordWebhook(url=webhook_url, content=common_info["sku"])

    embed = DiscordEmbed(
        title=common_info["title"],
        color=color,
    )

    embed.set_author(name=author_text, icon_url=author_icon_url)

    embed.set_footer(text=footer_text, icon_url=footer_icon_url)

    embed.set_image(url=common_info["image_url"])

    embed.add_embed_field(name="MSRP", value="$" + common_info["msrp"], inline=True)
    embed.add_embed_field(name="As low as", value="$" + common_info["lowest_price"], inline=True)

    embed.add_embed_field(name="UPC", value=common_info["upc"], inline=True)

    embed.add_embed_field(name="Store", value=common_info["store"], inline=True)

    webhook.add_embed(embed)

    webhook.execute()

async def main():
    for settings in webhook_settings:
        await send_embed(
            settings["url"],
            settings["author_text"],
            settings["footer_text"],
            settings["author_icon_url"],
            settings["footer_icon_url"],
            settings["color"]
        )

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
