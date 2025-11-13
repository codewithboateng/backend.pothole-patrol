import os

from celery import Celery
from .tasks import BaseTask # noqa

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mainProj.settings")

app = Celery("mainProj")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


app.Task = BaseTask
