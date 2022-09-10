from pathlib import Path

import peewee as pw


def get_database(database_path):
    pw_database = pw.SqliteDatabase(database_path, pragmas={'foreign_keys': 1})

    class IllusionDb(pw.Model):
        class Meta:
            database = pw_database

    class Image(IllusionDb):
        id = pw.AutoField()
        path = pw.CharField(max_length=4096, index=True, unique=True)
        md5 = pw.CharField(index=True)  # do not make this unique. this will be used to find duplicates
        faces_detected = pw.BooleanField(default=False)
        tags_detected = pw.BooleanField(default=False)

        @classmethod
        def create_image(cls, path=None, md5=None):
            if isinstance(path, Path):
                path = str(path.resolve())
            return cls.create(path=path, md5=md5)

        @classmethod
        def get_image_if_exists(cls, id=None, path=None):
            if isinstance(path, Path):
                path = str(path.resolve())
            try:
                if id is not None:
                    return cls.get(id=id)
                if path is not None:
                    return cls.get(path=path)
            except:
                return None

        @classmethod
        def get_all_images(cls):
            return cls.select()

        @classmethod
        def get_tags(cls, image_id):
            return cls.get_image_if_exists(id=image_id).tags

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
        id = pw.IntegerField(primary_key=True)
        name = pw.CharField(index=True, null=True)

        @classmethod
        def get_or_create(cls, id, name=None):
            try:
                tag = cls.get(id=id)
            except:  # TagDoesNotExist:
                tag = cls.create(id=id, name=name)
            return tag

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

        @classmethod
        def create_face(
                cls, image, x, y, w, h, thumbnail_path=None
                    ):
            if thumbnail_path is not None and isinstance(thumbnail_path, Path):
                thumbnail_path = str(thumbnail_path.resolve())
            return cls.create(
                image=image, thumbnail_path=thumbnail_path, x=x, y=y, w=w, h=h
            )

    class FacePerson(IllusionDb):
        face = pw.ForeignKeyField(Face, backref="person", on_delete="CASCADE", on_update="CASCADE")
        person = pw.ForeignKeyField(Person, backref="faces", on_delete="CASCADE", on_update="CASCADE")

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
        pw_database.create_tables([
            Image, Tag, Person, Face, ImageTag, FacePerson
        ])

    create_tables()

    return Image, Tag, Person, Face, ImageTag, FacePerson
