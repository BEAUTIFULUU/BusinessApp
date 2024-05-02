import uuid

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views import View

from cards.models import BusinessCard
from cards.services import (
    create_business_card,
    get_user_card_qr_url,
    get_user_card_url,
    get_business_card,
    create_contact_request,
    parse_vcard_data, send_data_to_ceremeo_api,
)
from cards.forms import BusinessCardForm, FirstStepContactFormPhoneNumber
from cards.validators import validate_contact_request_post_data


class CreateCardView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        if not request.user.is_authenticated:
            return HttpResponseForbidden("You must be logged in.")
        form = BusinessCardForm()
        return render(request, "create_card.html", {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = BusinessCardForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                create_business_card(data=form.cleaned_data, user=request.user)
                return HttpResponseRedirect(reverse("card_info"))
            except ValidationError as e:
                return HttpResponseBadRequest(e.message)
        else:
            return render(
                request, "form_validation_error.html", {"form": form}, status=400
            )


class MyCardView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        if not request.user.is_authenticated:
            return HttpResponseForbidden("You must be logged in.")
        elif not BusinessCard.objects.filter(user=request.user).exists():
            messages.info(
                request, "You are being redirected to create a business card."
            )
            return HttpResponseRedirect(reverse("create_card"))
        business_card = get_business_card(user_id=request.user.id)
        context = {
            "card_url": get_user_card_url(card_id=business_card.id),
            "qr_code": get_user_card_qr_url(user=request.user),
        }
        return render(request, "user_card_info.html", context)


class ContactRequestPhoneInputView(View):
    def get(self, request: HttpRequest, card_id: uuid.UUID) -> HttpResponse:
        business_card = get_object_or_404(BusinessCard, id=card_id)
        form = FirstStepContactFormPhoneNumber()
        context = {
            "name_and_surname": business_card.name_and_surname,
            "company": business_card.company,
            "lead_photo": business_card.user_photo,
            "form": form,
        }
        return render(request, "contact_phone_number.html", context)

    def post(self, request: HttpRequest, card_id: uuid.UUID) -> HttpResponseRedirect:
        business_card = get_object_or_404(BusinessCard, id=card_id)
        form = FirstStepContactFormPhoneNumber(request.POST, request.FILES)
        phone_number = request.POST.get("phone_number")
        vcard = request.FILES.get("vcard")
        if phone_number and vcard:
            return render(
                request,
                "contact_phone_number_form_error.html",
                {
                    "error_message": "You need to upload either phone number or vCard, not both."
                },
                status=400,
            )

        if form.is_valid():
            if not vcard:
                form.cleaned_data.pop("vcard")
                create_contact_request(
                    data=form.cleaned_data,
                    requestor=request.user,
                    lead=business_card.user,
                )
            else:
                vcard_data = parse_vcard_data(vcard_file=vcard)
                error_message = send_data_to_ceremeo_api(data=vcard_data)
                if error_message:
                    return render(
                        request,
                        "contact_phone_number_form_error.html",
                        {"error_message": error_message},
                        status=500,
                    )
            return HttpResponse("success")
        else:
            return render(
                request,
                "contact_phone_number_form_error.html",
                {"form": form},
                status=400,
            )
