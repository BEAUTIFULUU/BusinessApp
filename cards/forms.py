from django import forms
from django.core.exceptions import ValidationError
from phonenumber_field.formfields import PhoneNumberField
from cards.validators import (
    validate_vcard_format,
    validate_user_photo,
    validate_phone_number_for_contact_request,
)


class AlphaCharsValidator:
    def __call__(self, value):
        if not value.replace(" ", "").isalpha():
            raise ValidationError(
                "Name and surname can only contain alphabetic characters."
            )


class BusinessCardForm(forms.Form):
    name_and_surname = forms.CharField(
        max_length=100, validators=[AlphaCharsValidator()]
    )
    company = forms.CharField(max_length=100)
    phone_number = PhoneNumberField(region="PL")
    email = forms.EmailField(max_length=320)
    user_photo = forms.ImageField(validators=[validate_user_photo])
    vcard_address = forms.CharField(max_length=200)


class FirstStepContactFormPhoneNumber(forms.Form):
    phone_number = PhoneNumberField(
        region="PL",
        required=False,
        validators=[validate_phone_number_for_contact_request],
    )
    vcard = forms.FileField(
        label="Wyślij wizytówkę", required=False, validators=[validate_vcard_format]
    )

    def clean(self):
        cleaned_data = super().clean()
        phone_number = cleaned_data.get("phone_number")
        vcard = cleaned_data.get("vcard")

        if phone_number and vcard:
            raise forms.ValidationError(
                "You need to upload either phone number or vCard, not both."
            )

        return cleaned_data
