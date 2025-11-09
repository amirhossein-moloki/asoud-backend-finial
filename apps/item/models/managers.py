from django.db import models

class ItemManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()