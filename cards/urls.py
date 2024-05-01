from django.conf.urls.static import static
from django.urls import path

from BusinessApp import settings
from cards.views import CreateCardView, MyCardView

urlpatterns = [
    path("create_card/", CreateCardView.as_view(), name="create_card"),
    path("my_card/", MyCardView.as_view(), name="card_info"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
