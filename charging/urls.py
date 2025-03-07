from django.urls import path, include
from rest_framework.routers import DefaultRouter

from charging.views.charger_views import ChargingViewSet
from charging.views.remote_transaction_views import RemoteTransactionViewSet
from charging.views.transaction_views import TransactionViewSet

router = DefaultRouter()
router.register(r'charger', ChargingViewSet, basename='charging')
router.register(r'transactions', TransactionViewSet, basename='transactions')
router.register(r'remote-transactions', RemoteTransactionViewSet, basename='remote-transactions')

urlpatterns = [
    path("", include(router.urls)),
]
