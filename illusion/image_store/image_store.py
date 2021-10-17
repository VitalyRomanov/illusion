import hashlib
from enum import Enum
from pathlib import Path
from typing import List, Union

import cv2

from illusion.image_store.datamodel import get_database
from illusion.protocol import Message, AbstractWorker


class DatamodelObject:
    def __repr__(self):
        content_string = ', '.join(f"{key}: {value}" for key, value in self.__dict__.items())
        return f"{self.__class__.__name__}({content_string})"


class Image(DatamodelObject):
    def __init__(self, id=None, path=None, md5=None, faces_detected=None, tags_detected=None, tags=None, faces=None):
        self.id = id
        self.path = path
        self.md5 = md5
        self.faces_detected = faces_detected
        self.faces = faces
        self.tags = tags
        self.tags_detected = tags_detected
        self.was_updated = False

        if self.path is not None and isinstance(self.path, str):
            self.path = Path(self.path)

    def add_faces(self, new_faces):
        if self.faces is None:
            self.faces = []
        self.faces.extend(new_faces)
        self.was_updated = True

    def set_faces_detected_flag(self):
        self.faces_detected = True
        self.was_updated = True

    def add_tags(self, tags):
        self.tags.update(tags)
        self.was_updated = True

    def set_tags_detected_flag(self):
        self.tags_detected = True

    def read_image_content(self):
        """
        Read image from the disk
        :return:
        """
        if isinstance(self.path, Path):
            self.path = str(self.path.resolve())
        return cv2.imread(self.path)

    # def __repr__(self):
    #     return f"Image({self.__dict__})"

    @classmethod
    def from_datamodel(cls, image):
        return cls(
            id=image.id, path=image.path, md5=image.md5, faces_detected=image.faces_detected,
            tags_detected=image.tags_detected,
            tags={t.tag.name for t in image.tags}, faces=[Face.from_datamodel(face) for face in image.faces]
        )


class Face(DatamodelObject):
    def __init__(
            self, id, x, y, w, h, deleted, person, thumbnail_path=None, thumbnail=None, image_id=None, recognized=False
    ):
        self.id = id
        self.image_id = image_id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self._thumbnail = cv2.resize(thumbnail, (64, 64)) if thumbnail is not None else None
        self.thumbnail_path = thumbnail_path
        self.deleted = deleted
        self.person = person
        self.recognized = recognized

        if self.thumbnail_path is not None and isinstance(self.thumbnail_path, str):
            self.thumbnail_path = Path(self.thumbnail_path)

    def set_person(self, person_id):
        self.person = person_id

    def set_person_identified_flag(self):
        self.recognized = True

    # def __repr__(self):
    #     return f"Face({self.__dict__})"

    def get_thumbnail(self):
        if self._thumbnail is None:
            self._thumbnail = cv2.imread(str(self.thumbnail_path.resolve()))
        return self._thumbnail

    def save_thumbnail(self, save_dir: Path):
        thumbnail_name = f"{hashlib.md5(self._thumbnail.tobytes()).hexdigest()}.jpeg"
        self.thumbnail_path = save_dir.joinpath(thumbnail_name)
        # self.thumbnail_path = join(save_dir, thumbnail_name)
        cv2.imwrite(str(self.thumbnail_path.resolve()), self._thumbnail)

    @classmethod
    def from_datamodel(cls, face):
        faceperson = [p for p in face.person]
        if len(faceperson) == 0:
            person = None
        elif len(faceperson) == 1:
            person = faceperson[0].person
        else:
            raise Exception()
        return cls(
            id=face.id, x=face.x, y=face.y, w=face.w, h=face.h, deleted=face.deleted,
            thumbnail_path=face.thumbnail_path, person=Person.from_datamodel(person), image_id=face.image.id,
            recognized=face.recognized
        )


class Person(DatamodelObject):
    def __init__(self, id, name, image_ids=None):
        self.id = id
        self.name = name
        self.image_ids = image_ids

    # def __repr__(self):
    #     return f"Person({self.__dict__})"
    def set_image_ids(self, image_ids):
        self.image_ids = image_ids

    @classmethod
    def from_datamodel(cls, person):
        if person is None:
            return None
        image_ids = [f.face.image.id for f in person.faces]
        return Person(id=person.id, name=person.name, image_ids=image_ids)


