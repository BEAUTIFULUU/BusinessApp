import mimetypes
import os
from datetime import date

import pytest
import requests_mock
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile, InMemoryUploadedFile
from django.test import Client
from django.urls import reverse

from BusinessApp import settings
from cards.models import BusinessCard, ContactRequest

User = get_user_model()


@pytest.fixture
def request_mocker():
    with requests_mock.Mocker() as mocker:
        yield mocker


@pytest.fixture
def authenticated_user() -> User:
    user = User.objects.create(username="testuser123645", password="testpassword12367")
    return user


@pytest.fixture
def authenticated_user_with_business_card() -> User:
    user = User.objects.create(username="test111", password="test999111")
    return user


@pytest.fixture
def client(authenticated_user: User) -> Client:
    client = Client()
    client.force_login(authenticated_user)
    return client


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


@pytest.fixture
def business_card(
    authenticated_user_with_business_card: User,
    in_memory_image: SimpleUploadedFile,
    in_memory_vcard: SimpleUploadedFile,
):
    business_card = BusinessCard.objects.create(
        name_and_surname="John Doe",
        company="testcompany",
        phone_number="+48264354758",
        email="user@gmail.com",
        user_photo=in_memory_image,
        vcard=in_memory_vcard,
        user=authenticated_user_with_business_card,
    )
    return business_card


@pytest.fixture
def user() -> User:
    user = User.objects.create(username="testuser65740", password="testpassword123")
    return user


@pytest.fixture
def user_second_step_contact() -> User:
    user = User.objects.create(username="testus11", password="tstpsw111")
    return user


@pytest.fixture
def user_third_step_contact() -> User:
    user = User.objects.create(username="tstsu123", password="tsts543345")
    return user


@pytest.fixture
def contact_request_1st_step(user: User) -> ContactRequest:
    contact_request = ContactRequest.objects.create(
        lead=user,
        requestor=None,
        phone_number="+48564835465",
        name_and_surname=None,
        email=None,
        company_or_contact_place=None,
        contact_date=None,
        contact_topic=None,
        form_step=1,
    )
    return contact_request


@pytest.fixture
def contact_request_2nd_step(user_second_step_contact: User) -> ContactRequest:
    contact_request = ContactRequest.objects.create(
        lead=user_second_step_contact,
        requestor=None,
        phone_number="+48374958767",
        name_and_surname="testname",
        email="usr@gmail.com",
        company_or_contact_place="testplace",
        contact_date=None,
        contact_topic=None,
        form_step=2,
    )
    return contact_request


@pytest.fixture
def contact_request_3th_step(user_third_step_contact: User) -> ContactRequest:
    contact_request = ContactRequest.objects.create(
        lead=user_third_step_contact,
        requestor=None,
        phone_number="+48253917465",
        name_and_surname="tstnam",
        email="usr1@gmail.com",
        company_or_contact_place="testplace",
        contact_date=date(2024, 5, 1),
        contact_topic="testtopic",
        form_step=3,
    )
    return contact_request


