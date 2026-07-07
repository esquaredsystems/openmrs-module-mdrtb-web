from django.apps import AppConfig
from utilities import report_queue


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        report_queue.start_background_poller()
