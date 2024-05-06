from django.conf.urls.static import static
from django.urls import path

from BusinessApp import settings
from cards.views import (
    CreateCardView,
    MyCardView,
    ContactRequestFirstStepView,
    ContactRequestSecondStepView,
    ContactRequestThirdStepView,
    CompletedContactRequestView,
)

urlpatterns = (
    [
        path("create_card/", CreateCardView.as_view(), name="create_card"),
        path("my_card/", MyCardView.as_view(), name="card_info"),
        path(
            "contact_request/<uuid:card_id>/phone_number/",
            ContactRequestFirstStepView.as_view(),
            name="upload_phone_num",
        ),
        path(
            "contact_request/<uuid:card_id>/requestor_info/",
            ContactRequestSecondStepView.as_view(),
            name="requestor_info",
        ),
        path(
            "contact_request/<uuid:card_id>/contact_prefs/",
            ContactRequestThirdStepView.as_view(),
            name="contact_prefs",
        ),
        path(
            "contact_request/<uuid:card_id>/finish_meme/",
            CompletedContactRequestView.as_view(),
            name="finish_meme",
        ),
    ]
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
