from django.urls import path

from .views import PromotionsListView

urlpatterns = [
    path("", PromotionsListView.as_view(), name="promotions-list"),
]
