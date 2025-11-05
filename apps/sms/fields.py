from django.db import models
from django.contrib.postgres.fields import ArrayField

class CustomArrayField(ArrayField):
    def db_type(self, connection):
        if connection.vendor == 'sqlite':
            return 'json'
        return super().db_type(connection)

    def get_prep_value(self, value):
        if isinstance(value, list):
            return value
        return super().get_prep_value(value)