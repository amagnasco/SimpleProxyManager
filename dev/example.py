# this is an example file for development purposes

#################
#    IMPORTS    #
#################

import os
from SimpleProxyManager import ProxyManager

#################
#   SETTINGS    #
#################

# list of proxies
filename = "proxies.txt"

# number of threads to use
threads = 100

# wait time in seconds
wait = {
    "min": 3,
    "max": 8,
    "timeout": 3
}

# query headers
headers = {
    "ua": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0',
    "accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    "accept_language": 'en-US,en;q=0.5'
}

# configuration for health check
# min and max are wait time in seconds, usually shorter than prod
test = {
    "uri": "http://books.toscrape.com/",
    "min": 1,
    "max": 3
}

# example test URL to scrape
url = "http://books.toscrape.com/catalogue/page-{}.html"
pages = 10
encoding = 'latin1'

#################
#     USAGE     #
#################

print('>> Welcome to the example for SimpleProxyManager.py!')

# set workdir
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
filepath = os.path.join(__location__, filename)

# start
print('>> Starting up proxy management system...')
proxies = ProxyManager(threads, wait, headers, test)
proxies.load(filepath)

# stoplight
print('>> Waiting for system to be ready...')
ready = False
while ready == False:
    p = proxies.available()
    if p >= 1:
        ready = True

# set up URLs
urls = []
for i in range(2, pages):
    urls.append(url.format(i))
print(urls)

# test URLs
print('>> Scraping test URLs (single thread)...')
scraped = []
for p in urls:
    try:
        page = proxies.req(p)
    
        if page['success'] == False:
            raise Exception(str(page['error']))

        decoded = page['data'].read().decode(encoding)
        #print(decoded)
        scraped.append(decoded)
        print("Successfully scraped page " + str(p))
    except Exception as err:
        print("Couldn't scrape page " + str(p) + ": " + str(err))

print('>> Example completed!')