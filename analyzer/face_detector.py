import logging
from pathlib import Path
from typing import List

import cv2
import wget

from image_store import Face, Image


class FaceDetector:
    def __init__(self, model_path: Path) -> None:
        # model_path = config["face_extractor_model"]

        if not model_path.is_file():
            logging.info("Downloading haarcascade_frontalface_default.xml")
            wget.download(
                url="https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades"
                    "/haarcascade_frontalface_default.xml",
                out=str(model_path.parent.resolve())
            )
        self.face_cascade = cv2.CascadeClassifier(str(model_path.resolve()))

    def detect_bounding_boxes(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, minNeighbors=10)
        return faces

    def get_faces(self, image):
        faces = self.detect_bounding_boxes(image)

        return [
            Face(
                id=None, person=None, deleted=False,
                x=x, y=y, w=w, h=h, thumbnail=image[y:y + h, x:x + w]
            )
            for (x, y, w, h) in faces
        ]

    def detect_faces(self, image) -> List[Face]:
        return [
            Face(id=None, x=x, y=y, w=w, h=h, deleted=False, person=None)
            for (x, y, w, h) in self.detect_bounding_boxes(image)
        ]

    def add_faces(self, image: Image):
        faces = self.detect_faces(image)
        image.add_faces(faces)
        return image


def draw_boxes(image, boxes):
    image = image.copy()
    for (x, y, w, h) in boxes:
        cv2.rectangle(image, (x, y), (x+w, y+h), (255, 0, 0), 2)
    return image
    

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("face_detector_model")
    parser.add_argument("input_image")
    parser.add_argument("output_image")

    args = parser.parse_args()

    fe = FaceDetector(args.face_detector_model)

    img = cv2.imread(args.input_image)
    face_boxes = fe.get_faces(img)
    boxed_faces_img = draw_boxes(img, face_boxes)
    cv2.imwrite(args.output_image, boxed_faces_img)
