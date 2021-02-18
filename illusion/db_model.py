import hashlib
import os
import peewee as pw


def get_database_path():
    return "illusion.db"


database = pw.SqliteDatabase(get_database_path(), pragmas={'foreign_keys': 1})


def get_database():
    # home = str(Path.home())
    return database


class IllusionDb(pw.Model):
    class Meta:
        database = get_database()


class Image(IllusionDb):
    id = pw.AutoField()
    path = pw.CharField(max_length=4096, index=True, unique=True)
    md5 = pw.CharField(index=True) # TODO unique


class Tag(IllusionDb):
    id = pw.AutoField()
    name = pw.CharField(index=True)


class Person(IllusionDb):
    id = pw.AutoField()
    name = pw.CharField(index=True)


class Face(IllusionDb):
    id = pw.AutoField()
    image = pw.ForeignKeyField(Image, backref="faces", on_delete="CASCADE", on_update="CASCADE")
    path = pw.CharField(max_length=4096, index=True, unique=True)


class FacePerson(IllusionDb):
    face = pw.ForeignKeyField(Face, backref="people", on_delete="CASCADE", on_update="CASCADE")
    person = pw.ForeignKeyField(Person, backref="faces", on_delete="CASCADE", on_update="CASCADE")


class ImageTag(IllusionDb):
    image = pw.ForeignKeyField(Image, backref="tags", on_delete="CASCADE", on_update="CASCADE")
    tag = pw.ForeignKeyField(Tag, backref="images", on_delete="CASCADE", on_update="CASCADE")

    class Meta:
        indexes = (
            (('image_id', 'tag_id'), True),
        )
        primary_key = False


class DbManager:
    def __init__(self):
        self.database = get_database()
        self.create_tables()
        # self.database.connect()

    def create_tables(self):
        self.database.create_tables([
            Image, Tag, Person, Face, ImageTag, FacePerson
        ])

    def add_image(self, path):
        if os.path.isfile(path):
            md5 = hashlib.md5(open(path,'rb').read()).hexdigest()
        else:
            md5 = "" # TODO remove

        image = Image.create(path=path, md5=md5)

        return image

    def add_tags_to_image(self, image, tags):
        for tag in tags:
            try:
                t = Tag.get(name=tag)
            except: # TagDoesNotExist:
                t = Tag.create(name=tag)
            ImageTag.create(image=image, tag=t)

    def add_person(self, name):
        person = Person.create(name=name)
        return person

    def add_face(self, face_path, image, person=None):
        face = Face.create(image=image, path=face_path)

        if person is not None:
            FacePerson.create(face=face, person=person)

        return face

    # def __del__(self):
    #     self.database.close()


if __name__ == "__main__":
    manager = DbManager()
    image1 = manager.add_image("image/path")
    image2 = manager.add_image("image2/path")
    manager.add_tags_to_image(image1, ["tag1", "tag2"])
    manager.add_tags_to_image(image2, ["tag1"])
    person = manager.add_person("Dude")
    manager.add_face("face1/path", image1, person)
    manager.add_face("face2/path", image2)

