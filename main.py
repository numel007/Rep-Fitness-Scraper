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
import schedule
from multiprocessing import Process
import sys


client = discord.Client()
load_dotenv()
TOKEN = os.getenv('TOKEN')
text_channel_list = []

def scrape_category(target):
  """Scrapes a Rep page depending on user choice"""

  # Define links corresponding to categories
  benchs_url = 'https://www.repfitness.com/strength-equipment/strength-training'
  racks_url = 'https://www.repfitness.com/strength-equipment/power-racks?product_list_limit=12'
  bells_url = 'https://www.repfitness.com/conditioning/strength-equipment/dumbbells'
  bars_url = 'https://www.repfitness.com/bars-plates/olympic-bars'
  plates_url = 'https://www.repfitness.com/bars-plates/olympic-plates'
  invalid_url = 'https://www.repfitness.com/in-stock-items'
  url_to_scrape = ''

  # Determine chosen category
  if target == 'benches':
	  url_to_scrape = benchs_url
  elif target == 'racks':
	  url_to_scrape = racks_url
  elif target == 'bells':
	  url_to_scrape = bells_url
  elif target == 'bars':
	  url_to_scrape = bars_url
  elif target == 'plates':
	  url_to_scrape = plates_url
  else:
	  print('No url found for this category.')
	  url_to_scrape = invalid_url

  # Initialize empty dictionaries
  in_stock_items = {}
  out_of_stock_items = {}
  links = []

  # Scrape chosen page and parse listings
  r = requests.get(url_to_scrape)
  page_content = bs(r.content, features='html5lib')
  all_items = page_content.select('li.item.product.product-item')


  for item in all_items:
	  price = ''

	  # Parse <a> from all_items
	  item_link = item.find('a', attrs={'class': 'product-item-link'})

	  # Parse listing link, append to links list
	  links.append(item_link['href'])

	  # Parse listing name, will be used as a key later
	  item_name = ('**[' + item_link.string.strip() + f']** ')

	  # Parse price container
	  prices = item.select('div.price-box.price-final_price')

	  # Rep doesn't know how to build a coherent website; these try/excepts detect which
	  # price container the site is using for the item
	  try:
		  price_from = prices[0].select('p.price-from span.price')
		  price_to = prices[0].select('p.price-to span.price')
		  try:
			  price = (f': {price_from[0].string} - {price_to[0].string} ')
		  except IndexError:

			  try:
				  minimal_price = prices[0].select('p.minimal-price span.price')
				  price = (': ' + minimal_price[0].string + ' ')
			  except IndexError:

				  try:
					  normal_price = prices[0].select('span.normal-price span.price')
					  price = (': ' + normal_price[0].string + ' ')
				  except IndexError:
					  final_price = prices[0].select('span.price')
					  price = (': ' + final_price[0].string + ' ')

	  except:
		  price = (': No price listed')

	  # Parse in stock container
	  in_stock = item.select('div.actions-primary span')

	  # Determine if string in stock container lists as in/out of stock
	  if in_stock[0].string == 'Out of Stock':

		  # If out of stock, add item to OOS dictionary using item_name as key and price as value
		  out_of_stock_items[item_name] = price
	  elif in_stock[0].string == 'Add to Cart':
		  in_stock_items[item_name] = price

  # Return in/out of stock dictionaries and links list
  return in_stock_items, out_of_stock_items, links

def scrape_all_categories():

	#---------BENCHES---------
	benches_in_stock, benches_out_of_stock, benches_links = scrape_category('benches')
	benches_content = create_message(benches_in_stock, benches_out_of_stock, benches_links)

	#---------BELLS---------
	bells_in_stock, bells_out_of_stock, bells_links = scrape_category('bells')
	bells_content = create_message(bells_in_stock, bells_out_of_stock, bells_links)

	#---------BARS---------
	bars_in_stock, bars_out_of_stock, bars_links = scrape_category('bars')
	bars_content = create_message(bars_in_stock, bars_out_of_stock, bars_links)

	#---------RACKS---------
	racks_in_stock, racks_out_of_stock, racks_links = scrape_category('racks')
	racks_content = create_message(racks_in_stock, racks_out_of_stock, racks_links)

	#---------PLATES---------
	plates_in_stock, plates_out_of_stock, plates_links = scrape_category('plates')
	plates_content = create_message(plates_in_stock, plates_out_of_stock, plates_links)

	return benches_content, bells_content, bars_content, racks_content, plates_content

