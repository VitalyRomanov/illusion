import os

from django.apps import AppConfig


# To prevent double launching, runserver with option --noreload

class CrawlerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crawler'
    IS_RUNNING = False

    def ready(self):
        if not self.IS_RUNNING:
            self.IS_RUNNING = True
            print(os.getpid())
