import hashlib
import os
import illusion.datamodel as dm


class Tag:
    @staticmethod
    def get_or_create(name):
        try:
            tag = dm.Tag.get(name=name)
        except:  # TagDoesNotExist:
            tag = dm.Tag.create(name=name)
        return tag


class TagSet(set):
    def __init__(self, image):
        self._image = image

    def iter(self):
        return self._image.tags

    def add(self, tag_name):
        tag = Tag.get_or_create(tag_name)
        # ImageTag.create(image=image, tag=t)
        dm.ImageTag.create(image=self._image, tag=tag)

    def __repr__(self):
        return {t.name for t in self._image.tags}

    def update(self, tags):
        for tag in tags:
            self.add(tag)

    def pop(self, tag):
        dm.ImageTag.delete().where(dm.ImageTag.image_id == self._image.id and dm.ImageTag.tag_id == tag)


class FaceSet(set):
    def __init__(self, image):
        self._image = image

    def iter(self):
        return self._image.faces

    def __repr__(self):
        return {t.name for t in self._image.faces}

    def pop(self, face_id):
        dm.Face.delete().where(Face.id == face_id)


class Image:
    def __init__(self, path):
        if os.path.isfile(path):
            md5 = hashlib.md5(open(path, 'rb').read()).hexdigest()
        else:
            raise FileNotFoundError(f"File nod found: {path}")

        self._image = dm.Image.create(path=path, md5=md5)
        self._tags = TagSet(self._image)
        self._faces = FaceSet(self._image)

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
    def tags(self):
        return self._tags

    def faces(self):
        return self._image.faces

    def detect_faces(self):
        pass

    def add_tags(self, tags):
        for tag in tags:
            self._tags.add(tag)


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
    def __init__(self, image, thumbnail_path):
        self._face = dm.Face.create(image=image, path=thumbnail_path)

    @property
    def id(self):
        return self._face.id

    @property
    def image(self):
        return self._face.image

    @property
    def thumbnail_path(self):
        return self._face.thumbnail_path

    def __del__(self):
        pass
        # dm.Face.delete().where(Face.id == self._face.id)
        # TODO
        #  mark as removed


if __name__ == "__main__":
    image = Image("/Volumes/External/dev/illusion/test_photo.jpg")
    image.add_tags(["!!", "##"])

