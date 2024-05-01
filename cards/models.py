import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from phonenumber_field.modelfields import PhoneNumberField


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.username


class BusinessCard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name_and_surname = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    phone_number = PhoneNumberField()
    email = models.EmailField(max_length=320)
    user_photo = models.ImageField(
        upload_to="images/",
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "png"])],
    )
    vcard = models.FileField(upload_to="vcard_files/")
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, default=uuid.uuid4
    )
