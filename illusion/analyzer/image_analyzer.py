from enum import Enum

from illusion.protocol import AbstractWorker, Message


class ImageAnalyzer(AbstractWorker):
    thumbnailer = None
    face_detector = None
    face_identifier = None
    image_categorizer = None

    class InboxTypes(Enum):
        ANALYZE_NEW_IMAGES = 1  # existing images arrived

    class OutboxTypes(Enum):
        UPDATE_METADATA = 1  # sending discovered images

    def __init__(self, config, inbox_queue, outbox_queue):
        self.config = config
        self.inbox_queue = inbox_queue
        self.outbox_queue = outbox_queue

    def full_analysis(self, images):
        pass

    def _handle_message(self, message):
        if message.descriptor == ImageAnalyzer.InboxTypes.ANALYZE_NEW_IMAGES:
            return Message(
                ImageAnalyzer.OutboxTypes.UPDATE_METADATA,
                content=self.full_analysis(message.content)
            )