@pytest.mark.django_db
class TestCreateCardView:
    def test_create_card_view_return_200_for_authenticated_user(self, client: Client):
        response = client.get(reverse("create_card"))
        assert response.status_code == 200

    def test_create_card_view_return_403_for_anonymous_user(self):
        client = Client()
        response = client.get(reverse("create_card"))
        assert response.status_code == 403

    def test_create_card_view_return_302_for_authenticated_user_when_card_created(
        self,
        client: Client,
        in_memory_image: InMemoryUploadedFile,
        authenticated_user: User,
    ):
        assert BusinessCard.objects.filter(user=authenticated_user).count() == 0
        data = {
            "name_and_surname": "Test Name",
            "company": "testcompany",
            "phone_number": "+48132465825",
            "email": "user@gmail.com",
            "user_photo": in_memory_image,
            "vcard_address": "TYPE=WORK,POSTAL,PARCEL:;;One Microsoft Way;Redmond;WA;98052-6399;USA",
        }
        response = client.post(reverse("create_card"), data=data, format="multipart")
        assert response.status_code == 302
        assert BusinessCard.objects.count() == 1
        created_card = BusinessCard.objects.first()
        os.remove(created_card.user_photo.path)
        os.remove(created_card.vcard.path)

    def test_create_card_view_return_400_if_name_and_surname_invalid(
        self,
        in_memory_image: InMemoryUploadedFile,
        client: Client,
    ):
        data = {
            "name_and_surname": "111111",
            "company": "testcompany",
            "phone_number": "+48507444365",
            "email": "user@gmail.com",
            "user_photo": in_memory_image,
            "vcard_address": "TYPE=WORK,POSTAL,PARCEL:;;One Microsoft Way;Redmond;WA;98052-6399;USA",
        }
        response = client.post(reverse("create_card"), data=data, format="multipart")
        assert response.status_code == 400
        assert BusinessCard.objects.count() == 0

    def test_create_card_view_return_400_if_phone_not_polish(
        self,
        in_memory_image: InMemoryUploadedFile,
        client: Client,
    ):
        data = {
            "name_and_surname": "Test Name",
            "company": "testcompany",
            "phone_number": "+50507444365",
            "email": "user@gmail.com",
            "user_photo": in_memory_image,
            "vcard_address": "TYPE=WORK,POSTAL,PARCEL:;;One Microsoft Way;Redmond;WA;98052-6399;USA",
        }
        response = client.post(reverse("create_card"), data=data, format="multipart")
        assert response.status_code == 400
        assert BusinessCard.objects.count() == 0

    def test_create_card_view_return_400_if_phone_fake(
        self,
        in_memory_image: InMemoryUploadedFile,
        client: Client,
    ):
        data = {
            "name_and_surname": "Test Name",
            "company": "testcompany",
            "phone_number": "+48111111111",
            "email": "user@gmail.com",
            "user_photo": in_memory_image,
            "vcard_address": "TYPE=WORK,POSTAL,PARCEL:;;One Microsoft Way;Redmond;WA;98052-6399;USA",
        }
        response = client.post(reverse("create_card"), data=data, format="multipart")
        assert response.status_code == 400
        assert BusinessCard.objects.count() == 0

    def test_create_card_view_return_400_if_email_invalid(
        self,
        in_memory_image: InMemoryUploadedFile,
        client: Client,
    ):
        data = {
            "name_and_surname": "Test Name",
            "company": "testcompany",
            "phone_number": "+48111111111",
            "email": "asdggdsa",
            "user_photo": in_memory_image,
            "vcard_address": "TYPE=WORK,POSTAL,PARCEL:;;One Microsoft Way;Redmond;WA;98052-6399;USA",
        }
        response = client.post(reverse("create_card"), data=data, format="multipart")
        assert response.status_code == 400
        assert BusinessCard.objects.count() == 0


@pytest.mark.django_db
class TestMyCardViewView:
    def test_my_card_view_return_200_for_authenticated_user_with_business_card(
        self,
        client: Client,
        business_card: BusinessCard,
        in_memory_image: SimpleUploadedFile,
        in_memory_vcard: SimpleUploadedFile,
    ):
        client.force_login(business_card.user)
        response = client.get(reverse("card_info"))
        assert response.status_code == 200
        assert b"card-url" in response.content
        assert b"qr-code-img" in response.content
        os.remove(f"media/images/{in_memory_image.name}")
        os.remove(f"media/vcard_files/{in_memory_vcard.name}")

    def test_my_card_view_return_302_for_authenticated_user_with_no_business_card(
        self, client: Client
    ):
        response = client.get(reverse("card_info"))
        assert response.status_code == 302

    def test_my_card_view_return_403_for_anonymous_user(self):
        client = Client()
        response = client.get(reverse("card_info"))
        assert response.status_code == 403


