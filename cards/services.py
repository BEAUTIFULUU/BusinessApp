import email
import os
import uuid
from io import BytesIO
from pathlib import Path
from typing import Tuple, Optional

import qrcode
import vobject
import requests
from django.core.files.base import ContentFile
from vobject import vCard
from PIL import Image
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
from django.http import HttpRequest, QueryDict
from django.shortcuts import get_object_or_404

from BusinessApp import settings
from cards.models import BusinessCard, ContactRequest
from cards.validators import (
    validate_business_card_duplication,
    validate_user_photo,
    validate_vcard_data,
)


def generate_vcard(data: dict[str, str], user_id: int) -> ContentFile:
    vcard_content = f"BEGIN:VCARD\n"
    vcard_content += f"VERSION:3.0\n"
    vcard_content += f"N:{data.get('last_name')};{data.get('first_name')}\n"
    vcard_content += f"FN:{data.get('name_and_surname')}\n"
    vcard_content += f"ORG:{data.get('company')}\n"
    vcard_content += f"TEL;TYPE=WORK,VOICE:{data.get('phone_number')}\n"
    vcard_content += f"EMAIL;TYPE=INTERNET:{data.get('email')}\n"
    vcard_content += f"ADR;TYPE=WORK:;;{data.get('street')};{data.get('city')};{data.get('region')};{data.get('postal_code')};{data.get('country')}\n"
    vcard_content += f"END:VCARD\n"

    return ContentFile(vcard_content, name=f"user_id-{user_id}.vcf")


def set_business_cart_post_data(request: HttpRequest) -> QueryDict:
    post_data = request.POST.copy()
    post_data["user_photo"] = request.FILES.get("user_photo")
    post_data["user"] = request.user
    post_data.pop("csrfmiddlewaretoken", None)
    return post_data


def resize_image_to_square(
        uploaded_image: InMemoryUploadedFile, user: User
) -> InMemoryUploadedFile:
    image = Image.open(uploaded_image)
    image = image.convert("RGB")
    width, height = image.size

    new_size = min(width, height)
    square_image = image.resize((new_size, new_size))

    output = BytesIO()
    square_image.save(output, format="JPEG")
    output.seek(0)

    image_name = f"user_id-{user.id}_{uuid.uuid4()}.jpg"
    return InMemoryUploadedFile(
        output, "ImageField", image_name, "image/jpeg", output.getbuffer().nbytes, None
    )


def get_image_dimensions(uploaded_image: InMemoryUploadedFile) -> Tuple[int, int]:
    image = Image.open(uploaded_image)
    width, height = image.size
    return width, height


def generate_qr_code(url: str, user_id: int) -> None:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color="black", back_color="white")
    file_name = f"qr_user_id-{user_id}.png"
    file_path = os.path.join("media", "qr_codes", file_name)
    qr_image.save(file_path)


def create_business_card(data: dict[str, any], user: User) -> BusinessCard:
    uploaded_image = data.get("user_photo")
    data.pop("vcard_address")
    validate_business_card_duplication(user=user)
    validate_user_photo(uploaded_image=uploaded_image)
    vcard = generate_vcard(data=data, user_id=user.id)

    width, height = get_image_dimensions(uploaded_image=uploaded_image)
    if width != height:
        resized_image = resize_image_to_square(uploaded_image=uploaded_image, user=user)
        uploaded_image = resized_image

    uploaded_image.name = f"user_id-{user.id}.jpg"

    data["vcard"] = vcard
    data["user_photo"] = uploaded_image
    generate_qr_code(url=f"{settings.DOMAIN}api/my_card/", user_id=user.id)

    return BusinessCard.objects.create(**data, user=user)


def get_user_card_qr_url(user: User) -> str:
    qr_image_path = f"{settings.DOMAIN}media/qr_codes/qr_user_id-{user.id}.png"
    return qr_image_path


def get_user_card_url(card_id: uuid.UUID) -> str:
    qr_url = f"{settings.DOMAIN}contact_request/{card_id}/phone_number"
    return qr_url


def get_business_card(user_id: uuid.UUID) -> BusinessCard:
    return get_object_or_404(BusinessCard, user_id=user_id)


def create_contact_request(
        data: dict[str, any], requestor: Optional[User], lead: User
) -> ContactRequest:
    data["lead"] = lead
    if requestor is not None and requestor.is_authenticated:
        data["requestor"] = requestor
    return ContactRequest.objects.create(**data)


def parse_vcard_data(vcard_file: SimpleUploadedFile) -> dict[str, str]:
    vcard_content = vcard_file.read().decode("utf-8")

    if not vcard_content:
        return {}

    try:
        vcard = vobject.readOne(vcard_content)
    except StopIteration:
        return {}

    vcard_data = {
        "phone": None,
        "name": None,
        "surname": None,
        "email": None,
        "comments": []  # Initialize comments list
    }

    if vcard.tel:
        vcard_data["phone"] = vcard.tel.value

    if vcard.n:
        vcard_data["surname"] = vcard.n.value.family
        vcard_data["name"] = vcard.n.value.given

    if vcard.email:
        vcard_data["email"] = vcard.email.value

    if vcard.org:
        company_name = vcard.org.value[0] if isinstance(vcard.org.value, list) else vcard.org.value
        vcard_data["comments"].append({"text": f"Company: {company_name}"})

    validate_vcard_data(vcard_data)

    return vcard_data


def get_phone_number_and_vcard(data):
    phone_number = data.get("phone_number")
    vcard = data.get("vcard")
    return phone_number, vcard


def send_data_to_ceremeo_api(data: dict[str, str]):
    try:
        response = requests.post(settings.CEREMEO_URL, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Error sending data to Ceremeo API: {e}"
