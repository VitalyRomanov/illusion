import asyncio
import datetime
from pathlib import Path

from colorama import Fore

from crawler_settings import CrawlerSettings

tracked_images = {}  # path, detection_time, mod_time


def retrieve_images(search_dirs, ignore_dirs, extensions):
    images = {}

    for search_dir in search_dirs:
        for f in Path(search_dir).rglob('*'):
            if not set(f.parents).isdisjoint(ignore_dirs):
                continue
            if f.suffix in extensions:
                try:
                    images[f] = f.stat().st_mtime_ns
                except FileNotFoundError:
                    print(Fore.CYAN, f'File {f} does not exist')
    return images


async def get_fs_changes(added_images, removed_images, changed_images, interval=5):
    print(CrawlerSettings.EXTENSIONS,
          CrawlerSettings.TRACKED_DIRS,
          CrawlerSettings.IGNORED_DIRS)
    while True:
        crawling_start_time = datetime.datetime.now()
        for image_path, mod_time in retrieve_images(CrawlerSettings.TRACKED_DIRS,
                                                    CrawlerSettings.IGNORED_DIRS,
                                                    CrawlerSettings.EXTENSIONS).items():
            if image_path not in tracked_images:
                await added_images.put(item=image_path)
            elif tracked_images[image_path]['mod_time'] != mod_time:
                await changed_images.put(item=image_path)

            tracked_images[image_path] = {'detection_time': crawling_start_time,
                                          'mod_time': mod_time}

        tracked_image_paths = tuple(tracked_images.keys())
        for tracked_image in tracked_image_paths:
            if tracked_images[tracked_image]['detection_time'] != crawling_start_time:
                await removed_images.put(item=tracked_image)
                tracked_images.pop(tracked_image)

        print(Fore.RED, 'SLEEP')
        await asyncio.sleep(interval)
