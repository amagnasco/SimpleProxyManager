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
# localization
import os
import json

class ProxyManager:
    def __init__(self, conf):
        self.f = "ProxyManager"
        # conf
        self.wait = conf["wait"]
        self.headers = conf["headers"]
        self.test = conf["test"]
        # multithreading
        self.n_threads = conf["threads"]
        self.threads = queue.Queue(maxsize=conf["threads"]) # to establish a maximum later
        # proxies
        self.all = queue.Queue()
        self.ready = queue.Queue()
        self.broken = queue.Queue()
        # i18n: locale is a str of format "en" or "es"
        self._i18: dict
        # run setup
        self._setup(conf["locale"])

    # initial setup
    def _setup(self, locale) -> None:
        fn = self.f + " setup: "
        # load locale
        if not locale:
            self._load_i18("en")
        else:
            self._load_i18(locale)
        # check test URI
        if not self.validate(self.test["uri"]):
            raise Exception(self._t('error.test_uri'))
        # assign threads
        for t in range(self.n_threads):
            self.threads.put(t)
        print(fn + self._t('setup.threads', str(self.threads.qsize())))
        # start
        return

    # proxy list load, thread-safe
    def load(self, path: str):
        fn = self.f + " load: "
        try:
            # handle lack of input
            if not path:
                raise Exception(self._t('error.no_list'))

            print(fn + self._t('load.loading', path))
            read = 0

            # load the list
            try:
                f = open(path, "r")
            except FileNotFoundError as err:
                raise Exception(self._t('error.no_file'))
            else:
                arr = f.read().split("\n") # on line break
                if not arr:
                    raise Exception(self._t('error.list_empty'))
                for p in arr:
                    if not p:
                        continue
                    elif not p[0]: # skip empty
                        continue
                    elif p[0] == "#": # skip comments
                        # print(fn + "comment: " + p)
                        continue
                    else:
                        read += 1
                        self.all.put(p)

            print(fn + self._t('load.n_read', str(read)))
            n_per_thread = self.all.qsize()/self.n_threads
            print(fn + self._t('load.per_thread', str("{0:.0f}".format(n_per_thread))))
            maxtime = (n_per_thread*(self.test['max']))
            if maxtime > 60:
                print(fn + self._t('load.less_than', (str("{0:.2f}".format(maxtime/60)),"m")))
            else:
                print(fn + self._t('load.less_than', (str("{0:.0f}".format(maxtime)),"s")))

            # collect the threads to use
            threads = []
            # run health check multi-thread
            for _ in range(self.n_threads):
                thread = threading.Thread(target=self.healthcheck)
                thread.start()
                threads.append(thread)
            # wait for threads to complete
            for thread in threads:
                thread.join()

            # print available proxies and exit
            print(self.f + ": " + self._t('common.available', str(self.available())))
            return
        except Exception as err:
            print(fn + str(err))

    # go through "all" queue and test, thread-safe
    def healthcheck(self) -> None:
        fn = self.f + " healthcheck: "
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
        print(fn + self._t('healthcheck.status', (str(valid), str(broken))))
        return

    # getter
    def get(self, p, uri: str):
        fn = self.f + " get: "
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
            raise Exception(fn + self._t('error.get', (p, uri, str(err))))
        else:
            #print(fn + ": exitoso")
            self.ready.put(p)
            return res

    # process request, thread-safe
    def req(self, uri: str):
        fn = self.f + " req"
        try:
            # check if URL is valid, or will blow through the list
            if not self.validate(uri):
                raise Exception(fn + self._t('error.bad_uri', uri))

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
                    raise Exception(fn + self._t('error.bad_response', str(err.reason)))
                else:
                    return {"success": True, "data": res}

            raise Exception(fn + self._t('error.no_proxies_avail'))
        except Exception as err:
            return {"success": False, "error": err}

    # validate URIs
    def validate(self, uri: str):
        #print("validating "+uri+"...")
        try:
            result = urlparse(uri)
            return all([result.scheme, result.netloc])
        except AttributeError:
            return False

    # count available proxies
    def available(self) -> int:
        ready = self.ready.qsize()
        #print(self.f + ": " + self._t('common.available', str(ready)))
        return ready

    # count broken proxies
    def broken(self) -> int:
        arr = self.broken.qsize()
        print(self.f + ": "+ self._t('common.broken', str(arr)))
        return arr

    # private: i18n (nested 1 level)
    def _t(self, keys: str, *args) -> str:
        return self._i18.get(keys.split(".")[0],"i18n error!").get(keys.split(".")[1]).format(list(args))

    # private: load i18
    def _load_i18(self, locale: str) -> None:
        basepath = os.path.dirname(os.path.abspath(__file__))
        locspath = os.path.join(basepath, "locales/")
        filepath = os.path.join(locspath, "{}.json".format(locale))
        with open(filepath, "r") as f:
            self._i18 = json.load(f)
        return