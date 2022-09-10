from image_store import Person


class FaceIdentifier:
    def __init__(self):
        pass

    def identify(self, face_thumbnail) -> Person:
        return Person(id=0, name=None)

    def add_to_index_and_identify(self, face_thumbnail) -> Person:
        return Person(id=0, name=None)
