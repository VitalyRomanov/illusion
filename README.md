# Illusion

## Setup

1. Install [miniconda3](https://docs.conda.io/en/latest/miniconda.html)
2. Install environment `conda env create -f environment.yml`
3. ???

## Running 

test face extraction

```
python illusion/FaceExtractor.py haarcascade_frontalface_default.xml test_photo.jpg test_photo_out.jpg
```

## Roadmap
- [ ] Choose storage schema
- [ ] Choose database
- [ ] Implement continuous scanning folder for images
- [ ] Implement saving scan results in a database
- [ ] Implement fingerprinting with histogram for [near duplicate detection](https://stackoverflow.com/questions/11541154/checking-images-for-similarity-with-opencv)
- [ ] Find suitable on-disk index for high dimensional vectors (for similarity queries, e.g. searching similar images or similar faces) (check [annoy](https://github.com/spotify/annoy) or [faiss](https://github.com/facebookresearch/faiss/wiki/Installing-Faiss))
- [ ] Implement extracting faces from images and saving them in data storage
- [ ] Implement model for face grouping
- [ ] Train model for face grouping
- [ ] Implement similarity analizatior for faces stored in database
- [ ] Implement image search with natural language query using pretrained yolo models
- [ ] Implement graphical interface
