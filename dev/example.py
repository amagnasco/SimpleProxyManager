# this is an example file for development purposes

#################
#    IMPORTS    #
#################

import asyncio
import os
from SimpleProxyManager import ProxyManager

#################
#   SETTINGS    #
#################

# list of proxies
filename = "proxies.txt"

# example URL to scrape
url = "http://books.toscrape.com/catalogue/page-{}.html"
pages = 10
encoding = 'utf-8'

#################
#     USAGE     #
#################

async def example():
    print('>> Welcome to the example for SimpleProxyManager.py!')

    # set workdir
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    filepath = os.path.join(__location__, filename)

    # start
    print('>> Starting up proxy management system...')
    proxies = ProxyManager()
    await proxies.load(filepath)

    # stoplight
    print('>> Waiting for system to be ready...')
    ready = False
    while not ready:
        p = proxies.available()
        if p >= 1:
            ready = True

    # set up URLs
    urls = []
    for i in range(2, pages):
        urls.append({uri: url.format(i), headers: headers})
    print(urls)

    # test URLs
    print('>> Scraping test URLs...')
    requests = await proxies.multiple(urls)
    scraped = []
    for page in requests:
        try:    
            if not page['success']:
                raise Exception(str(page['error']))
            # process
            decoded = page['data'].read().decode(encoding)
            scraped.append(decoded)
            print("Successfully scraped page " + str(p))
        except Exception as err:
            print("Couldn't scrape page " + str(p) + ": " + str(err))

    print('>> Example completed!')

asyncio.run(example())