class ImageStore(AbstractWorker):

    class InboxTypes(Enum):
        GET_EXISTING_IMAGES = 1  # request to send all existing images arrived
        ADD_NEW_IMAGES = 2  # new images have arrived
        UPDATE_METADATA = 3

    class OutboxTypes(Enum):
        EXISTING_IMAGES = 1  # sending existing images
        ADDED_IMAGES = 2  # sending images that have been added
        UPDATED_METADATA = 3

    def __init__(self, config, inbox_queue, outbox_queue):
        self.config = config
        self.inbox_queue = inbox_queue
        self.outbox_queue = outbox_queue
        self.ImageTable, self.TagTable, self.PersonTable, \
            self.FaceTable, self.ImageTagTable, self.FacePersonTable = \
            get_database(config.db_loc)

    def _add_images(self, paths):
        added = []
        for image_path in paths:
            new_id = self._add_image(image_path)
            if new_id is not None:
                added.append(new_id)

        return added

    def _add_image(self, path: Path):
        if path.is_file():
            md5 = hashlib.md5(open(path, 'rb').read()).hexdigest()
        else:
            return None
            # raise FileNotFoundError(f"File nod found: {path}")

        image = self.ImageTable.get_image_if_exists(path=path)
        if image is not None:
            image.md5 = md5
            image.save()
            # TODO
            # This could be an issue when an image with the same name was added
            # but the image itself has changed. GUI will not be notified
            return None
        else:
            image = self.ImageTable.create_image(path=path, md5=md5)
            return Image.from_datamodel(image)

    def _update_image_metadata(self, image: Image):
        if image.was_updated:
            pw_image = self.ImageTable.get_image_if_exists(image.id)
            if pw_image.tags_detected is False and image.tags_detected is True:
                # {t.tag.name for t in self._image.tags}
                for tag in image.tags:  # TODO check for duplicates
                    pw_tag = self.TagTable.get_or_create(tag)
                    self.ImageTagTable.create(image=pw_image, tag=pw_tag)
                    pw_tag.save()
                pw_image.tags_detected = True

            if pw_image.faces_detected is False and image.faces_detected is True:
                for face in image.faces:
                    if face.id is not None:
                        continue
                    face.save_thumbnail(save_dir=self.config.face_thumbnails_loc)
                    pw_face = self.FaceTable.create_face(
                        image=pw_image, thumbnail_path=face.thumbnail_path,
                        x=face.x, y=face.y, w=face.w, h=face.h
                    )
                    face.id = pw_face.id
                    pw_face.save()
                pw_image.faces_detected = True
            pw_image.save()
            return image
        return None

    def _update_face_metadata(self, face: Face):
        pw_face = self.FaceTable.get(id=face.id)
        if pw_face.recognized is False and face.recognized is True:
            pw_person = self.PersonTable.get_or_create(id=face.person.id)
            self.FacePersonTable.create(face=face.id, person=pw_person.id)
            pw_face.recognized = True
            pw_face.save()
            face.person = Person.from_datamodel(pw_person)
            return face
        return None

    def _update_metadata(self, updated_objects: List[Union[Image, Face]]):
        updated = []

        for updated_object in updated_objects:
            if isinstance(updated_object, Image):
                updated_ = self._update_image_metadata(updated_object)
            elif isinstance(updated_object, Face):
                updated_ = self._update_face_metadata(updated_object)
            else:
                raise ValueError("Unrecognized object type:", type(updated_object))
            if updated_ is not None:
                updated.append(updated_object)

        return updated

    def _handle_message(self, message):
        if message.descriptor == ImageStore.InboxTypes.GET_EXISTING_IMAGES:
            images = [Image.from_datamodel(image) for image in self.ImageTable.get_all_images()]
            return Message(
                ImageStore.OutboxTypes.EXISTING_IMAGES,
                content=images
            )
        elif message.descriptor == ImageStore.InboxTypes.ADD_NEW_IMAGES:
            return Message(
                ImageStore.OutboxTypes.ADDED_IMAGES,
                content=self._add_images(message.content)
            )
        elif message.descriptor == ImageStore.InboxTypes.UPDATE_METADATA:
            return Message(
                ImageStore.OutboxTypes.UPDATED_METADATA,
                self._update_metadata(message.content)
            )
        return None


# def start_image_store(config, inbox_queue, outbox_queue):
#     image_store = ImageStore(config)
#
#     while True:
#         message = inbox_queue.get()
#         outbox_queue.put(
#             image_store.handle_message(message)
#         )


# class _Tag:
#     @staticmethod
#     def get_or_create(name):
#         try:
#             tag = dm.Tag.get(name=name)
#         except:  # TagDoesNotExist:
#             tag = dm.Tag.create(name=name)
#         return tag
#
#     @staticmethod
#     def get(id=None, name=None):
#         if id is not None:
#             tag = dm.Tag.get(id=id)
#         elif name is not None:
#             tag = dm.Tag.get(name=name)
#         else:
#             raise ValueError("Either `id` or `name` should be provided")
#
#         return tag


# class _TagSet(set):
#     def __init__(self, image):
#         self._image = image
#         self.update_local_tags()
#
#     def update_local_tags(self):
#         self.local_tags = {t.tag.name for t in self._image.tags}
#
#     def iter(self):
#         return self._image.tags
#
#     def add(self, tag_name):
#         if tag_name not in self.local_tags:
#             tag = _Tag.get_or_create(tag_name)
#             # ImageTag.create(image=image, tag=t)
#             dm.ImageTag.create(image=self._image, tag=tag)
#             self.update_local_tags()
#
#     def __repr__(self):
#         return repr(self.local_tags)
#
#     def update(self, tags):
#         tags = [tag for tag in tags if tag not in self.local_tags]
#         for tag in tags:
#             self.add(tag)
#         self.update_local_tags()
#
#     def pop(self, tag_name):
#         if tag_name in self.local_tags:
#             tag = _Tag.get(name=tag_name)
#             rows_removed = dm.ImageTag.delete().where(dm.ImageTag.image_id == self._image.id and dm.ImageTag.tag_id == tag.id).execute()
#             self.update_local_tags()


