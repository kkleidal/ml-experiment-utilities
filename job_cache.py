import concurrent
import concurrent.futures
import multiprocessing
import urllib
import os
import pickle

def _runner(name, cache_loc, fn, args, kwargs):
    results = fn(*args, **kwargs)
    with open(cache_loc, "wb") as f:
        pickle.dump(results, f)
    return name, results

def _load_pickle(name, fn):
    with open(fn, "rb") as f:
        return name, pickle.load(f)

class JobCache():
    def __init__(self, njobs=None, cache_prefix="job_cache", use_processes=False):
        if njobs is None:
            njobs = multiprocessing.cpu_count()
        os.makedirs(cache_prefix, exist_ok=True)
        self.cache_prefix = cache_prefix
        self.njobs = njobs
        self.use_processes = use_processes

    def start(self):
        if self.use_processes:
            self.executer = concurrent.futures.ProcessPoolExecutor(max_workers=self.njobs)
        else:
            self.executer = concurrent.futures.ThreadPoolExecutor(max_workers=self.njobs)

    def stop(self):
        self.executer.shutdown(wait=True)

    def __enter__(self):
        self.start()

    def __exit__(self, type, value, traceback):
        self.stop()

    def submit(self, name, fn, args=None, kwargs=None):
        safe_name = urllib.parse.quote(name, '')
        cache_loc = os.path.join(self.cache_prefix, safe_name + ".pickle")
        if os.path.exists(cache_loc):
            future = self.executer.submit(_load_pickle, name, cache_loc)
        else:
            if args is None:
                args = []
            if kwargs is None:
                kwargs = {}
            future = self.executer.submit(_runner, name, cache_loc, fn, args, kwargs)
        return future
