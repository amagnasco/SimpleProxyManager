### SimpleProxyManager.py
# by Alessandro G. Magnasco 2024
# licenced under GNU GPL
# https://github.com/amagnasco/SimpleProxyManager
# https://pypi.org/project/SimpleProxyManager/

# concurrency
import threading
import queue
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
    def load(self, path):
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
        n_per_thread = self.all.qsize()/self.threads
        print(fn + ": each thread should test about ~" + str(n_per_thread) + " proxies...")
        maxtime = (n_per_thread*(self.test['max']))
        if maxtime > 60:
            print(fn + ": this should take less than " + str("{0:.2f}".format(maxtime/60)) + "m...")
        else:
            print(fn + ": this should take less than " + str("{0:.2f}".format(maxtime)) + "s...")

        # collect the threads to use
        threads = []

        # run health check multi-thread
        for _ in range(self.threads):
            thread = threading.Thread(target=self.healthcheck)
            thread.start()
            threads.append(thread)

        # wait for threads to complete
        for thread in threads:
            thread.join()

        # print available proxies
        self.available()

    # go through all and test, thread-safe
    def healthcheck(self):
        fn = self.f + " healthcheck"
        valid = 0
        broken = 0

        if not self.all.qsize() > 1:
            return

        #print(fn + ": abriendo hilo, N=" + str(self.all.qsize()) + "...")

        while not self.all.empty():
            # pull a proxy from the list
            p = self.all.get()

            # test
            try:
                sleep = random.randint(self.test["min"], self.test["max"])
                #print(fn + ": sleeping " + str(sleep) + "s...")
                time.sleep(sleep) 
                self.get(p, self.test["uri"])
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
    def get(self, p, uri):
        fn = self.f + " get"
        #print(fn + ": usando proxy " + p + " para url " + uri + "...")

        # define usage schema
        # assuming p is valid for both
        json = {
            "http": p,
            "https": p
        }

        # configure proxy
        proxy_support = urllib.request.ProxyHandler(json)
        opener = urllib.request.build_opener(proxy_support)
        urllib.request.install_opener(opener)

        # configure headers
        req = urllib.request.Request(uri)
        req.add_header('User-Agent', self.headers["ua"])
        req.add_header('Accept', self.headers["accept"])
        req.add_header('Accept-Language', self.headers["accept_language"])

        try:
            res = urllib.request.urlopen(req, timeout=self.wait['timeout'])
        except Exception as err:
            self.broken.put(p)
            raise Exception(fn + " error! using proxy " + p + " for " + uri + ". Trace: " + str(err))
        else:
            #print(fn + ": exitoso")
            self.ready.put(p)
            return res

    # process request, thread-safe
    def req(self, uri):
        fn = self.f + " req"
        try:
            # check if URL is valid, or will blow through the list
            if not self.validate(uri):
                raise Exception(fn + " error: invalid URI! (" + uri + ")")

            #print(fn+": getting " + uri + " ...")

            # run through queue
            while not self.ready.empty():
                # assign a new proxy
                p = self.ready.get()
                # wait before requesting
                time.sleep(random.randint(self.wait['min'], self.wait['max']))

                try:
                    # getter
                    res = self.get(p, uri)
                    #print('status is: ' + str(res.status))
                except Exception as err:
                    raise Exception(fn + " error: trace: " + str(err))
                else:
                    return {"success": True, "data": res}

            raise Exception(fn + " error: no hay proxies disponibles!")
        except Exception as err:
            return {"success": False, "error": err}

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

    # list broken proxies
    def broken(self):
        arr = list(self.broken)
        print(self.f + " has " + str(arr.length) + " broken proxies: " + str(arr))
        return arr

