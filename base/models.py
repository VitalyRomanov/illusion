from django.db import models


class Image(models.Model):

    file_path = models.CharField(max_length=100)
    last_modified_time = models.BigIntegerField()
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-last_modified_time']

    def __str__(self):
        return f'File {self.file_path}'
