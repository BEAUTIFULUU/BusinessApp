import mimetypes
import os
from datetime import date

import pytest
from _pytest.fixtures import SubRequest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from cards.services import parse_vcard_data
from cards.validators import (
    validate_image_format,
    validate_business_card_duplication,
    validate_image_size,
    validate_vcard_data,
    validate_vcard_format,
    validate_phone_number_for_contact_request,
    validate_name_and_surname,
    validate_date,
)
from cards.models import BusinessCard, ContactRequest

User = get_user_model()


@pytest.fixture
def in_memory_file(request: SubRequest):
    folder_name, filename = request.param
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_image_path = os.path.join(current_dir, "test_data", folder_name, filename)
    content_type, _ = mimetypes.guess_type(test_image_path)
    with open(test_image_path, "rb") as f:
        file_content = f.read()
        in_memory_file = SimpleUploadedFile(filename, file_content, content_type)
    return in_memory_file


@pytest.fixture
def user() -> User:
    user = User.objects.create(username="testuser123", password="testpassword123")
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
def contact_request(user: User):
    contact_request = ContactRequest.objects.create(
        lead=user, requestor=None, phone_number="+48564835465"
    )
    return contact_request


class TestImageValidation:
    @pytest.mark.parametrize(
        "in_memory_file", [("test_images", "valid_image.jpg")], indirect=True
    )
    def test_validate_image_format_return_none_if_image_valid(self, in_memory_file):
        try:
            validate_image_format(uploaded_image=in_memory_file)
        except ValidationError as e:
            pytest.fail(str(e))

    @pytest.mark.parametrize(
        "in_memory_file", [("test_images", "fake_jpg_file.jpg")], indirect=True
    )
    def test_validate_image_format_raise_error_if_invalid_image_format(
        self, in_memory_file: SimpleUploadedFile
    ):
        with pytest.raises(ValidationError) as e:
            validate_image_format(uploaded_image=in_memory_file)
            assert (
                str(e.value)
                == "Invalid image format. Only JPEG and PNG images are allowed."
            )

    @pytest.mark.parametrize(
        "in_memory_file", [("test_images", "wrong_extension_image.ggg")], indirect=True
    )
    def test_validate_image_format_raise_error_if_image_invalid_image_extension(
        self, in_memory_file: SimpleUploadedFile
    ):
        with pytest.raises(ValidationError) as e:
            validate_image_format(uploaded_image=in_memory_file)
            assert str(e.value) == "Invalid image extension."

    @pytest.mark.parametrize(
        "in_memory_file", [("test_images", "valid_image.jpg")], indirect=True
    )
    def test_validate_image_size_does_not_raise_error_if_image_in_right_size(
        self, in_memory_file: SimpleUploadedFile
    ):
        try:
            validate_image_size(uploaded_image=in_memory_file)
        except ValidationError as e:
            pytest.fail(str(e))

    @pytest.mark.parametrize(
        "in_memory_file", [("test_images", "too_big_image.jpg")], indirect=True
    )
    def test_validate_image_size_raise_error_if_image_too_big(
        self, in_memory_file: SimpleUploadedFile
    ):
        with pytest.raises(ValidationError) as e:
            validate_image_size(uploaded_image=in_memory_file)
            assert str(e.value) == "Photo is too big. Max width: 400, Max height: 600"

    @pytest.mark.parametrize(
        "in_memory_file", [("test_images", "too_small_image.jpg")], indirect=True
    )
    def test_validate_image_size_raise_error_if_image_too_small(
        self, in_memory_file: SimpleUploadedFile
    ):
        with pytest.raises(ValidationError) as e:
            validate_image_size(uploaded_image=in_memory_file)
            assert str(e.value) == "Photo is too small. Min width: 100, Min height: 100"


class TestVcardValidation:
    @pytest.mark.parametrize(
        "in_memory_file", [("test_vcards", "valid_vcf_vcard.vcf")], indirect=True
    )
    def test_validate_vcard_format_return_none_if_vcard_valid(self, in_memory_file):
        try:
            validate_vcard_format(uploaded_vcard=in_memory_file)
        except ValidationError as e:
            pytest.fail(str(e))

    @pytest.mark.parametrize(
        "in_memory_file", [("test_vcards", "fake_vcf_file.vcf")], indirect=True
    )
    def test_validate_vcard_format_raise_error_if_invalid_vcard_format(
        self, in_memory_file: SimpleUploadedFile
    ):
        with pytest.raises(ValidationError) as e:
            validate_vcard_format(uploaded_vcard=in_memory_file)
            assert str(e.value) == "Invalid vcard format. Only VCF vcards are allowed."

    @pytest.mark.parametrize(
        "in_memory_file", [("test_vcards", "wrong_extension_vcard.ggg")], indirect=True
    )
    def test_validate_vcard_format_raise_error_if_vcard_invalid_vcard_extension(
        self, in_memory_file: SimpleUploadedFile
    ):
        with pytest.raises(ValidationError) as e:
            validate_vcard_format(uploaded_vcard=in_memory_file)
            assert str(e.value) == "Invalid vcard extension."


@pytest.mark.django_db
def test_validate_business_card_duplication_raise_error_if_user_already_has_card(
    business_card: BusinessCard, user: User
):
    with pytest.raises(ValidationError) as e:
        validate_business_card_duplication(user=user)
        assert str(e.value) == "Card already exists."


def test_validate_vcard_data_raise_error_if_key_missing():
    data = {
        "phone": "+48-758-334-536",
        "name": "Derik",
        "surname": "Stenerson",
        "comments": [{"text": "Company: Microsoft Corporation"}],
    }
    with pytest.raises(ValidationError) as e:
        validate_vcard_data(vcard_data=data)
        assert str(e.value) == "Missing required key: email"


def test_validate_vcard_data_raise_error_if_phone_not_polish():
    data = {
        "phone": "+50-758-334-536",
        "name": "Derik",
        "surname": "Stenerson",
        "email": "deriks@Microsoft.com",
        "comments": [{"text": "Company: Microsoft Corporation"}],
    }
    with pytest.raises(ValidationError) as e:
        validate_vcard_data(vcard_data=data)
        assert str(e.value) == "Phone number must start with '+48'"


@pytest.mark.django_db
def test_validate_phone_number_for_contact_request_raise_error_if_phone_number_duplicated(
    contact_request: ContactRequest,
):
    with pytest.raises(ValidationError) as e:
        validate_phone_number_for_contact_request(contact_request.phone_number)
        assert str(e.value) == "You cannot create contact request for your own card."


def test_validate_name_surname_raise_validation_error_if_space_not_in_it():
    with pytest.raises(ValidationError) as e:
        validate_name_and_surname(name_and_surname="testname")
        assert str(e.value) == "Name and surname must be separated by a space."


def test_validate_date_return_raise_error_if_date_in_past():
    with pytest.raises(ValidationError) as e:
        validate_date(date=date(2024, 4, 1))
        assert str(e.value) == "Date cannot be in the past."
