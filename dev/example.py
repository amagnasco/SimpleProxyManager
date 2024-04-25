# this is an example file for development purposes

### IMPORTS
import os
from SimpleProxyManager.SimpleProxyManager import SimpleProxyManager

### SETTINGS

# list of proxies
filename = "proxies.txt"

# number of threads to use
threads = 10

# wait time in seconds
wait = {
    "min": 3,
    "max": 8
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

### USAGE

# set workdir
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
filepath = os.path.join(__location__, filename)

# start
proxies = SimpleProxyManager(threads, wait, headers, test)
proxies.load(filepath)

# test -- breaks async
#proxies.available()

# query an URL:
#url = "http://example.com"
#proxies.req(url)

# parse
# .read().decode(encoding)
