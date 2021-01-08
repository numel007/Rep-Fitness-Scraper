import discord
import os
import requests
import json
import random
import re
from bs4 import BeautifulSoup as bs
import html5lib
from datetime import datetime
import time
from dotenv import load_dotenv
from discord.ext import commands


client = discord.Client()
load_dotenv()
TOKEN = os.getenv('TOKEN')

sad_words = ['$sad', '$mad', '$bad']
encouragements = ["Just like... don't be sad lol", "lolwut sadboi"]

def scrape_rep():
  """Scrape Rep's in-stock page, return scraped data"""

  # Initialize empty variable to store message
  message_to_send = ""

  # Set webpage to be scraped
  r = requests.get("https://www.repfitness.com/in-stock-items?product_list_limit=12")

  # Store scraped page
  page_content = bs(r.content, features="html5lib")

  # Parse item listings from scraped data
  all_items = page_content.select('li.item.product.product-item')
  
  for item in all_items:

    # Parse <a> from all_items
    item_link = item.select('a.product-item-link')

    # Parse item name from <a> tag, append to message_to_send
    message_to_send += ("> **" + item_link[0].string.strip() + ":** ")

    # Parse price container corresponding to currently selected item
    prices = item.select('div.price-box.price-final_price')

    # Rep doesn't know how to build a coherent website; these try/excepts detect which
    # price container the site is using for the item
    try:
      price_from = prices[0].select('p.price-from span.price')
      price_to = prices[0].select('p.price-to span.price')
      try:
        message_to_send += (f"{price_from[0].string} - {price_to[0].string}\n")
      except IndexError:

        try:
          minimal_price = prices[0].select('p.minimal-price span.price')
          message_to_send += (minimal_price[0].string + "\n")
        except IndexError:

          try:
            normal_price = prices[0].select('span.normal-price span.price')
            message_to_send += (normal_price[0].string + "\n")
          except IndexError:
            final_price = prices[0].select('span.price')
            message_to_send += (final_price[0].string + "\n")

    except:
      message_to_send += ("Out of stock (Rep listed as in-stock 🤔)\n")
  
  # After all items have been parsed, return message
  return message_to_send

def scrape_benches():
  """Scrapes Rep's benches page"""

  price = ""
  in_stock_items = {}
  out_of_stock_items = {}
  links = []
  r = requests.get('https://www.repfitness.com/strength-equipment/strength-training')
  page_content = bs(r.content, features='html5lib')

  all_items = page_content.select('li.item.product.product-item')

  for item in all_items:
      item_link = item.find('a', attrs={'class': 'product-item-link'})
      item_name = ("**[" + item_link.string.strip() + f"]:** ")
      prices = item.select('div.price-box.price-final_price')
      links.append(item_link['href'])

      try:
          price_from = prices[0].select('p.price-from span.price')
          price_to = prices[0].select('p.price-to span.price')
          try:
              price = (f"{price_from[0].string} - {price_to[0].string} ")
          except IndexError:

              try:
                  minimal_price = prices[0].select('p.minimal-price span.price')
                  price = (minimal_price[0].string + " ")
              except IndexError:

                  try:
                      normal_price = prices[0].select('span.normal-price span.price')
                      price = (normal_price[0].string + " ")
                  except IndexError:
                      final_price = prices[0].select('span.price')
                      price = (final_price[0].string + " ")

      except:
          price = ("No price listed")

      add_to_cart = item.select('div.actions-primary')
      in_stock = add_to_cart[0].select('span')

      if in_stock[0].string == 'Out of Stock':
          out_of_stock_items[item_name] = price
      elif in_stock[0].string == 'Add to Cart':
          in_stock_items[item_name] = price

  return in_stock_items, out_of_stock_items, links

def scrape_racks():
  """Scrape Rep's power-racks page"""

  message_to_send = ""
  r = requests.get('https://www.repfitness.com/strength-equipment/power-racks?product_list_limit=12')
  page_content = bs(r.content, features='html5lib')

  all_items = page_content.select('li.item.product.product-item')

  for item in all_items:
    item_link = item.select('a.product-item-link')
    message_to_send += ("> **" + item_link[0].string.strip() + ":** ")
    prices = item.select('div.price-box.price-final_price')

    try:
      price_from = prices[0].select('p.price-from span.price')
      price_to = prices[0].select('p.price-to span.price')
      try:
        message_to_send += (f"{price_from[0].string} - {price_to[0].string}\n")
      except IndexError:

        try:
          minimal_price = prices[0].select('p.minimal-price span.price')
          message_to_send += (minimal_price[0].string + "\n")
        except IndexError:

          try:
            normal_price = prices[0].select('span.normal-price span.price')
            message_to_send += (normal_price[0].string + "\n")
          except IndexError:
            final_price = prices[0].select('span.price')
            message_to_send += (final_price[0].string + "\n")

    except:
      message_to_send += ("No Price Listed\n")

  return message_to_send

