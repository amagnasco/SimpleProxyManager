import os
import asyncio
from proxyManager import ProxyManager

# lista de proxies
filename = "testproxies.txt"

# numero de hilos a usar
threads = 10

# tiempo de espera en segundos
wait = {
    "min": 3,
    "max": 8
}

# headers
headers = {
    "ua": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0',
    "accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    "accept_language": 'en-US,en;q=0.5'
}

# configuracion para health check
test = {
    "uri": "http://ipinfo.io/json",
    "min": 1,
    "max": 3
}

### workdir
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
filepath = os.path.join(__location__, filename)

### start
proxies = ProxyManager(threads, wait, headers, test)
await proxies.load(filepath)

# test
proxies.available()

# try to scrape an URL:
#url = "http://example.com"
#proxies.req(url)

# parse
# .read().decode(encoding)
