from django.urls import path
from .views import PromotionsListView, PromotionDetailView

urlpatterns = [
    path('', PromotionsListView.as_view(), name='promotions-list'),
    path('<uuid:promotion_id>', PromotionDetailView.as_view(), name='promotion-detail'),
]
