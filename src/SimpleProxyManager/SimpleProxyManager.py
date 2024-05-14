# SimpleProxyManager.py
# by Alessandro G. Magnasco 2024
# licenced under GNU GPL
# https://github.com/amagnasco/SimpleProxyManager
# https://pypi.org/project/SimpleProxyManager/

# concurrency
from concurrent.futures import ThreadPoolExecutor
import asyncio
import uvloop
import queue
# HTTP
import aiohttp
from aiohttp_requests import requests
from urllib.parse import urlparse
# utilities
import random
import re
from functools import partial

class ProxyManager:
    def __init__(self, threads, wait, test):
        self.f = "ProxyManager"
        # conf
        self.threads = threads
        self.wait = wait
        self.test = test
        # warp time
        self.loop = uvloop.new_event_loop()
        asyncio.set_event_loop(self.loop)
        # proxies
        self.unprocessed = queue.Queue()
        self.http = queue.Queue()
        self.https = queue.Queue()
        self.ftp = queue.Queue()
        self.any = queue.Queue()
        self.broken = queue.Queue()
        # ensure test URI is not broken
        if not self.validate(self.test["uri"]):
            raise Exception("Setup error: invalid test URI!")
        
    # load a list of proxies
    async def load(self, path):
        fn = self.f + " load"

        if not path:
            raise Exception(fn + " error: no list of proxies!")
        print(fn + ": starting with " + str(self.threads) + " threads...")
        print(fn + ": loading proxy list from {}...".format(path))
        read = 0

        # load the list
        with open(path, "r") as f:
            arr = f.read().split("\n") # on line break
            if not arr:
                raise Exception(fn + " error: proxy file is empty! ({})".format(path))
            for p in arr:
                if not p:
                    continue
                elif not p[0]: # skip empty
                    continue
                elif p[0] == "#": # skip comments
                    continue
                else:
                    read += 1
                    self.unprocessed.put(p)

        print(fn + ": " + str(read) + " proxies read from the list...")
        n_per_thread = self.unprocessed.qsize()/self.threads
        print(fn + ": each thread should test about ~" + str(n_per_thread) + " proxies...")
        maxtime = (n_per_thread*(self.test['max']))
        if maxtime > 60:
            print(fn + ": this should take less than " + str("{0:.2f}".format(maxtime/60)) + "m...")
        else:
            print(fn + ": this should take less than " + str("{0:.2f}".format(maxtime)) + "s...")

        # run health check multi-thread
        await self.healthcheck()
        # print available proxies
        self.available()

    # go through unprocessed and test, thread-safe
    async def healthcheck(self):
        fn = self.f + " healthcheck"
        while not self.unprocessed.empty():
            requests = [self.test["uri"] * self.unprocessed.qsize()]
            # run a time loop using test-specific values across all unprocessed proxies
            # currently does not validate schema
            await self.__loopy_manager(requests, self.__individualcheck)
        return

    async def __individualcheck(self, testuri):
        try:
            # pull a proxy from unprocessed
            p = self.unprocessed.get()
            # use test-specific sleep times
            await asyncio.sleep(random.randint(self.test["min"], self.test["max"])) 
            # use test-specific URI for getter
            return await self.get(p, testuri)
        except Exception as err:
            return # skip errors

    # getter
    async def get(self, p, uri, h):
        fn = self.f + " get"
        try:
            res = await requests.get(uri, headers=h, proxies=p, timeout=self.wait['timeout'])
        except Exception as err:
            self.broken.put(p)
            raise Exception(fn + " error! using proxy " + p + " for " + uri + ". Trace: " + str(err))
        else:
            self.__replace(p)
            return res

    # process request, thread-safe
    async def req(self, request):
        fn = self.f + " req"
        try:
            uri = request['uri']
            headers = request['headers']
            # check if URL is valid, or will blow through the list
            if not self.validate(uri):
                raise Exception(fn + " error: invalid URI! (" + uri + ")")

            # determine schema
            schema = urlparse(uri).scheme
            queue = None
            if schema == "http":
                queue = self.http
            elif schema == "https":
                queue = self.https
            elif schema == "ftp":
                queue = self.ftp
            else:
                raise Exception(fn + " error: invalid schema!")

            # run through queue
            while not queue.empty():
                # assign a new proxy
                p = queue.get()
                # wait before requesting
                await asyncio.sleep(random.randint(self.wait['min'], self.wait['max']))
                # getter
                try:
                    res = await self.get(p, uri, headers)
                except Exception as err:
                    raise Exception(fn + " error: trace: " + str(err))
                else:
                    return {"success": True, "data": res}

            raise Exception(fn + " error: no proxies available!")
        except Exception as err:
            return {"success": False, "error": err}

    # process a pile of requests concurrently
    # requests are {uri: uri, headers: headers}
    # returns all at once in original order
    async def multiple(self, requests):
        return await self.__loopy_manager(requests, self.req)

    # run async coroutines
    async def __loopy_manager(self, requests, reqfn):
        # establish scope of work
        tasks = [reqfn(request) for request in requests]
        # kick-start the continuum
        return await asyncio.gather(*tasks)
 
    # validate URIs
    def validate(self, uri):
        #print("validating "+uri+"...")
        try:
            result = urlparse(uri)
            return all([result.scheme, result.netloc])
        except AttributeError:
            return False

    # check number of proxies that are ready
    def available(self):
        http = self.http.qsize()
        https = self.https.qsize()
        ftp = self.ftp.qsize()
        any = self.any.qsize()
        broken = self.broken.qsize()
        ready = http+https+ftp+any
        if ready > 1:
            print(self.f + " has " + str(any) + " any, "+ str(http) + " http, " + str(https) + " https, " + str(ftp) + " ftp, " + str(broken) + " broken proxies currently available.")
            return ready
        else:
            return 0

    # list broken proxies by cycling through FIFO
    def listbroken(self):
        arr = []
        for p in range(0, self.broken.qsize()):
            b = self.broken.get()
            arr.push(b)
            self.broken.put(b)
        print(self.f + " has " + str(arr.length) + " broken proxies: " + str(arr))
        return arr

    # classify proxy by schema and replace in correct queue
    def __replace(self, p):
        formatted = self.findschema(p)
        if formatted is None:
            self.broken.put(p)
        else:
            schema = formatted.group()
            if schema == "http":
                self.http.put(p)
            elif schema == "https":
                self.https.put(p)
            elif schema == "ftp":
                self.ftp.put(p)
            else:
                self.any.put(p)

    # regex to determine proxy schema
    def findschema(self,p):
        # ensures it follows format "(schema://)ip(:port)"
        format = r"^((ftp|http|https)(?:\:\/\/)){0,1}(?:\d{1,3}(?:\.|\b)){3}(?:\d{1,3}(?:\:|\b)){1}(?:\d{0,8})$"
        return re.search(format,p)
