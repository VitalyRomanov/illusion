import hashlib
import os

import cv2

import illusion.datamodel as dm
from illusion.FaceExtractor import FaceExtractor


class ImageStore:
    def __init__(self):
        pass


class Tag:
    @staticmethod
    def get_or_create(name):
        try:
            tag = dm.Tag.get(name=name)
        except:  # TagDoesNotExist:
            tag = dm.Tag.create(name=name)
        return tag

    @staticmethod
    def get(id=None, name=None):
        if id is not None:
            tag = dm.Tag.get(id=id)
        elif name is not None:
            tag = dm.Tag.get(name=name)
        else:
            raise ValueError("Either `id` or `name` should be provided")

        return tag


class TagSet(set):
    def __init__(self, image):
        self._image = image
        self.update_local_tags()

    def update_local_tags(self):
        self.local_tags = {t.tag.name for t in self._image.tags}

    def iter(self):
        return self._image.tags

    def add(self, tag_name):
        if tag_name not in self.local_tags:
            tag = Tag.get_or_create(tag_name)
            # ImageTag.create(image=image, tag=t)
            dm.ImageTag.create(image=self._image, tag=tag)
            self.update_local_tags()

    def __repr__(self):
        return repr(self.local_tags)

    def update(self, tags):
        tags = [tag for tag in tags if tag not in self.local_tags]
        for tag in tags:
            self.add(tag)
        self.update_local_tags()

    def pop(self, tag_name):
        if tag_name in self.local_tags:
            tag = Tag.get(name=tag_name)
            rows_removed = dm.ImageTag.delete().where(dm.ImageTag.image_id == self._image.id and dm.ImageTag.tag_id == tag.id).execute()
            self.update_local_tags()


class FaceSet(set):
    def __init__(self, image):
        self._image = image

    def iter(self):
        return self._image.faces

    def __repr__(self):
        return {t.name for t in self._image.faces}

    def pop(self, face_id):
        dm.Face.delete().where(Face.id == face_id).execute()


class Image:

    face_extractor = FaceExtractor("/Volumes/External/dev/illusion/haarcascade_frontalface_default.xml")
    histogram_index = None

    def __init__(self, path=None, from_id=None):
        if path is not None:
            if os.path.isfile(path):
                md5 = hashlib.md5(open(path, 'rb').read()).hexdigest()
            else:
                raise FileNotFoundError(f"File nod found: {path}")

            self._image = self.get_image(path=path)
            if self._image is not None:
                self._image.md5 = md5
                self._image.save()
            else:
                self._image = self.create_image(path, md5)

        elif from_id is not None:
            self._image = self.get_image(id=from_id)

        self._tags = TagSet(self._image)
        self._faces = FaceSet(self._image)

    def get_image(self, id=None, path=None):
        try:
            if id is not None:
                return dm.Image.get(id=id)
            if path is not None:
                return dm.Image.get(path=path)
        except:
            return None

    def create_image(self, path, md5):
        return dm.Image.create(path=path, md5=md5)

    @property
    def id(self):
        return self._image.id

    @property
    def path(self):
        return self._image.path

    @property
    def md5(self):
        return self._image.md5

    @property
    def faces_detected(self):
        return self._image.faces_detected

    def tags(self):
        return self._tags

    def faces(self):
        return self._image.faces

    def detect_faces(self):
        faces = self.face_extractor(cv2.imread(self._image.path))

        for_analysis = []
        for x, y, w, h, thumbnail in faces:
            face = Face(image=self._image, x=x, y=y, w=w, h=h)
            face.set_thumbnail_path(
                os.path.join(
                    os.environ["ILLUSION_CONF"],
                    os.path.join("face_thumbnails", f"thumbnail_{face.id}.jpg")
                )
            )
            cv2.imwrite(face.thumbnail_path, thumbnail)
            for_analysis.append(face.thumbnail_path)

        self._image.faces_detected = True
        self._image.save()
        # TODO
        #  run analysis
        #  decide on person name assignment after clustering

    def add_tags(self, tags):
        for tag in tags:
            self._tags.add(tag)

    def remove_tags(self, tags):
        for tag in tags:
            self._tags.pop(tag)


class Person:
    def __init__(self, name):
        self._person = dm.Person.create(name=name)

    @property
    def id(self):
        return self._person.id

    @property
    def name(self):
        return self._person.name


class Face:

    encoding_model = None
    face_index = None

    def __init__(self, image, x, y, w, h):
        self._face = dm.Face.create(image=image, x=x, y=y, w=w, h=h, deleted=False)

    @property
    def id(self):
        return self._face.id

    @property
    def image(self):
        return self._face.image

    @property
    def thumbnail_path(self):
        return self._face.thumbnail_path

    def set_thumbnail_path(self, path):
        self._face.thumbnail_path = path
        self._face.save()

    # def __del__(self):
    #     self._face.deleted = True  # this will set deleted flag on destructor
    #     self._face.save()

    # def encode(self, thumbnail=None):
    #     if thumbnail is None:
    #         thumbnail = cv2.imread(self._face.thumbnail_path)
    #     encoding = self.encoding_model(thumbnail)
    #     return encoding
    #
    # def add_to_face_index(self, encoding=None):
    #     if encoding is None:
    #         encoding = self.encode()
    #     self.face_index.register(encoding)

    def recognize(self, thumbnail=None):
        if thumbnail is None:
            thumbnail = cv2.imread(self._face.thumbnail_path)
        encoding = self.encoding_model(thumbnail)
        self.face_index.register(self._face.id, encoding)
        self.face_index.find_similar(encoding)


def main_test():
    image = Image("/Volumes/External/dev/illusion/test_photo.jpg")
    image.add_tags(["!!", "##"])
    image.add_tags(["??"])
    image.remove_tags(["??"])
    if image.faces_detected is False:
        image.detect_faces()
    print()

if __name__ == "__main__":
    main_test()

