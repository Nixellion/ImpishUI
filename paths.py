import os

APP_DIR = realPath = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(APP_DIR, "config")
CACHE_DIR = os.path.join(APP_DIR, "cache")
DATA_DIR = os.path.join(APP_DIR, "data",)
DATABASE_PATH = os.path.join(DATA_DIR, "database.db")

for d in [CACHE_DIR, DATA_DIR, CONFIG_DIR]:
    if not os.path.exists(d):
        try:
            os.makedirs(d)
        except Exception as e:
            print(f"Can't auto create dir {d}: {e}")
