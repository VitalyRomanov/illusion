from enum import Enum
from multiprocessing import Process
from multiprocessing import Queue
from typing import List

from analyzer import ImageAnalyzer
from crawler import Crawler
from image_store import ImageStore, Image
from protocol import Message, AbstractWorker, start_worker


class ProcessManager(AbstractWorker):
    to_image_store_queue = None
    image_store_proc = None

    to_image_crawler_queue = None
    image_crawler_proc = None

    to_image_analyzer_queue = None
    image_analyzer_proc = None

    class InboxTypes(Enum):
        GET_EXISTING_IMAGES = 1

    class OutboxTypes(Enum):
        EXISTING_IMAGES = 1
        ADDED_IMAGES = 2
        UPDATED_METADATA = 3

    def __init__(self, config, inbox_queue, outbox_queue):
        self.config = config
        self.inbox_queue = inbox_queue
        self.outbox_queue = outbox_queue

        self._create_image_store()
        self._create_image_crawler()
        self._create_image_analyzer()

        self.message_processing_table = {
            ImageStore.OutboxTypes.EXISTING_IMAGES: self._received_existing_images,
            ImageStore.OutboxTypes.ADDED_IMAGES: self._received_images_added_to_image_store,
            ImageStore.OutboxTypes.UPDATED_METADATA: self._send_updates_to_app,
            Crawler.OutboxTypes.DISCOVERED_IMAGES: self._received_discovered_images,
            ProcessManager.InboxTypes.GET_EXISTING_IMAGES: self._request_existing_images,
            ImageAnalyzer.OutboxTypes.UPDATE_METADATA: self._set_new_metadata,
            ImageAnalyzer.OutboxTypes.FACES_IDENTIFIED: self._set_new_metadata
        }

    def _create_image_store(self):
        self.to_image_store_queue = Queue()
        self.image_store_proc = Process(
            target=start_worker, args=(ImageStore, self.config, self.to_image_store_queue, self.inbox_queue)
        )
        self.image_store_proc.start()

    def _create_image_crawler(self):
        self.to_image_crawler_queue = Queue()
        self.image_crawler_proc = Process(
            target=start_worker, args=(Crawler, self.config, self.to_image_crawler_queue, self.inbox_queue)
        )
        self.image_crawler_proc.start()

    def _create_image_analyzer(self):
        self.to_image_analyzer_queue = Queue()
        self.image_analyzer_proc = Process(
            target=start_worker, args=(ImageAnalyzer, self.config, self.to_image_analyzer_queue, self.inbox_queue)
        )
        self.image_analyzer_proc.start()

    def _received_existing_images(self, message: Message):
        self.outbox_queue.put(
            Message(ProcessManager.OutboxTypes.EXISTING_IMAGES, content=message.content)
        )
        self.to_image_crawler_queue.put(
            Message(
                Crawler.InboxTypes.SET_EXISTING_IMAGES,
                content=[image.path for image in message.content]
            )
        )
        self._send_images_for_analysis(message.content)
        self._send_faces_for_analysis(message.content)

    def _received_images_added_to_image_store(self, message: Message):
        self.outbox_queue.put(
            Message(ProcessManager.OutboxTypes.ADDED_IMAGES, content=message.content)
        )
        self._send_images_for_analysis(message.content)

    def _received_discovered_images(self, message: Message):
        self.to_image_store_queue.put(
            Message(ImageStore.InboxTypes.ADD_NEW_IMAGES, content=message.content)
        )

    def _request_existing_images(self, message: Message):
        self.to_image_store_queue.put(
            Message(ImageStore.InboxTypes.GET_EXISTING_IMAGES, content=None)
        )

    def _set_new_metadata(self, message: Message):
        self.to_image_store_queue.put(
            Message(ImageStore.InboxTypes.UPDATE_METADATA, message.content)
        )

    def _send_images_for_analysis(self, images: List[Image]):
        not_analyzed = [
            image for image in images if image.faces_detected is False or image.tags_detected is False
        ]
        if len(not_analyzed) > 0:
            self.to_image_analyzer_queue.put(
                Message(ImageAnalyzer.InboxTypes.ANALYZE_NEW_IMAGES, content=not_analyzed)
            )

    def _send_faces_for_analysis(self, images: List[Image]):
        faces_for_analysis = []
        for image in images:
            for face in image.faces:
                # id is assigned after face was written to the database
                if face.recognized is False and face.id is not None:
                    faces_for_analysis.append(face)

        if len(faces_for_analysis) > 0:
            self.to_image_analyzer_queue.put(
                Message(ImageAnalyzer.InboxTypes.ANALYZE_FACES, content=faces_for_analysis)
            )

    def _send_updates_to_app(self, message: Message):
        self.outbox_queue.put(Message(
            ProcessManager.OutboxTypes.UPDATED_METADATA,
            message.content
        ))
        self._send_faces_for_analysis(message.content)

    def _handle_message(self, message):
        if message.descriptor in self.message_processing_table:
            self.message_processing_table[message.descriptor](message)
        else:
            raise Exception(f"Unknown message descriptor: {message.descriptor}")


# def start_process_manager(config, from_gui: Queue = None, to_gui: Queue = None):
#     """
#     Start main loop for the database and helper processes.
#     :param monitoring_folders: List of folders to pass on to the crawler for monitoring.
#     :param input_queue: queue for receiving messages from gui
#     :param output_queue: queue for sending messages back to gui
#     :return:
#     """
#
#     proc_manager = ProcessManager(config, from_gui, to_gui)
#
#     while True:
#         proc_manager.handle_incoming()
