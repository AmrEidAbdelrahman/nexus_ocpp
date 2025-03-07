from django.urls import path
from charging.consumers import ChargePointConsumer

websocket_urlpatterns = [
    path("ws/ocpp/<str:charger_id>/", ChargePointConsumer.as_asgi()),
]
