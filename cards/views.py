from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from cards.models import BusinessCard
from cards.services import create_business_card, get_user_card_qr_url, get_user_card_url
from cards.forms import BusinessCardForm


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
        context = {
            "card_url": get_user_card_url(user=request.user),
            "qr_code": get_user_card_qr_url(user=request.user),
        }
        return render(request, "user_card_info.html", context)
