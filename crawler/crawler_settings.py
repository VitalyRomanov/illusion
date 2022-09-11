import configparser
from pathlib import PosixPath


class CrawlerSettings:
    TRACKED_DIRS = None
    IGNORED_DIRS = None
    EXTENSIONS = None

    @classmethod
    def load(cls):
        config = configparser.ConfigParser()
        config.read('../config.ini')

        search_dirs_str = config['DIRECTORIES']['search_dirs'].strip()
        cls.TRACKED_DIRS = set(map(str.strip, search_dirs_str.split(','))) if search_dirs_str != '' else {}

        ignore_dirs_str = config['DIRECTORIES']['ignore_dirs'].strip()
        cls.IGNORED_DIRS = set(
            map(lambda p: PosixPath(p.strip()), ignore_dirs_str.split(','))) if ignore_dirs_str != '' else {}

        extensions_str = config['EXTENSIONS']['image_extensions'].strip()
        cls.EXTENSIONS = {f'.{ext}' for ext in extensions_str.split(',')} if extensions_str != '' else {'.png',
                                                                                                        '.jpeg',
                                                                                                        '.jpg'}