def get_quote():
  """Get random quote from ZenQuotes"""
  response = requests.get("https://zenquotes.io/api/random")
  json_data = json.loads(response.text)
  quote = json_data[0]['q'] + " -" + json_data[0]['a']
  return quote

@client.event
async def on_ready():
  print('{0.user} now running'.format(client))
  print('-------------------')
  print('Connected Servers:')
  for guild in client.guilds:
      print(guild.name)
  print('-------------------')

@client.event
async def on_message(message):

  # Parse discord message's content
  msg_content = message.content

  # Stops the bot from talking to itself
  if message.author == client.user:
    return

  # Respond to ping
  if client.user.mentioned_in(message) and message.mention_everyone == False:
    await message.channel.send(':eyes:')

  # Testing pinging a user
  if msg_content.startswith('$whoami'):
    await message.channel.send('You are {}.'.format(message.author.mention))

  # Testing api calls
  if msg_content.startswith('$inspire'):
    quote = get_quote()
    await message.channel.send(quote)

  if any(word in msg_content for word in sad_words):
    await message.channel.send(random.choice(encouragements))

  # Calls scrape_rep() and runs forever
  if msg_content.startswith('$rep'):
    # Set time, store scrape, set embed link
    now = datetime.now()
    old_scrape = scrape_rep()
    e = discord.Embed(title="Click For In-Stock Items", url="https://www.repfitness.com/in-stock-items?product_list_limit=12")

    # Send embed link, current time, and first scrape
    await message.channel.send(embed=e)
    await message.channel.send(f'**\nIn Stock Items:** Updated {now.strftime("%H:%M:%S")} UTC\n\n')
    await message.channel.send(old_scrape)

    # Loops and checks for changes in old vs new scrape
    while True:

      # Store second scrape
      new_scrape = scrape_rep()


      if old_scrape == new_scrape:

        # If scrapes are the same then sleep 60 seconds and repeat
        time.sleep(60)
        continue
      else:

        # If scrapes are different then send new scrape, sleep 60 seconds, and repeat
        await message.channel.send(embed=e)
        await message.channel.send(f'**\nNew Items In Stock!:** Updated {now.strftime("%H:%M:%S")} UTC\n\n')
        await message.channel.send(new_scrape)

        # Reset old_scrape with new data
        old_scrape = new_scrape
        time.sleep(60)
        continue

  if msg_content.startswith('$racks'):
    now = datetime.now()
    racks_scrape = scrape_racks()
    e = discord.Embed(title="Rep Power Racks", url="https://www.repfitness.com/strength-equipment/power-racks?product_list_limit=12")

    await message.channel.send(embed=e)
    await message.channel.send(f'**\nRep Power Racks:** Updated {now.strftime("%H:%m:%S")} UTC\n')
    await message.channel.send(racks_scrape)

  if msg_content.startswith('$benches'):
    message_to_send = ''
    now = datetime.now()
    in_stock, out_of_stock, links = scrape_benches()

    message_to_send += '**IN STOCK**\n'
    i=0
    for item, price in in_stock.items():
      message_to_send += f':white_check_mark: {item} {price} \n{links[i]}\n'
      i+=1

    message_to_send += '\n\n**OUT OF STOCK**\n'
    for item, price in out_of_stock.items():
      message_to_send += f':x: {item} {price} \n{links[i]}\n'
    
    e = discord.Embed(url="https://www.repfitness.com/strength-equipment/strength-training", description=message_to_send, color=0x23cc50)
    e.set_author(name='BENCHES', url='https://www.repfitness.com/strength-equipment/strength-training')
    e.set_thumbnail(url='https://www.repfitness.com/media/catalog/product/cache/6031cf661625f6f6abd8f87ef140b802/w/i/wide-pad.jpg')
    e.set_footer(text=f'Updated {now.strftime("%H:%m:%S")} UTC', icon_url='https://i.imgur.com/1sqNK27b.jpg')
    await message.channel.send(embed=e)

# Run run botty boi
client.run(TOKEN)