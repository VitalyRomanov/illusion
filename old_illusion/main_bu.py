import asyncio
import datetime
from asyncio import AbstractEventLoop
from pathlib import Path, PosixPath

from colorama import Fore

tracked_images = {}  # path, detection_time, mod_time
added_images = asyncio.Queue()
removed_images = asyncio.Queue()
changed_images = asyncio.Queue()


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


async def crawl_file_system(interval=5, times=5):
    while True:
        print('added emtpy:', added_images.empty())

        crawling_start_time = datetime.datetime.now()
        for image_path, mod_time in retrieve_images(SEARCH_DIRS, IGNORE_DIRS, EXTENSIONS).items():
            if image_path not in tracked_images:
                await added_images.put(item=image_path)
            elif tracked_images[image_path]['mod_time'] != mod_time:
                await changed_images.put(item=image_path)

            tracked_images[image_path] = {'detection_time': crawling_start_time,
                                          'mod_time': mod_time}

        tracked_image_paths = tuple(tracked_images.keys())
        print(Fore.RED, tracked_image_paths)
        for tracked_image in tracked_image_paths:
            if tracked_images[tracked_image]['detection_time'] != crawling_start_time:
                await removed_images.put(item=tracked_image)
                tracked_images.pop(tracked_image)

        print(Fore.RED, 'SLEEP')
        await asyncio.sleep(interval)


async def print_queues(times=5):
    while True:
        if not added_images.empty():
            print(Fore.GREEN, 'added_images')
        while not added_images.empty():
            print(await added_images.get())

        if not removed_images.empty():
            print(Fore.GREEN, 'removed_images')
        while not removed_images.empty():
            print(await removed_images.get())

        if not changed_images.empty():
            print(Fore.GREEN, 'changed_images')
        while not changed_images.empty():
            print(await changed_images.get())

        await asyncio.sleep(5)


async def get_running_tasks():
    tasks = await asyncio.gather(
        crawl_file_system(),
        print_queues()
    )
    return tasks


def main():
    # loop: AbstractEventLoop = asyncio.new_event_loop()
    # loop.run_until_complete(get_running_tasks)
    # asyncio.set_event_loop(loop)
    asyncio.run(get_running_tasks())


if __name__ == '__main__':
    import configparser

    config = configparser.ConfigParser()
    config.read('config.ini')

    search_dirs_str = config['DIRECTORIES']['search_dirs'].strip()
    SEARCH_DIRS = set(map(str.strip, search_dirs_str.split(','))) if search_dirs_str != '' else {}
    ignore_dirs_str = config['DIRECTORIES']['ignore_dirs'].strip()
    IGNORE_DIRS = set(map(lambda p: PosixPath(p.strip()), ignore_dirs_str.split(','))) if ignore_dirs_str != '' else {}
    extensions_str = config['EXTENSIONS']['image_extensions'].strip()
    EXTENSIONS = {f'.{ext}' for ext in extensions_str.split(',')} if extensions_str != '' else {'.png', '.jpeg', '.jpg'}

    main()
