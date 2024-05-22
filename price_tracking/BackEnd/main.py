import asyncio
from playwright.async_api import async_playwright
import json
import os
from amazon import get_product as get_amazon_product
from requests import post

AMAZON = "https://amazon.ca"
