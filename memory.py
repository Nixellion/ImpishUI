import os
import json
from paths import CACHE_DIR

class DataCache():
    def __init__(self, fp=os.path.join(CACHE_DIR, "cache.json")):
        self.fp = fp
        if not os.path.exists(self.fp):
            self.write({})

    def write(self, data):
        with open(self.fp, 'w+') as f:
            return f.write(json.dumps(data, indent=4, sort_keys=True))

    def read(self):
        with open(self.fp, 'r') as f:
            return json.loads(f.read())

    def get(self, key, default=None):
        return self.read().get(key, default)

    def set(self, key, value):
        data = self.read()
        data[key] = value
        self.write(data)

    def remove(self, key):
        data = self.read()
        if key in data:
            data.pop(key)
        self.write(data)

    def key_exists(self, key):
        data = self.read()
        return key in data

    pop = remove




data_cache = DataCache()