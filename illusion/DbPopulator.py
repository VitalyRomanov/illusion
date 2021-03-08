import hashlib
import os
from multiprocessing import Process
from multiprocessing import Queue
from queue import Empty

import illusion.datamodel as dm
from illusion.crawler import Crawler


class Image:
    def __init__(self, id_=None, path=None, md5=None, faces_detected=None, tags=None, faces=None):
        self.id = id_
        self.path = path
        self.md5 = md5
        self.faces_detected = faces_detected
        self.tags = tags
        self.faces = faces

    def __repr__(self):
        return f"Image({self.__dict__})"

    @classmethod
    def wrap(cls, image):
        return cls(
            id_=image.id, path=image.path, md5=image.md5, faces_detected=image.faces_detected,
            tags={t.tag.name for t in image.tags}, faces=[Face.wrap(face) for face in image.faces]
        )


class Face:
    def __init__(self, x, y, w, h, deleted, person):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.deleted = deleted
        self.person = person

    @classmethod
    def wrap(cls, face):
        return cls(
            x=face.x, y=face.y, w=face.w, h=face.h, deleted=face.deleted, person=Person.wrap(face.person)
        )


class Person:
    def __init__(self, id_, name):
        self.id = id_
        self.name = name

    @classmethod
    def wrap(cls, person):
        return Person(id_=person.id, name=person.name)


class CrawlManager:
    def __init__(self, monitoring_folders):
        self.monitoring_folders = monitoring_folders
        self.new_images_queue = Queue()
        self.crawler = Crawler(new_images_queue=self.new_images_queue)

        self.crawler_proc = None

        self.run()

    def run(self):
        self.crawler_proc = Process(target=self.crawler.find_in_dirs, args=(self.monitoring_folders,))
        self.crawler_proc.start()

    def fetch(self):
        new_images = []
        while not self.new_images_queue.empty():
            new_images.append(self.new_images_queue.get())
        return new_images


class ProcessManager:
    def __init__(self, image_store, monitoring_folders, input_queue, output_queue):
        self.image_store = image_store
        self.crawl_manager = CrawlManager(monitoring_folders)
        self.crawl_manager.run()
        self.input_queue = input_queue
        self.output_queue = output_queue

    def check_new_images(self):
        """
        Get new images from the crawler and add them to the DB
        :return:
        """
        new_images = self.image_store.add_images(self.crawl_manager.fetch())

        if new_images:
            self.output_queue.put({"message": "new_images", "content": new_images})

        self.crawl_manager.run()

    def wait_for_incoming(self):
        """
        Wait for messages from gui. This is intended to be the longest part of the main loop
        :return:
        """
        try:
            self.input_queue.get(timeout=5)  # TODO adjust timeout
        except Empty:
            pass


class ImageStore:
    def __init__(self):
        pass

    def get_existing(self):
        return dm.Image.select()

    def add_images(self, paths):
        added = []
        for image_path in paths:
            new_id = self.add_image(image_path)
            if new_id is not None:
                added.append(new_id)

        return added

    def add_image(self, path):
        if os.path.isfile(path):
            md5 = hashlib.md5(open(path, 'rb').read()).hexdigest()
        else:
            return None
            # raise FileNotFoundError(f"File nod found: {path}")

        image = dm.Image.get_image(path=path)
        if image is not None:
            image.md5 = md5
            image.save()
            return None
        else:
            image = dm.Image.create(path=path, md5=md5)
            return Image.wrap(image)


def image_store_main_loop(monitoring_folders, input_queue: Queue = None, output_queue: Queue = None):
    """
    Start main loop for the database and helper processes.
    :param monitoring_folders: List of folders to pass on to the crawler for monitoring.
    :param input_queue: queue for receiving messages from gui
    :param output_queue: queue for sentding messages back to gui
    :return:
    """
    image_store = ImageStore()  # should this be moved inside process manager?

    existing_images = [Image.wrap(image) for image in image_store.get_existing()]
    output_queue.put({"message": "existing", "content": existing_images})

    proc_manager = ProcessManager(image_store, monitoring_folders, input_queue, output_queue)

    while True:
        proc_manager.wait_for_incoming()
        proc_manager.check_new_images()


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
#     face_extractor = FaceExtractor("/Volumes/External/dev/illusion/haarcascade_frontalface_default.xml")
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


def main_loop_test():
    image_store_main_loop()


if __name__ == "__main__":
    main_loop_test()

