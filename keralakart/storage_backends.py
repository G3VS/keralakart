import cloudinary.uploader
from django.core.files.storage import Storage
from django.conf import settings
import cloudinary
import os


class CloudinaryStorage(Storage):

    def _save(self, name, content):
        # Upload to Cloudinary
        response = cloudinary.uploader.upload(
            content,
            public_id=os.path.splitext(name)[0],
            overwrite=True,
            resource_type='auto'
        )
        return response['secure_url']

    def url(self, name):
        # If it's already a full Cloudinary URL return as is
        if name and name.startswith('http'):
            return name
        # Otherwise return local media URL
        return f"/media/{name}"

    def exists(self, name):
        return False

    def _open(self, name, mode='rb'):
        pass

    def delete(self, name):
        pass

    def listdir(self, path):
        return [], []

    def size(self, name):
        return 0