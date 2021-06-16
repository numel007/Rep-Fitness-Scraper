import discord
import os
import requests
from bs4 import BeautifulSoup as bs
from datetime import datetime
from dotenv import load_dotenv

client = discord.Client()
load_dotenv()
text_channel_list = []


def scrape_category(target):
    """Scrapes a Rep page depending on user choice"""

    # Determine chosen category
    if target == "benches":
        r = requests.get(os.getenv("BENCHES_URL"))
    elif target == "racks":
        r = requests.get(os.getenv("RACKS_URL"))
    elif target == "bells":
        r = requests.get(os.getenv("BELLS_URL"))
    elif target == "bars":
        r = requests.get(os.getenv("BARS_URL"))
    elif target == "plates":
        r = requests.get(os.getenv("PLATES_URL"))

    # Initialize empty dictionaries
    in_stock_items = {}
    out_of_stock_items = []
    links = []

    # Scrape chosen page and parse listings
    page_content = bs(r.content, features="html5lib")
    all_items = page_content.select("li.item.product.product-item")

    for item in all_items:
        price = ""

        # Parse <a> from all_items
        item_link = item.find("a", attrs={"class": "product-item-link"})

        # Parse listing link, append to links list
        links.append(item_link["href"])

        # Parse listing name, will be used as a key later
        item_name = item_link.string.strip()

        # Parse price container
        prices = item.select("div.price-box.price-final_price")

        # Rep doesn't know how to build a coherent website; these try/excepts detect which
        # price container the site is using for the item
        try:
            price_from = prices[0].select("p.price-from span.price")
            price_to = prices[0].select("p.price-to span.price")
            try:
                price = (f"{price_from[0].string} - {price_to[0].string} ")
            except IndexError:

                try:
                    minimal_price = prices[0].select(
                        "p.minimal-price span.price")
                    price = minimal_price[0].string
                except IndexError:

                    try:
                        normal_price = prices[0].select(
                            "span.normal-price span.price")
                        price = (normal_price[0].string)
                    except IndexError:
                        final_price = prices[0].select("span.price")
                        price = final_price[0].string

        except:
            price = (": No price listed")

        # Parse in stock container
        in_stock = item.select("div.actions-primary span")

        # Determine if string in stock container lists as in/out of stock
        if in_stock[0].string == "Out of Stock":

            # If out of stock, add item to OOS list
            out_of_stock_items.append(item_name)
        elif in_stock[0].string == "Add to Cart":
            in_stock_items[item_name] = price

    return in_stock_items, out_of_stock_items, links


def create_message(in_stock, out_of_stock, links):
    """Builds message from scraped data"""
    message = ":white_check_mark: **IN STOCK**\n\n"

    i = 0

    # Concatenate items/prices/links for in stock items to message
    for item, price in in_stock.items():

        # Hyperlink and bold item name, price in regular text
        message += f" ✓ **[{item}:]({links[i]})** {price}\n"
        i += 1

    message += "\n\n:x:** OUT OF STOCK **\n\n"

    for item in out_of_stock:
        message += f" × {item}\n"

    return message


def create_embed(listing):

    if listing == "racks":
        in_stock, out_of_stock, links = scrape_category("racks")
        e = discord.Embed(url="https://www.repfitness.com/strength-equipment/power-racks",
                          description=create_message(in_stock, out_of_stock, links), color=0x0000ff)
        e.set_author(name="POWER/SQUAT RACKS")
        e.set_thumbnail(url=os.getenv("RACKS_THUMBNAIL"))

    elif listing == "benches":
        in_stock, out_of_stock, links = scrape_category("benches")
        e = discord.Embed(url="https://www.repfitness.com/strength-equipment/strength-training",
                          description=create_message(in_stock, out_of_stock, links), color=0x00ff0d)
        e.set_author(name="FID/FLAT BENCHES")
        e.set_thumbnail(url=os.getenv("BENCHES_THUMBNAIL"))

    elif listing == "bells":
        in_stock, out_of_stock, links = scrape_category("bells")
        e = discord.Embed(url="https://www.repfitness.com/conditioning/strength-equipment/dumbbells",
                          description=create_message(in_stock, out_of_stock, links), color=0xffff00)
        e.set_author(name="DUMBBELLS + RACKS")
        e.set_thumbnail(url=os.getenv("BELLS_THUMBNAIL"))

    elif listing == "bars":
        in_stock, out_of_stock, links = scrape_category("bars")
        e = discord.Embed(url="https://www.repfitness.com/bars-plates/olympic-bars",
                          description=create_message(in_stock, out_of_stock, links), color=0x00ffff)
        e.set_author(name="BARBELLS")
        e.set_thumbnail(url=os.getenv("BARS_THUMBNAIL"))

    elif listing == "plates":
        in_stock, out_of_stock, links = scrape_category("plates")
        e = discord.Embed(url="https://www.repfitness.com/bars-plates/olympic-plates",
                          description=create_message(in_stock, out_of_stock, links), color=0x7b00ff)
        e.set_author(name="PLATES")
        e.set_thumbnail(url=os.getenv("PLATES_THUMBNAIL"))

    e.set_footer(
        text=f'Checked {datetime.utcnow().strftime("%H:%M:%S")} UTC')

    return e


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="you UWU"))
    print("{0.user} now running\n".format(client))


@client.event
async def on_message(message):

    # Stops the bot from talking to itself
    if message.author == client.user:
        return

    if message.content.startswith("$help") or message.content.startswith("$commands"):
        commands_list = "**$racks:** Track powerracks\n**$benches:** Track FID/Flat benches\n**$bells:** Track dumbbells\n**$bars:** Track barbells\n**$plates:** Track bumper/iron plates"
        e = discord.Embed(url="https://github.com/numel007/Rep-Fitness-Scraper",
                          description=commands_list, color=0xffffff)
        await message.channel.send(embed=e)

    if message.content.startswith("$racks"):
        await message.channel.send(embed=create_embed("racks"))

    if message.content.startswith("$benches"):
        await message.channel.send(embed=create_embed("benches"))

    if message.content.startswith("$bells"):
        await message.channel.send(embed=create_embed("bells"))

    if message.content.startswith("$bars"):
        await message.channel.send(embed=create_embed("bars"))

    if message.content.startswith("$plates"):
        await message.channel.send(embed=create_embed("plates"))

client.run(os.getenv("TOKEN"))
