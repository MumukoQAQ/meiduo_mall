from django.apps import AppConfig
import os

class GoodsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.goods'

    def ready(self):
        if os.environ.get('RUN_MAIN') == 'true':
            from .utils import start
            start()
