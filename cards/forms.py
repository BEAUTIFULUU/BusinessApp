from django import forms
from django.core.exceptions import ValidationError
from phonenumber_field.formfields import PhoneNumberField


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
    user_photo = forms.ImageField()
    vcard_address = forms.CharField(max_length=200)
