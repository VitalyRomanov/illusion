from collections import Set
from enum import Enum
from pathlib import Path
from queue import Empty
from time import sleep


class Crawler:
    """
    Crawler which searches FS for the files of specified extensions,
    keeps track of them in __scanned_files__ (existing file records are updated if last update timestamp has changed),
    shares newly found images via __new_images_queue__ queue
    """

    class InboxTypes(Enum):
        EXISTING = 1  # existing images arrived

    class OutboxTypes(Enum):
        NEW_IMAGES = 1  # sending discovered images

    __new_images_queue__ = None
    __scanned_files__ = set()
    __extensions__ = ['.jpg', '.jpeg', '.png']

    def __init__(self, new_images_queue, discovered_files=()):
        self.__new_images_queue__ = new_images_queue
        self.__scanned_files__.update(discovered_files)

    def __find_in_dir__(self, dir, recursive=True):
        """
        Finds untracked or changed files having extension listed in __extensions__ tuple in the given directory;
        Puts them into __new_images_queue__
        :param dir: folder to search in (string)
        :param recursive: search recursively on the folder (boolean)
        """
        dir_path = Path(dir)
        path_pattern = ('**' if recursive else '*') + "/*"
        for file in dir_path.glob(path_pattern):
            if file.suffix.lower() in self.__extensions__:
                if file not in self.__scanned_files__:
                    self.__new_images_queue__.put(file.absolute())
                    self.__scanned_files__.add(file.absolute())
                    # print(file)


    def find_in_dirs(self, dirs, recursive=True):
        """
        Finds untracked or changed files having extension listed in __extensions__ tuple in the given directories;
        Puts them into __new_images_queue__
        :param dir_name: folder to search in (string)
        :param recursive: search recursively on the folder (boolean)
        """
        for dir in dirs:
            self.__find_in_dir__(dir=dir, recursive=recursive)

    def _untrack_removed_files(self):
        """
        Removes deleted files from internal __scanned_files__
        """
        for file_name in self.__scanned_files__:
            file = Path(file_name)
            if not file.is_file() or not file.exists():
                self.__scanned_files__.remove(file_name)


def start_crawler(inbox_queue, output_queue, monitoring_folders, scan_every=10):
    crawler = Crawler(new_images_queue=output_queue)

    while True:
        try:
            message = inbox_queue.get(timeout=scan_every)
        except Empty:
            pass
        crawler.find_in_dirs(monitoring_folders)