import mimetypes
import os
from unittest.mock import patch

import requests_mock
from PIL import Image
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest

from BusinessApp import settings
from cards.services import (
    set_business_cart_post_data,
    resize_image_to_square,
    get_image_dimensions,
    create_business_card,
    get_user_card_qr_url,
    get_user_card_url,
    get_business_card,
    create_contact_request,
    parse_vcard_data,
    get_phone_number_and_vcard_from_request_data, send_data_to_ceremeo_api,
)
from cards.models import BusinessCard, ContactRequest

User = get_user_model()


@pytest.fixture
def ceremeo_api_mock():
    with requests_mock.Mocker() as m:
        yield m


@pytest.fixture
def user() -> User:
    user = User.objects.create(username="testuser123", password="testpassword123")
    return user


@pytest.fixture
def user_with_no_card() -> User:
    user = User.objects.create(username="testusr1111", password="testpsw1111")
    return user


@pytest.fixture
def business_card(user: User):
    business_card = BusinessCard.objects.create(
        name_and_surname="John Doe",
        company="testcompany",
        phone_number="+48264354758",
        email="user@gmail.com",
        user_photo=None,
        vcard=None,
        user=user,
    )
    return business_card


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


@pytest.fixture
def in_memory_vcard():
    filename = "valid_vcf_vcard.vcf"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_vcard_path = os.path.join(current_dir, "test_data", "test_vcards", filename)
    content_type, _ = mimetypes.guess_type(test_vcard_path)
    with open(test_vcard_path, "rb") as f:
        file_content = f.read()
        in_memory_vcard = SimpleUploadedFile(filename, file_content, content_type)
    return in_memory_vcard


@pytest.mark.django_db
class TestCardsServices:
    def test_set_business_card_data(self, in_memory_image: SimpleUploadedFile):
        request = HttpRequest()
        request.method = "POST"
        request.user = AnonymousUser()
        request.FILES["user_photo"] = in_memory_image
        post_data = set_business_cart_post_data(request=request)

        assert post_data["user_photo"] == in_memory_image
        assert post_data["user"] == request.user
        assert "csrfmiddlewaretoken" not in post_data

    def test_get_image_dimensions_return_image_resolution(
            self, in_memory_image: SimpleUploadedFile
    ):
        image = Image.open(in_memory_image)
        expected_width, expected_height = image.size
        width, height = get_image_dimensions(uploaded_image=in_memory_image)
        assert expected_width == width
        assert expected_height == height

    def test_resize_image_to_square_resize_image(
            self, in_memory_image: SimpleUploadedFile, user: User
    ):
        width, height = get_image_dimensions(uploaded_image=in_memory_image)
        assert width != height
        resized_image_path = resize_image_to_square(
            uploaded_image=in_memory_image, user=user
        )
        resized_image = Image.open(resized_image_path)
        new_width, new_height = resized_image.size
        assert new_width == new_height

    def test_create_business_card_create_obj(
            self, user: User, in_memory_image: SimpleUploadedFile
    ):
        with patch("cards.services.generate_qr_code") as mock_generate_qr_code:
            mock_generate_qr_code.return_value = "/path/to/mock_qr_code.png"

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
            assert created_card.vcard.name is not None
            os.remove(created_card.user_photo.path)
            os.remove(created_card.vcard.path)

    def test_get_user_card_qr_return_qr(self, user: User):
        qr_url = get_user_card_qr_url(user=user)
        assert qr_url == f"{settings.DOMAIN}media/qr_codes/qr_user_id-{user.id}.png"

    def test_get_user_card_url_return_url(self, business_card: BusinessCard):
        card_url = get_user_card_url(business_card.id)
        assert (
                card_url
                == f"{settings.DOMAIN}contact_request/{business_card.id}/phone_number"
        )

    def test_business_card_return_business_card_if_exists(
            self, user: User, business_card: BusinessCard
    ):
        result = get_business_card(user_id=user.id)
        assert result is not None

    def test_create_contact_request_create_obj_and_return_dict(
            self, user: User, user_with_no_card: User, in_memory_vcard: SimpleUploadedFile
    ):
        data = {"phone_number": "+48536485725", "vcard": in_memory_vcard}
        assert ContactRequest.objects.count() == 0
        returned_dict = create_contact_request(
            data=data, requestor=user_with_no_card, lead=user
        )
        assert returned_dict["phone"] == "+48536485725"
        assert "vcard" not in data
        created_contact = ContactRequest.objects.get(phone_number="+48536485725")
        assert created_contact.lead == user
        assert created_contact.requestor == user_with_no_card

    def test_create_contact_request_create_obj_and_return_dict_if_user_is_anonymous(
            self, user: User, in_memory_vcard: SimpleUploadedFile
    ):
        data = {"phone_number": "+48536485725", "vcard": in_memory_vcard}
        assert ContactRequest.objects.count() == 0
        returned_dict = create_contact_request(data=data, requestor=None, lead=user)
        assert returned_dict["phone"] == "+48536485725"
        created_contact = ContactRequest.objects.get(phone_number="+48536485725")
        assert created_contact.lead == user
        assert created_contact.requestor is None

    def test_parse_vcard_data_return_correct_dict(
            self, in_memory_vcard: SimpleUploadedFile
    ):
        expected_parsed_vcard_data = {
            "phone": "+48-758-334-536",
            "name": "Derik",
            "surname": "Stenerson",
            "email": "deriks@Microsoft.com",
            "comments": [{"text": "Company: Microsoft Corporation"}],
        }
        parsed_vcard_data = parse_vcard_data(vcard_file=in_memory_vcard)

        assert parsed_vcard_data == expected_parsed_vcard_data

    def get_phone_number_and_vcard_from_request_data_return_phone_num_and_vcard(
            self, in_memory_vcard: SimpleUploadedFile
    ):
        data = {
            "phone_number": "+48546824635",
            "vcard": in_memory_vcard,
        }
        phone_num, vcard = get_phone_number_and_vcard_from_request_data(data=data)
        assert phone_num == data["phone_number"]
        assert vcard == data["vcard"]


class TestSendingDataToCeremeo:
    ALLOWED_KEYS = [
        "campaign_token",
        "phone",
        "email",
        "external_id",
        "ip",
        "creator_id",
        "trader_id",
        "name",
        "surname",
        "pesel",
        "id_card",
        "account",
        "address_region",
        "address_city",
        "address_street",
        "address_building",
        "address_flat",
        "address_postcode",
        "correspondence_region",
        "correspondence_city",
        "correspondence_street",
        "correspondence_building",
        "correspondence_flat",
        "correspondence_postcode",
        "comments",
    ]

    @requests_mock.Mocker()
    def test_send_data_to_ceremeo_api(self, request_mocker):
        data = {
            "phone": "+48635495647"
        }
        requests_mocker.get(settings.CEREMEO_URL, status=200)
        send_data_to_ceremeo_api(data=data)


