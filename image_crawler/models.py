from django.db import models


class Photo(models.Model):
    file_path = models.CharField(max_length=200)
    thumbnail_path = models.CharField(max_length=200)
    type = models.CharField(max_length=15)
    creation_date = models.DateTimeField()
    tracking_start_date = models.DateTimeField(auto_now_add=True)
