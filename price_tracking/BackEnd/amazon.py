from asyncio import gather

async def get_stock(product_div):
    """ get_stock asynchronous function that finds and return elements related 
        to stock information within a given product_div element """
    elements = await product_div.query_selector_all('.a-size-base') # select elements within product_div that has class a_size_base
    filtered_elements = [element for element in elements if 'stock' in await element.inner_text()] # Include products with "stock" to check wheteher product is in stock or not
    return filtered_elements

async def get_product(product_div):
    """ Function that gets the image , product name , product price , product url 
        of a particular product and returns it """
    # Query for all elements at once
    image_element_future = product_div.query_selector('img.s-image') # select image element with class 's-image'
    name_element_future = product_div.query_selector(
        'h2 a span') # selects product name that matches selector 'h2 a span 
    price_element_future = product_div.query_selector('span.a-offscreen') # selcts price of the element
    url_element_future = product_div.query_selector(
        'a.a-link-normal.s-no-hover.s-underline-text.s-underline-link-text.s-link-style.a-text-normal') # get url of product
    
    # Await for the completion of all queries mentioned above
    image_element, name_element, price_element, url_element = await gather(
        image_element_future,
        name_element_future,
        price_element_future,
        url_element_future,
    )

    # Fetch all attributes and text at once
    image_url = await image_element.get_attribute('src') if image_element else None
    product_name = await name_element.inner_text() if name_element else None
    try:
         #fetch inner text, remove characters ("$" and ","), strip whitespaces, and convert the resulting string to a float.
        print((await price_element.inner_text()).replace("$", "").replace(",", "").strip())
        product_price = float((await price_element.inner_text()).replace("$", "").replace(",", "").strip()) if price_element else None
    except:
        product_price = None
    product_url = "/".join((await url_element.get_attribute('href')).split("/")[:4]) if url_element else None

    return {"img": image_url, "name": product_name, "price": product_price, "url": product_url}

   