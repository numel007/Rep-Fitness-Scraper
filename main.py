import requests
import re
from bs4 import BeautifulSoup as bs
import html5lib
import pprint

# Load the webpage content
r = requests.get("https://www.repfitness.com/in-stock-items?product_list_limit=12")

# Convert to a beautiful soup object
page_content = bs(r.content, features="html5lib")

all_items = page_content.select('li.item.product.product-item')

for item in all_items:
  item_link = item.select('a.product-item-link')
  print(item_link[0].string.strip())

  prices = item.select('div.price-box.price-final_price')
  price_from = prices[0].select('p.price-from span.price')
  price_to = prices[0].select('p.price-to span.price')

  try:
    print(f"{price_from[0].string} - {price_to[0].string}\n")
  except IndexError:

    try:
      minimal_price = prices[0].select('p.minimal-price span.price')
      print(minimal_price[0].string + "\n")
    except IndexError:

      try:
        normal_price = prices[0].select('span.normal-price span.price')
        print(normal_price[0].string + "\n")
      except IndexError:
        final_price = prices[0].select('span.price')
        print(final_price[0].string + "\n")