from django.urls import path
from .views import CreateOrderView, GetQRInfoView, WebhookView, CheckOrderStatusView

urlpatterns = [
    path('create-order/', CreateOrderView.as_view(), name='create-order'),
    path('qr-info/', GetQRInfoView.as_view(), name='qr-info'),
    path('webhook/', WebhookView.as_view(), name='webhook'),
    path('check-order/<str:order_id>/', CheckOrderStatusView.as_view(), name='check-order-status'),
]
