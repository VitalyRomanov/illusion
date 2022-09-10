from multiprocessing import Process
from multiprocessing import Queue
from pathlib import Path

from crawler.crawler import Crawler

if __name__ == "__main__":
    new_images = Queue()
    crawler = Crawler(new_images_queue=new_images)
    app_config = {'folders': {Path.home().joinpath(".illusion")}}  # put your directories instead for testing
    # TODO: read folders from app config
    crawler_process = Process(target=crawler.find_in_dirs, args=(app_config.get('folders'),))
    crawler_process.start()
    crawler_process.join()
    print(new_images.qsize())
