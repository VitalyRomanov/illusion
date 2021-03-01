from pathlib import Path


class Crawler:
    """
    Crawler which searches FS for the files of specified extensions,
    keeps track of them in __scanned_files__ (existing file records are updated if last update timestamp has changed),
    shares newly found images via __new_images_queue__ queue
    """
    __new_images_queue__ = None
    __scanned_files__ = {}
    __extensions__ = ['.jpg', '.jpeg', '.png']

    def __init__(self, new_images_queue):
        self.__new_images_queue__ = new_images_queue

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
            if file.suffix in self.__extensions__:
                file_last_edited = file.stat().st_mtime
                if (file.name not in self.__scanned_files__.keys()) or (
                        self.__scanned_files__[file.name] != file_last_edited):
                    self.__new_images_queue__.put(file.name)
                    self.__scanned_files__[file.name] = file_last_edited  # last content edit (consider inode)
                    # print(file)

        # print(self.__new_images_queue__.qsize())

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
                self.__scanned_files__.pop(file_name)
