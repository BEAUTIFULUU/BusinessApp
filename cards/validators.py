import magic
from datetime import date, timedelta
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError
from PIL import Image
from django.utils.timezone import now

from BusinessApp import settings
from cards.models import BusinessCard, ContactRequest


def validate_image_format(uploaded_image: InMemoryUploadedFile) -> None:
    if uploaded_image is None:
        raise ValidationError("No image provided.")

    image_bytes = uploaded_image.read()
    mime = magic.Magic(mime=True)
    mime_type = mime.from_buffer(image_bytes[:2048])

    if not any(
        mime_type.startswith(content_type)
        for content_type in settings.WHITELISTED_IMAGE_TYPES.values()
    ):
        raise ValidationError(
            "Invalid image format. Only JPEG and PNG images are allowed."
        )

    extension = uploaded_image.name.split(".")[-1].lower()
    if extension not in settings.WHITELISTED_IMAGE_TYPES:
        raise ValidationError("Invalid image extension.")


def validate_vcard_format(uploaded_vcard: InMemoryUploadedFile) -> None:
    if uploaded_vcard is None:
        raise ValidationError("No vcard provided.")

    image_bytes = uploaded_vcard.read()
    mime = magic.Magic(mime=True)
    mime_type = mime.from_buffer(image_bytes[:2048])

    if not any(
        mime_type.startswith(content_type)
        for content_type in settings.WHITELISTED_VCARD_TYPES.values()
    ):
        raise ValidationError("Invalid vcard format. Only VCF vcards are allowed.")

    extension = uploaded_vcard.name.split(".")[-1].lower()
    if extension not in settings.WHITELISTED_VCARD_TYPES:
        raise ValidationError("Invalid vcard extension.")


def validate_image_size(uploaded_image: InMemoryUploadedFile) -> Image:
    min_width = 100
    min_height = 100
    max_width = 400
    max_height = 600

    if uploaded_image is None:
        raise ValidationError("No image provided.")

    image = Image.open(uploaded_image)
    width, height = image.size

    if width > max_width or height > max_height:
        raise ValidationError(
            f"Photo is too big. Max width: {max_width}, Max height: {max_height}"
        )

    if width < min_width or height < min_height:
        raise ValidationError(
            f"Photo is too small. Min width: {min_width}, Min height: {min_height}"
        )


def validate_user_photo(uploaded_image: InMemoryUploadedFile) -> None:
    validate_image_format(uploaded_image=uploaded_image)
    validate_image_size(uploaded_image=uploaded_image)


def validate_business_card_duplication(user: User) -> None:
    if BusinessCard.objects.filter(user=user).exists():
        raise ValidationError("Card already exists.")


def validate_vcard_data(vcard_data: dict) -> None:
    required_keys = ["phone", "name", "surname", "email", "comments"]

    for key in required_keys:
        if key not in vcard_data:
            raise ValidationError(f"Missing required key: {key}")

    if not vcard_data["phone"].startswith("+48"):
        raise ValidationError("Phone number must start with '+48'")


def validate_phone_number_for_contact_request(phone_number: str) -> None:
    contact_request = ContactRequest.objects.filter(phone_number=phone_number)
    if contact_request:
        raise ValidationError("You cannot create contact request for your own card.")


def validate_name_and_surname(name_and_surname: str) -> None:
    if " " not in name_and_surname:
        raise ValidationError("Name and surname must be separated by a space.")


def validate_date(date: date) -> None:
    if date < now().date():
        raise ValidationError("Date cannot be in the past.")
    if date > now().date() + timedelta(days=30):
        raise ValidationError("Date cannot be more than 30 days in the future.")