@pytest.mark.django_db
class TestContactRequestFirstStepView:
    def test_contact_request_first_step_view_return_200_for_anonymous_user(
        self, business_card: BusinessCard, request_mocker
    ):
        client = Client()
        request_mocker.get(settings.CEREMEO_URL, status_code=200)
        response = client.get(
            reverse("upload_phone_num", kwargs={"card_id": business_card.id})
        )
        assert response.status_code == 200

    def test_contact_request_first_step_view_return_302_when_anonymous_user_post_phone_number(
        self, business_card: BusinessCard, request_mocker
    ):
        client = Client()
        data = {"phone_number": "+48564738467"}
        request_mocker.post(settings.CEREMEO_URL, status_code=200)
        response = client.post(
            reverse("upload_phone_num", kwargs={"card_id": business_card.id}),
            data=data,
            format="json",
        )
        assert response.status_code == 302
        created_contact = ContactRequest.objects.get(phone_number=data["phone_number"])
        assert created_contact.form_step == 2
        assert created_contact.requestor is None

    def test_contact_request_first_step_view_return_302_when_authenticated_user_post_phone_number(
        self,
        client: Client,
        request_mocker,
        business_card: BusinessCard,
        authenticated_user_with_business_card: User,
    ):
        data = {"phone_number": "+48564738467"}
        client.force_login(authenticated_user_with_business_card)
        request_mocker.post(settings.CEREMEO_URL, status_code=200)
        response = client.post(
            reverse("upload_phone_num", kwargs={"card_id": business_card.id}),
            data=data,
            format="json",
        )
        assert response.status_code == 302
        created_contact = ContactRequest.objects.get(phone_number=data["phone_number"])
        assert created_contact.form_step == 2
        assert created_contact.requestor == authenticated_user_with_business_card

    def test_contact_request_first_step_view_return_400_when_anonymous_user_upload_empty_fields(
        self, business_card: BusinessCard, request_mocker
    ):
        client = Client()
        request_mocker.post(settings.CEREMEO_URL, status_code=200)
        response = client.post(
            reverse("upload_phone_num", kwargs={"card_id": business_card.id}),
            data={},
            format="json",
        )
        assert response.status_code == 400

    def test_contact_request_first_step_view_return_302_if_form_step_invalid_for_view(
        self,
        contact_request_2nd_step: ContactRequest,
        client: Client,
        business_card: BusinessCard,
        request_mocker,
        authenticated_user_with_business_card,
    ):
        data = {f"phone_number": "+48564728343"}
        client.force_login(authenticated_user_with_business_card)
        request_mocker.post(settings.CEREMEO_URL, status_code=200)
        response = client.post(
            reverse("upload_phone_num", kwargs={"card_id": business_card.id}),
            data=data,
            format="json",
        )
        assert response.status_code == 302


@pytest.mark.django_db
class TestContactRequestSecondStepView:
    def test_contact_request_second_step_view_return_200_for_anonymous_user(
        self,
        business_card: BusinessCard,
        contact_request_2nd_step: ContactRequest,
        user_second_step_contact,
    ):
        client = Client(user_second_step_contact)
        response = client.get(
            (
                reverse("requestor_info", kwargs={"card_id": business_card.id})
                + f"?phone_number={contact_request_2nd_step.phone_number}"
            )
        )
        assert response.status_code == 200

    def test_contact_request_second_step_view_return_302_if_form_step_invalid_for_view(
        self,
        business_card: BusinessCard,
        contact_request_1st_step: ContactRequest,
    ):
        client = Client(contact_request_1st_step.requestor)
        response = client.get(
            (
                reverse("requestor_info", kwargs={"card_id": business_card.id})
                + f"?phone_number={contact_request_1st_step.phone_number}"
            )
        )
        assert response.status_code == 302

    def test_contact_request_second_step_view_return_302_when_data_posted(
        self,
        business_card: BusinessCard,
        request_mocker,
        contact_request_1st_step: ContactRequest,
    ):
        client = Client()
        data = {
            "name_and_surname": "test user",
            "email": "testemail@gmail.com",
            "company_or_contact_place": "sadffsd",
            "phone_number": "+48564835465",
        }
        url = (
            reverse("requestor_info", kwargs={"card_id": business_card.id})
            + f"?phone_number={contact_request_1st_step.phone_number}"
        )
        request_mocker.post(settings.CEREMEO_URL, status_code=200)
        response = client.post(url, data=data)
        updated_contact = ContactRequest.objects.get(id=contact_request_1st_step.id)
        assert response.status_code == 302
        assert updated_contact.name_and_surname == data["name_and_surname"]
        assert updated_contact.email == data["email"]
        assert (
            updated_contact.company_or_contact_place == data["company_or_contact_place"]
        )
        assert updated_contact.form_step == 3
