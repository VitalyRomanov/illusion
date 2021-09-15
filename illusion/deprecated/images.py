from pathlib import Path


class ImageCrawler:
    _extensions = ['.jpg', '.jpeg', '.png']

    @staticmethod
    def find_in_dir(dir_name, recursive=True):
        """
        Find all files with extensions listed in _extensions tuple
        :param dir_name: folder to search in (string)
        :param recursive: search recursively on the folder (boolean)
        :return: tuple of Path object representing images found
        """
        result = []
        dir_path = Path(dir_name)
        path_pattern = '**' if recursive else '*' + '/*'
        result = [file for file in dir_path.glob(path_pattern) if file.suffix in ImageCrawler._extensions]
        return result


images = ImageCrawler.find_all_in_dir("C:/", True)
print(images)
