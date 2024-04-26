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
    def __init__(self, threads: int, wait: dict, headers: dict, test: dict, locale: str):
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
        # i18n: locale is a str of format "en" or "es"
        self._i18
        # run setup
        __setup(locale)

    # initial setup
    def __setup(self, locale) -> None:
        fn = self.f + " setup: "
        # check test URI
        if not self.validate(self.test["uri"]):
            raise Exception(self._i18('error.test_uri'))
        # load locale
        self.__load_i18(locale ? locale : "en")
        # start
        print(fn + self.__t('setup.threads', str(self.threads)))
        return

    # proxy list load, thread-safe
    def load(self, path: str):
        fn = self.f + " load: "

        if not path:
            raise Exception(fn + self.__t('error.no_list'))
        print(fn + self.__t('load.loading', path))
        read = 0

        # load the list
        with open(path, "r") as f:
            arr = f.read().split("\n") # on line break
            if not arr:
                raise Exception(fn + self.__t('error.list_empty'))
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

        print(fn + self.__t('load.n_read', str(read)))
        n_per_thread = self.all.qsize()/self.threads
        print(fn + self.__t('load.per_thread', str(n_per_thread)))
        maxtime = (n_per_thread*(self.test['max']))
        if maxtime > 60:
            print(fn + self.__t('load.less_than', (str("{0:.2f}".format(maxtime/60)),"m")))
        else:
            print(fn + self.__t('load.less_than', (str("{0:.0f}".format(maxtime)),"s")))

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
        print(self.available().length)

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
        print(fn + self.__t('healthcheck.status', (str(valid), str(broken))))
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
            raise Exception(fn + self.__t('error.get', (p, uri, str(err))))
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
                raise Exception(fn + self.__t('error.bad_uri', uri))

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
                except HTTPError as err:
                    raise Exception(fn + self.__t('error.bad_response', str(err.reason)))
                else:
                    return {"success": True, "data": res}

            raise Exception(fn + self.__t('error.no_proxies_avail'))
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

    # list available proxies
    def available(self) -> list:
        ready = list(self.ready)
        print(self.f + ": " + self.__t('common.available', str(ready.length)))
        return ready

    # list broken proxies
    def broken(self) -> list:
        arr = list(self.broken)
        print(self.f + ": "+ self.__t('common.broken', (str(arr.length), str(arr))))
        return arr

    # private: i18n
    def __t(self, key: str, insert: str) -> str:
        if not insert:
            return self._i18[key]
        else:
            return self._i18[key].format(insert)

    # private: load i18
    def __load_i18(self, locale: str):
        filepath = "locales/{}.json".format(locale)
        with open(filepath, "r") as f:
            self._i18 = json.load(f)

