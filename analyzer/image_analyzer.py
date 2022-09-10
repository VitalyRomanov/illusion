from enum import Enum
from typing import List

from analyzer.face_detector import FaceDetector
from analyzer.face_identifier import FaceIdentifier
from analyzer.image_tagger import ImageTagger
from image_store import Image, Face
from old_illusion.protocol import AbstractWorker, Message


class ImageAnalyzer(AbstractWorker):
    thumbnailer = None
    face_extractor = None
    face_identifier = None
    image_tagger = None

    class InboxTypes(Enum):
        ANALYZE_NEW_IMAGES = 1  # existing images arrived
        ANALYZE_FACES = 2

    class OutboxTypes(Enum):
        UPDATE_METADATA = 1  # sending discovered images
        FACES_IDENTIFIED = 2

    def __init__(self, config, inbox_queue, outbox_queue):
        self.config = config
        self.inbox_queue = inbox_queue
        self.outbox_queue = outbox_queue
        self.face_extractor = FaceDetector(self.config.face_extractor_model)
        self.image_tagger = ImageTagger()
        self.face_identifier = FaceIdentifier()

    def image_analysis(self, images: List[Image]):
        for image in images:
            image_array = image.read_image_content()
            if image.faces_detected is False:
                self.detect_faces(image, image_array)
            if image.tags_detected is False:
                self.detect_tags(image, image_array)
        return images

    def detect_faces(self, image, image_array):
        faces = self.face_extractor.get_faces(image_array)
        image.add_faces(faces)
        image.set_faces_detected_flag()

    def detect_tags(self, image, image_array):
        image.add_tags(self.image_tagger.detect_tags(image_array))
        image.set_tags_detected_flag()

    def face_analysis(self, faces: List[Face]):
        for face in faces:
            identity = self.face_identifier.add_to_index_and_identify(face.get_thumbnail())
            face.set_person(identity)
            face.set_person_identified_flag()
        return faces

    def _handle_message(self, message):
        if message.descriptor == ImageAnalyzer.InboxTypes.ANALYZE_NEW_IMAGES:
            images = message.content
            for image in images:
                # send one by one because processing is slow
                self.outbox_queue.put(
                    Message(
                        ImageAnalyzer.OutboxTypes.UPDATE_METADATA,
                        content=self.image_analysis([image])
                    )
                )
        elif message.descriptor == ImageAnalyzer.InboxTypes.ANALYZE_FACES:
            faces = message.content
            for face in faces:
                # send one by one because processing is slow
                self.outbox_queue.put(
                    Message(
                        ImageAnalyzer.OutboxTypes.FACES_IDENTIFIED,
                        content=self.face_analysis([face])
                    )
                )