def create_message(in_stock, out_of_stock, links):
	"""Builds message from scraped data"""

	message = ':white_check_mark: **IN STOCK**\n\n'
  
	# Index indicator, used to iterate through links list
	i = 0

	# Concatenate items/prices/links for in stock items to message
	for item, price in in_stock.items():
		message += f' ✓ {item} {price} \n{links[i]}\n'
		i+=1

	message += '\n\n:x:** OUT OF STOCK **\n\n'

	# Concatenate only item (no price/links) for OOS items to message
	# This is to try to stay below Discord's 2000 char limit
	for item, price in out_of_stock.items():
		message += f' × {item}\n'

	return message

def create_racks_embed():

	# Get current time to be used as posted scrape time
	scrape_update_time = datetime.now()

	# Scrape category and store returned dictionaries and links
	in_stock, out_of_stock, links = scrape_category('racks')

	# Pass dictionaries and links into message creation method, store returned message
	description_content = create_message(in_stock, out_of_stock, links)
	
	# Create embed
	e = discord.Embed(url='https://www.repfitness.com/strength-equipment/power-racks', description=description_content, color=0x0000ff)
	e.set_author(name='POWER/SQUAT RACKS + ADDONS', url='https://www.repfitness.com/strength-equipment/power-racks')
	e.set_thumbnail(url='https://www.repfitness.com/media/catalog/product/cache/b4987f3b5df5a1097465525c4602b5fb/r/e/rep_pr-5000_v2-loaded_3__13.jpg')
	e.set_footer(text=f'Checked at {scrape_update_time.strftime("%H:%m:%S")} UTC', icon_url='https://i.imgur.com/1sqNK27b.jpg')

	return e

def create_plates_embed():
	scrape_update_time = datetime.now()
	in_stock, out_of_stock, links = scrape_category('plates')
	description_content = create_message(in_stock, out_of_stock, links)
	
	e = discord.Embed(url='https://www.repfitness.com/bars-plates/olympic-plates', description=description_content, color=0x7b00ff)
	e.set_author(name='OLYMPIC/IRON/FRACTIONAL PLATES', url='https://www.repfitness.com/bars-plates/olympic-plates')
	e.set_thumbnail(url='https://www.repfitness.com/media/catalog/product/cache/b4987f3b5df5a1097465525c4602b5fb/l/i/lightroom_retouch-2.jpg')
	e.set_footer(text=f'Checked at {scrape_update_time.strftime("%H:%m:%S")} UTC', icon_url='https://i.imgur.com/1sqNK27b.jpg')
	return e

def create_bars_embed():
	scrape_update_time = datetime.now()
	in_stock, out_of_stock, links = scrape_category('bars')
	description_content = create_message(in_stock, out_of_stock, links)

	e = discord.Embed(url='https://www.repfitness.com/bars-plates/olympic-bars', description=description_content, color=0x00ffff)
	e.set_author(name='OLYMPIC/TECHNIQUE/EZ-CURL/TRAP/POWER BARS', url='https://www.repfitness.com/bars-plates/olympic-bars')
	e.set_thumbnail(url='https://www.repfitness.com/media/catalog/tmp/category/Category_Headers-Barbells.jpg')
	e.set_footer(text=f'Checked at {scrape_update_time.strftime("%H:%m:%S")} UTC', icon_url='https://i.imgur.com/1sqNK27b.jpg')
	return e

def create_bells_embed():
	scrape_update_time = datetime.now()
	in_stock, out_of_stock, links = scrape_category('bells')
	description_content = create_message(in_stock, out_of_stock, links)

	e = discord.Embed(url='https://www.repfitness.com/conditioning/strength-equipment/dumbbells', description=description_content, color=0xffff00)
	e.set_author(name='HEX/ADJUTABLE DUMBBELLS + RACKS', url='https://www.repfitness.com/conditioning/strength-equipment/dumbbells')
	e.set_thumbnail(url='https://www.repfitness.com/media/catalog/product/cache/b4987f3b5df5a1097465525c4602b5fb/t/h/thumbnail-60_1.jpg')
	e.set_footer(text=f'Checked at {scrape_update_time.strftime("%H:%m:%S")} UTC', icon_url='https://i.imgur.com/1sqNK27b.jpg')
	return e

def create_benches_embed():
	scrape_update_time = datetime.now()
	in_stock, out_of_stock, links = scrape_category('benches')
	description_content = create_message(in_stock, out_of_stock, links)

	e = discord.Embed(url='https://www.repfitness.com/strength-equipment/strength-training', description=description_content, color=0x00ff0d)
	e.set_author(name='FID/FLAT BENCHES + ADDONS', url='https://www.repfitness.com/strength-equipment/strength-training')
	e.set_thumbnail(url='https://www.repfitness.com/media/catalog/product/cache/6031cf661625f6f6abd8f87ef140b802/w/i/wide-pad.jpg')
	e.set_footer(text=f'Checked at {scrape_update_time.strftime("%H:%m:%S")} UTC', icon_url='https://i.imgur.com/1sqNK27b.jpg')
	return e

