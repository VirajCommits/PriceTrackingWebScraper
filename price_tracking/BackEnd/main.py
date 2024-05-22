import asyncio
from playwright.async_api import async_playwright
import json
import os
from amazon import get_product as get_amazon_product
from requests import post

AMAZON = "https://amazon.ca"

# URLS is a dictionary that contains configuration details for interacting with Amazon's website
URLS = {
    AMAZON: {
        "search_field_query": 'input[name="field-keywords"]', # to locate the search input field where queries are to be written
        "search_button_query": 'input[value="Go"]', # to click on the search icon to begin the search
        "product_selector": "div.s-card-container" # to locate the product containers on the search results page.
    }
}

available_urls = URLS.keys()

def load_auth():
    """ Function to get the username and password(to connect with brightdata)"""
    FILE = os.path.join("Scraper", "auth.json")
    with open(FILE, "r") as f:
        return json.load(f)

# connect with brighdata
cred = load_auth()
auth = f'{cred["username"]}:{cred["password"]}'
browser_url = f'wss://{auth}@{cred["host"]}'

async def search(metadata, page, search_text):
    """ asynchronous function that performs a search on a webpage using provided metadata and search text. """

    print(f"Searching for {search_text} on {page.url}")
    search_field_query = metadata.get("search_field_query") # get the serach field
    search_button_query = metadata.get("search_button_query") # get the search button icon

    if search_field_query and search_button_query:
        print("Filling input field")
        search_box = await page.wait_for_selector(search_field_query) # wait until search field has been found
        await search_box.type(search_text) # type the query in the search box 
        print("Pressing search button")
        button = await page.wait_for_selector(search_button_query) # wait until the search icon has been found
        await button.click() # press the search button
    else:
        raise Exception("Could not search.")

    await page.wait_for_load_state() # wiat for the page to finish loading after the search button is clicked.
    return page # return the page object, which contains the search results.

async def get_products(page, search_text, selector, get_product):
    """ asynchronous function made to retrieve product information from a webpage 
        page: represents the webpage
        selector: used to identify product elements on the page
        get_product: asynchronous function that extracts product details from a product element.
        """

    print("Retreiving products.")
    product_divs = await page.query_selector_all(selector) # select all produncts on a given webpage
    valid_products = [] # to store all valid products
    words = search_text.split(" ") # to filter products based off of names

    async with asyncio.TaskGroup() as tg: # asyncio.TaskGroup is used to run multiple tasks at once
        for div in product_divs:
            async def task(p_div):
                product = await get_product(p_div) # wait until product is returned

                if not product["price"] or not product["url"]: # check if product exists
                    return

                for word in words:
                    # check if word is in a products name
                    if (not product["name"]) or (word.lower() not in product["name"].lower()):
                        break
                else:
                    # add product to vlaid_products if legit
                    valid_products.append(product)
            tg.create_task(task(div)) # create a new task in the task group tg to process the 
                                      # current product element div asynchronously.



    return valid_products