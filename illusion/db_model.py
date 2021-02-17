from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, func, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

images_to_tags = Table(
    "association", Base.metadata,
    Column("image_id", Integer, ForeignKey("images.image_id")),
    Column("tag_id", Integer, ForeignKey("tags.tag_id")),
)


class Images(Base):
    __tablename__ = "images"
    image_id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False)
    tags = relationship(
        "Tags", secondary=images_to_tags, back_populates="images"
    )


class Tags(Base):
    __tablename__ = "tags"
    tag_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    images = relationship(
        "Images", secondary=images_to_tags, back_populates="tags"
    )


from sqlalchemy import create_engine

engine = create_engine('sqlite:///illusion.sqlite')

from sqlalchemy.orm import sessionmaker

session = sessionmaker()
session.configure(bind=engine)
Base.metadata.create_all(engine)
i = Images(image_id=3, path="path1")
t = Tags(tag_id=3, name="Vitalyyyyy!!!!")
i.tags.append(t)

t.images.
s = session()
s.add(i)
s.add(t)
s.commit()
