### proxyManager.py
# by Alessandro G. Magnasco 2024
# licenced under Creative Commons CC-BY-SA 4.0
# https://github.com/amagnasco/proxymanager

# concurrency
import threading
import queue
import asyncio
# HTTP
import urllib.request
from urllib.parse import urlparse
# time management
import random
import time

class ProxyManager:
    def __init__(self, threads, wait, headers, test):
        self.f = "ProxyManager"
        # conf
        self.threads = threads
        self.wait = wait
        self.headers = headers
        self.test = test
        # proxies
        self.all = queue.Queue()
        self.ready = queue.Queue()
        self.broken = queue.Queue()
        # validar setup
        if not self.validate(self.test["uri"]):
            raise Exception("Setup error: test URI invalido!")
        
    # initial load, single thread
    async def load(self, path):
        fn = self.f + " load"

        if not path:
            raise Exception(fn + " error: no hay lista de proxies!")
        print(fn + ": iniciando con " + str(self.threads) + " hilos...")
        print(fn + ": cargando lista de proxies de {}...".format(path))
        read = 0

        # load the list
        with open(path, "r") as f:
            arr = f.read().split("\n") # on line break
            if not arr:
                raise Exception(fn + " error: archivo de proxies vacio! ({})".format(path))
            for p in arr:
                if not p:
                    continue
                elif not p[0]: # skip empty
                    continue
                elif p[0] == "#": # skip comments
                    continue
                else:
                    read += 1
                    self.all.put(p)

        print(fn + ": " + str(read) + " proxies leídos de la lista...")

        # run health check multi-thread
        for _ in range(self.threads):
            threading.Thread(target=self.healthcheck).start()

    # go through all and test, thread-safe
    async def healthcheck(self):
        fn = self.f + " healthcheck"
        valid = 0
        broken = 0

        if not self.all.qsize() > 1:
            return

        print(fn + ": abriendo hilo, N=" + str(self.all.qsize()) + "...")

        while not self.all.empty():
            # pull a proxy from the list
            p = self.all.get()

            # test
            try:
                sleep = random.randint(self.test["min"], self.test["max"])
                #print(fn + ": sleeping " + str(sleep) + "s...")
                time.sleep(sleep) 
                await self.get(p, self.test["uri"])
            except Exception as err:
                #print(fn+": broken " + p + " (" + str(err) + ")")
                broken += 1
                continue
            else:
                valid += 1
                continue

        # don't throw error here
        print(fn + ": " + str(valid) + " validos, " + str(broken) + " rotos.")
        return

    # getter
    async def get(self, p, url):
        fn = self.f + " get"
        #print(fn + ": usando proxy " + p + " para url " + url + "...")

        # define usage schema
        # assuming p is valid for both
        json = {
            "http": p,
            "https": p
        }

        # configure headers
        req = urllib.request.Request(url)
        req.add_header('User-Agent', self.headers["ua"])
        req.add_header('Accept', self.headers["accept"])
        req.add_header('Accept-Language', self.headers["accept_language"])

        try:
            res = await urllib.request.urlopen(req, proxies=json)
        except:
            self.broken.put(p)
            raise Exception(fn + " error: proxy " + p + " esta roto!")
        else:
            print(fn + ": exitoso")
            self.ready.put(p)
            return res

    # process request, thread-safe
    async def req(self, url, headers):
        fn = self.f + " req"

        print(fn+"...")
        # check if URL is valid, or will blow through the list
        if not self.validate(url):
            raise Exception(fn + " error: invalid URI! (" + url + ")")

        # run through queue
        while not self.ready.empty():
            # assign a new proxy
            p = self.ready.get()
            # wait before requesting
            time.sleep(random.randint(self.wait.min, self.wait.max))
            # getter
            res = await self.get(p, validated)
            if res.status_code == 200:
                return res

        raise Exception(fn + " error: no hay proxies disponibles!")

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
        ready = self.ready.qsize()
        print(self.f + " has " + str(ready) + " proxies currently available.")
        return ready

    