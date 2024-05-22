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

def save_results(results):
    """ Function to save results in database to compare in future and search for price fluctuations """
    data = {"results": results}
    FILE = os.path.join("Scraper", "results.json")
    with open(FILE, "w") as f:
        json.dump(data, f)

def post_results(results, endpoint, search_text, source):
    """ function that posts results to the specified endpoint """
    headers = {
        "Content-Type": "application/json" # define headers for the HTTP request,content should be in json
    }
    # create dictionary data containing the search results (results), the search text (search_text), and the source (source)
    data = {"data": results, "search_text": search_text, "source": source}

    print("Sending request to", endpoint)
    response = post("http://localhost:5000" + endpoint,
                    headers=headers, json=data) # send a POST request to the endpoint with the headers and data
    print("Status code:", response.status_code)


async def main(url, search_text, response_route):
    """ Input:
    url: specified url we want to scrape(in our case AMAZON)
    search_text: the product user wants to search for
    response_route: the route to which the results will be posted
    """
    metadata = URLS.get(url) # get url of the website
    if not metadata:
        print("Invalid URL.")
        return

    async with async_playwright() as pw:
        """ create an async context using Playwright, a tool for automating browsers """
        print('Connecting to browser.')
        browser = await pw.chromium.connect_over_cdp(browser_url) # this connects chromium browser to the specified browser_url
        page = await browser.new_page() # creates a new browser tab (page) for the scraping process
        print("Connected.")
        await page.goto(url, timeout=120000) # navigates the page to the specified url with a timeout of 120 seconds
        print("Loaded initial page.")
        search_page = await search(metadata, page, search_text) # get the search page

        def func(x): return None

        if url == AMAZON:
            func = get_amazon_product
        else:
            raise Exception('Invalid URL')

        # call the get_products function to extract product information from the search results page
        results = await get_products(search_page, search_text, metadata["product_selector"], func)
        print("Saving results.")
        # post results to the specific response_router
        post_results(results, response_route, search_text, url)

        await browser.close()
    if __name__ == "__main__":
        # test script
        asyncio.run(main(AMAZON, "GTA 5 XBOX 360"))