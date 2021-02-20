import cv2

class FaceExtractor:
    def __init__(self, model_path) -> None:
        self.face_cascade = cv2.CascadeClassifier(model_path)

    def __call__(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        return [(x, y, w, h, cv2.resize(image[y:y+h, x:x+w], (299, 299))) for (x, y, w, h) in faces]


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

    fe = FaceExtractor(args.face_detector_model)

    img = cv2.imread(args.input_image)
    face_boxes = fe(img)
    boxed_faces_img = draw_boxes(img, face_boxes)
    cv2.imwrite(args.output_image, boxed_faces_img)
