import mimetypes
import os
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile, InMemoryUploadedFile
from django.test import Client
from django.urls import reverse
from cards.models import BusinessCard

User = get_user_model()


@pytest.fixture
def authenticated_user() -> User:
    user = User.objects.create(username="testuser123", password="testpassword123")
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
        response = client.post(reverse("create_card"), data=data, format="mulipart")
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
        response = client.post(reverse("create_card"), data=data, format="mulipart")
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
        response = client.post(reverse("create_card"), data=data, format="mulipart")
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
        response = client.post(reverse("create_card"), data=data, format="mulipart")
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
        response = client.post(reverse("create_card"), data=data, format="mulipart")
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
