from django.urls import path
from .views import LatestPromotionsView, DatePromotionsView, PromotionDetailView

urlpatterns = [
    path('latest', LatestPromotionsView.as_view(), name='latest-promotions'),
    path('', DatePromotionsView.as_view(), name='date-promotions'),
    path('<uuid:promotion_id>', PromotionDetailView.as_view(), name='promotion-detail'),
]
