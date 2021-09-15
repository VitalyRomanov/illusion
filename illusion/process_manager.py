from multiprocessing import Process
from multiprocessing import Queue
from time import sleep

from illusion.app import App
from illusion.crawler.crawler import start_crawler
from illusion.image_store import start_image_store, ImageStore
from illusion.protocol import Message


class ProcessManager:
    def __init__(self, config, from_gui, to_gui):
        self.config = config
        self.create_image_store()
        self.create_image_crawler()
        self.from_gui = from_gui
        self.to_gui = to_gui

        self.request_existing_images()

    def request_existing_images(self):
        self.to_image_store.put(
            Message(ImageStore.InboxTypes.GET_EXISTING_IMAGES, content=None)
        )

    def create_image_store(self):
        self.to_image_store = Queue()
        self.from_image_store = Queue()
        self.image_store_proc = Process(target=start_image_store, args=(self.config, self.to_image_store, self.from_image_store))
        self.image_store_proc.start()

    def create_image_crawler(self):
        self.to_image_crawler = Queue()
        self.from_image_crawler = Queue()
        self.image_crawler_proc = Process(target=start_crawler, args=(self.to_image_crawler, self.from_image_crawler, self.config["monitoring_folders"]))
        self.image_crawler_proc.start()

    def fetch_from_crawler(self):
        new_images = []
        while not self.from_image_crawler.empty():
            new_images.append(self.from_image_crawler.get())

        if len(new_images) > 0:
            self.to_image_store.put(
                Message(ImageStore.InboxTypes.ADD_NEW_IMAGES, content=new_images)
            )

    def fetch_from_image_store(self):
        while not self.from_image_store.empty():
            message = self.from_image_store.get()
            if message.descriptor == ImageStore.OutboxTypes.EXISTING_IMAGES:
                self.to_gui.put(
                    Message(App.InboxTypes.EXISTING_IMAGES, content=message.content)
                )
            elif message.descriptor == ImageStore.OutboxTypes.ADDED_IMAGES:
                self.to_gui.put(
                    Message(App.InboxTypes.ADDED_IMAGES, content=message.content)
                )

    def fetch_from_gui(self):
        while not self.from_gui.empty():
            message = self.from_image_store.get()

    def handle_incoming(self):
        """
        Wait for messages from gui. This is intended to be the longest part of the main loop
        :return:
        """
        self.fetch_from_gui()
        self.fetch_from_crawler()
        self.fetch_from_image_store()
        sleep(3)


def start_process_manager(config, from_gui: Queue = None, to_gui: Queue = None):
    """
    Start main loop for the database and helper processes.
    :param monitoring_folders: List of folders to pass on to the crawler for monitoring.
    :param input_queue: queue for receiving messages from gui
    :param output_queue: queue for sending messages back to gui
    :return:
    """

    proc_manager = ProcessManager(config, from_gui, to_gui)

    while True:
        proc_manager.handle_incoming()