# class _FaceSet(set):
#     def __init__(self, image):
#         self._image = image
#
#     def iter(self):
#         return self._image.faces
#
#     def __repr__(self):
#         return {t.name for t in self._image.faces}
#
#     def pop(self, face_id):
#         dm.Face.delete().where(_Face.id == face_id).execute()


# class _Image:
#
#     # face_extractor = FaceExtractor("/Volumes/External/dev/illusion/haarcascade_frontalface_default.xml")
#     histogram_index = None
#
#     def __init__(self, path=None, from_id=None):
#         if path is not None:
#             if os.path.isfile(path):
#                 md5 = hashlib.md5(open(path, 'rb').read()).hexdigest()
#             else:
#                 raise FileNotFoundError(f"File nod found: {path}")
#
#             self._image = self.get_image(path=path)
#             if self._image is not None:
#                 self._image.md5 = md5
#                 self._image.save()
#             else:
#                 self._image = self.create_image(path, md5)
#
#         elif from_id is not None:
#             self._image = self.get_image(id=from_id)
#
#         self._tags = _TagSet(self._image)
#         self._faces = _FaceSet(self._image)
#
#     def get_image(self, id=None, path=None):
#         try:
#             if id is not None:
#                 return dm.Image.get(id=id)
#             if path is not None:
#                 return dm.Image.get(path=path)
#         except:
#             return None
#
#     def create_image(self, path, md5):
#         return dm.Image.create(path=path, md5=md5)
#
#     @property
#     def id(self):
#         return self._image.id
#
#     @property
#     def path(self):
#         return self._image.path
#
#     @property
#     def md5(self):
#         return self._image.md5
#
#     @property
#     def faces_detected(self):
#         return self._image.faces_detected
#
#     def tags(self):
#         return self._tags
#
#     def faces(self):
#         return self._image.faces
#
#     def detect_faces(self):
#         faces = self.face_extractor(cv2.imread(self._image.path))
#
#         for_analysis = []
#         for x, y, w, h, thumbnail in faces:
#             face = _Face(image=self._image, x=x, y=y, w=w, h=h)
#             face.set_thumbnail_path(
#                 os.path.join(
#                     os.environ["ILLUSION_CONF"],
#                     os.path.join("face_thumbnails", f"thumbnail_{face.id}.jpg")
#                 )
#             )
#             cv2.imwrite(face.thumbnail_path, thumbnail)
#             for_analysis.append(face.thumbnail_path)
#
#         self._image.faces_detected = True
#         self._image.save()
#         # TODO
#         #  run analysis
#         #  decide on person name assignment after clustering
#
#     def add_tags(self, tags):
#         for tag in tags:
#             self._tags.add(tag)
#
#     def remove_tags(self, tags):
#         for tag in tags:
#             self._tags.pop(tag)
#
#     def wrap(self, image):
#         self._image = image


# class _Person:
#     def __init__(self, name):
#         self._person = dm.Person.create(name=name)
#
#     @property
#     def id(self):
#         return self._person.id
#
#     @property
#     def name(self):
#         return self._person.name


# class _Face:
#
#     encoding_model = None
#     face_index = None
#
#     def __init__(self, image, x, y, w, h):
#         self._face = dm.Face.create(image=image, x=x, y=y, w=w, h=h, deleted=False)
#
#     @property
#     def id(self):
#         return self._face.id
#
#     @property
#     def image(self):
#         return self._face.image
#
#     @property
#     def thumbnail_path(self):
#         return self._face.thumbnail_path
#
#     def set_thumbnail_path(self, path):
#         self._face.thumbnail_path = path
#         self._face.save()
#
#     # def __del__(self):
#     #     self._face.deleted = True  # this will set deleted flag on destructor
#     #     self._face.save()
#
#     # def encode(self, thumbnail=None):
#     #     if thumbnail is None:
#     #         thumbnail = cv2.imread(self._face.thumbnail_path)
#     #     encoding = self.encoding_model(thumbnail)
#     #     return encoding
#     #
#     # def add_to_face_index(self, encoding=None):
#     #     if encoding is None:
#     #         encoding = self.encode()
#     #     self.face_index.register(encoding)
#
#     def recognize(self, thumbnail=None):
#         if thumbnail is None:
#             thumbnail = cv2.imread(self._face.thumbnail_path)
#         encoding = self.encoding_model(thumbnail)
#         self.face_index.register(self._face.id, encoding)
#         self.face_index.find_similar(encoding)


# def main_test():
#     image = Image("/Volumes/External/dev/illusion/test_photo.jpg")
#     image.add_tags(["!!", "##"])
#     image.add_tags(["??"])
#     image.remove_tags(["??"])
#     if image.faces_detected is False:
#         image.detect_faces()
#     print()


# def main_loop_test():
#     image_store_main_loop()


# if __name__ == "__main__":
#     main_loop_test()
