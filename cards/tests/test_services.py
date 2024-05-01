import mimetypes
import os
from pathlib import Path

from PIL import Image
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest

from cards.services import (
    set_business_cart_post_data,
    resize_image_to_square,
    get_image_dimensions,
    create_business_card,
)
from cards.models import BusinessCard


User = get_user_model()


@pytest.fixture
def user() -> User:
    user = User.objects.create(username="testuser123", password="testpassword123")
    return user


@pytest.fixture
def in_memory_image():
    filename = "valid_image.jpg"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_image_path = os.path.join(current_dir, "test_data", "test_images", filename)
    content_type, _ = mimetypes.guess_type(test_image_path)
    with open(test_image_path, "rb") as f:
        file_content = f.read()
        in_memory_image = SimpleUploadedFile(filename, file_content, content_type)
    return in_memory_image


@pytest.mark.django_db
class TestCardsServices:
    def test_set_business_card_data(self, in_memory_image):
        request = HttpRequest()
        request.method = "POST"
        request.user = AnonymousUser()
        request.FILES["user_photo"] = in_memory_image
        post_data = set_business_cart_post_data(request=request)

        assert post_data["user_photo"] == in_memory_image
        assert post_data["user"] == request.user
        assert "csrfmiddlewaretoken" not in post_data

    def test_get_image_dimensions_return_image_resolution(self, in_memory_image):
        image = Image.open(in_memory_image)
        expected_width, expected_height = image.size
        width, height = get_image_dimensions(uploaded_image=in_memory_image)
        assert expected_width == width
        assert expected_height == height

    def test_resize_image_to_square_resize_image(self, in_memory_image, user):
        width, height = get_image_dimensions(uploaded_image=in_memory_image)
        assert width != height
        resized_image_path = resize_image_to_square(
            uploaded_image=in_memory_image, user=user
        )
        resized_image = Image.open(resized_image_path)
        new_width, new_height = resized_image.size
        assert new_width == new_height

    def test_create_business_card_create_obj(self, user, in_memory_image):
        assert BusinessCard.objects.count() == 0
        data = {
            "name_and_surname": "Test Name",
            "company": "testcompany",
            "phone_number": "+48132465825",
            "email": "user@gmail.com",
            "user_photo": in_memory_image,
            "vcard_address": "TYPE=WORK,POSTAL,PARCEL:;;One Microsoft Way;Redmond;WA;98052-6399;USA",
        }
        create_business_card(data=data, user=user)
        data.pop("user_photo")
        assert BusinessCard.objects.count() == 1
        created_card = BusinessCard.objects.get(user=user)
        for key, value in data.items():
            if key != "vcard":
                assert getattr(created_card, key) == value
        assert created_card.user_photo is not None
        assert created_card.vcard is not None
        os.remove(created_card.user_photo.path)
        os.remove(created_card.vcard.path)
