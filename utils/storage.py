

from django.core.files.storage import Storage



from django.conf import settings
from django.core.files.storage import Storage

class MyStorage(Storage):

    def open(self, name, mode='rb'):
        return super().open(name, mode='rb')

    def save(self, name, content, max_length=None):
        return super().save(name, content, max_length=None)

    def url(self, name):
        return "http//meiduo:8080/" + name

    def exists(self, name):
        return False

    def _save(self,*args,**kwargs):
        return False