def scrape_every_n_seconds():
	bench_1, bells_1, bars_1, racks_1, plates_1 = scrape_all_categories()
	print('Sleeping 60 seconds...')
	time.sleep(60)

	bench_2, bells_2, bars_2, racks_2, plates_2 = scrape_all_categories()

	changes_list = []

	if bench_1 == bench_2:
		changes_list.append(False)
	else:
		changes_list.append(True)

	if bells_1 == bells_2:
		changes_list.append(False)
	else:
		changes_list.append(True)

	if bars_1 == bars_2:
		changes_list.append(False)
	else:
		changes_list.append(True)

	if racks_1 == racks_2:
		changes_list.append(False)
	else:
		changes_list.append(True)

	if plates_1 == plates_2:
		changes_list.append(False)
	else:
		changes_list.append(True)
	
	return changes_list

@client.event
async def on_ready():
	await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='you UWU'))
	print('{0.user} now running\n'.format(client))
	print('Connected Servers:')
	print('-------------------')
	for guild in client.guilds:
		print(guild.name)
	print('\n')

	# Retrieve list of channels bot is running in
	for guild in client.guilds:
		for channel in guild.text_channels:
			text_channel_list.append(channel)

@client.event
async def on_message(message):

  	# Stops the bot from talking to itself
	if message.author == client.user:
		return

  	# Respond to ping
	if client.user.mentioned_in(message) and message.mention_everyone == False:
		await message.channel.send(':eyes:')

	if message.content.startswith('$help') or message.content.startswith('$commands'):
		commands_list = "**$racks:** Track powerracks page\n**$benches:** Track FID/Flat benches page\n**$bells:** Track dumbbells page\n**$bars:** Track barbells page\n**$plates:** Track bumper/iron plates page\n**$track-all:** Track all categories"
		e = discord.Embed(url='https://github.com/numel007/Rep-Fitness-Scraper', description=commands_list, color=0xffffff)
		e.set_author(name='Rep Fitness Tracker', url='https://www.repfitness.com/')
		e.set_thumbnail(url='https://img.icons8.com/fluent/344/github.png')
		e.set_footer(text='Updated 1/9/21', icon_url='https://i.imgur.com/1sqNK27b.jpg')
		await message.channel.send(embed=e)

  	# Testing pinging a user
	if message.content.startswith('$whoami'):
		await message.channel.send('You are {}.'.format(message.author.mention))

	if message.content.startswith('$racks'):
		await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='powercages/racks'))
		e = create_racks_embed()
		await message.channel.send(embed=e)
		await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='you UWU'))

	if message.content.startswith('$benches'):
		await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='FID/flat benches'))
		e = create_benches_embed()
		await message.channel.send(embed=e)
		await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='you UWU'))

	if message.content.startswith('$bells'):
		await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='dumbbells'))
		e = create_bells_embed()
		await message.channel.send(embed=e)
		await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='you UWU'))

	if message.content.startswith('$bars'):
		await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='olympic bars'))
		e = create_bars_embed()
		await message.channel.send(embed=e)
		await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='you UWU'))

	if message.content.startswith('$plates'):
		await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='bumper/iron plates'))
		e = create_plates_embed()
		await message.channel.send(embed=e)
		await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='you UWU'))

	if message.content.startswith('$track-all'):
		await message.channel.send("**NOW TRACKING ALL CATEGORIES \n WARNING: The dev is stupid and hasn't figured out how to kill this loop once it starts. Contact dev to restart.**")
		await message.channel.send('Checking for stock changes every 60 seconds.')
		await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='All Rep Pages'))

		while True:
			changes_list = scrape_every_n_seconds()
			print(changes_list)

			i = 0
			for change in changes_list:
				if change == False:
					pass
				else:
					
					if i == 0:
						e = create_benches_embed()
						await message.channel.send(embed=e)
						print('Benches inventory changed')

					elif i == 1:
						e = create_bells_embed()
						await message.channel.send(embed=e)
						print('Dumbbells inventory changed')

					elif i == 2:
						e = create_bars_embed()
						await message.channel.send(embed=e)
						print('Barbells inventory changed')

					elif i == 3:
						e = create_racks_embed()
						await message.channel.send(embed=e)
						print('Racks inventory changed')

					elif i == 4:
						e = create_plates_embed()
						await message.channel.send(embed=e)
						print('Plates inventory changed')
				i += 1

client.run(TOKEN)