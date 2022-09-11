from django.http import HttpRequest
from django.shortcuts import render

from base.models import Image
from pathlib import Path
import crawler


def image_list(request: HttpRequest):
    if request.method == 'GET':
        images = Image.objects.all()
        context = {'images': images}
        return render(request, 'base/image_list.html', context)
