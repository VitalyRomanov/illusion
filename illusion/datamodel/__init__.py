import peewee as pw
import os


def get_database_path():
    return os.path.join(os.environ["ILLUSION_CONF"], "illusion.db")


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
    md5 = pw.CharField(index=True)  # do not make this unique. this will be used to find duplicates
    faces_detected = pw.BooleanField(default=False)

    @classmethod
    def get_image(cls, id=None, path=None):
        try:
            if id is not None:
                return cls.get(id=id)
            if path is not None:
                return cls.get(path=path)
        except:
            return None

    @classmethod
    def get_tags(cls, image_id):
        return cls.get_image(id=image_id).tags

class Tag(IllusionDb):
    id = pw.AutoField()
    name = pw.CharField(index=True)

    @classmethod
    def get_tag_name(cls, tag_id):
        tag = cls.get(id=tag_id)
        return tag.name

    @classmethod
    def get_tag(cls, id=None, name=None):
        if id is not None:
            tag = cls.get(id=id)
        elif name is not None:
            tag = cls.get(name=name)
        else:
            raise ValueError("Either `id` or `name` should be provided")

        return tag

    @classmethod
    def get_or_create(cls, name):
        try:
            tag = cls.get(name=name)
        except:  # TagDoesNotExist:
            tag = cls.create(name=name)
        return tag




class Person(IllusionDb):
    id = pw.AutoField()
    name = pw.CharField(index=True, null=True)


class Face(IllusionDb):
    id = pw.AutoField()
    image = pw.ForeignKeyField(Image, backref="faces", on_delete="CASCADE", on_update="CASCADE")
    thumbnail_path = pw.CharField(max_length=4096, index=True, null=True)
    deleted = pw.BooleanField(default=False)
    recognized = pw.BooleanField(default=False)
    x = pw.IntegerField()
    y = pw.IntegerField()
    h = pw.IntegerField()
    w = pw.IntegerField()


class FacePerson(IllusionDb):
    face = pw.ForeignKeyField(Face, backref="person", on_delete="CASCADE", on_update="CASCADE")
    person = pw.ForeignKeyField(Person, backref="face", on_delete="CASCADE", on_update="CASCADE")

    class Meta:
        indexes = (
            (('face_id', 'person_id'), True),
        )
        primary_key = False


class ImageTag(IllusionDb):
    image = pw.ForeignKeyField(Image, backref="tags", on_delete="CASCADE", on_update="CASCADE")
    tag = pw.ForeignKeyField(Tag, backref="images", on_delete="CASCADE", on_update="CASCADE")

    class Meta:
        indexes = (
            (('image_id', 'tag_id'), True),
        )
        primary_key = False


class FaceSimilarity(IllusionDb):
    face = pw.ForeignKeyField(Face, backref="similar_to", on_delete="CASCADE", on_update="CASCADE")
    similar_to = pw.ForeignKeyField(Face, backref="similar_to", on_delete="CASCADE", on_update="CASCADE")

    class Meta:
        indexes = (
            (('face_id', 'similar_to_id'), True),
        )
        primary_key = False


def create_tables():
    database.create_tables([
        Image, Tag, Person, Face, ImageTag, FacePerson
    ])

create_tables()