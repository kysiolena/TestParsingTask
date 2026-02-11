from django.contrib.postgres.fields import ArrayField
from django.db import models


class Status(models.TextChoices):
    NEW = "NW", "New"
    DONE = "DE", "Done"
    FAILED = "FD", "Failed"


class ProductInfo(models.Model):
    link = models.URLField(unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    color = models.CharField(max_length=100, null=True, blank=True)
    builtin_memory = models.CharField(max_length=20, null=True, blank=True)
    manufacturer = models.CharField(max_length=100, null=True, blank=True)
    price_regular = models.CharField(max_length=11, null=True, blank=True)
    price_sale = models.CharField(max_length=11, null=True, blank=True)
    sku = models.CharField(max_length=50, null=True, blank=True)
    reviews_count = models.IntegerField(null=True, blank=True)
    images = ArrayField(models.CharField(max_length=255), null=True, blank=True)
    characteristics = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
