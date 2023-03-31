import os

APP_DIR = realPath = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = APP_DIR
CACHE_DIR = os.path.join(APP_DIR, "cache")

# THUMBNAIL_CACHE_DIR = os.path.join(APP_DIR, 'cache', 'thumbnails')

for d in [CACHE_DIR]:
    if not os.path.exists(d):
        try:
            os.makedirs(d)
        except Exception as e:
            print(f"Can't auto create dir {d}: {e}")
