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
    thumbnail_path = pw.CharField(max_length=4096, index=True, unique=True)


class FacePerson(IllusionDb):
    face = pw.ForeignKeyField(Face, backref="people", on_delete="CASCADE", on_update="CASCADE")
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
    database.create_tables([
        Image, Tag, Person, Face, ImageTag, FacePerson
    ])

create_tables()