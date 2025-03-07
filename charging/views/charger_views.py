from rest_framework import viewsets, permissions

from charging.models import Charger
from charging.serializers.charger_serializers import ChargerSerializer



class ChargingViewSet(viewsets.ModelViewSet):
    queryset = Charger.objects.all()
    serializer_class = ChargerSerializer
    permission_classes = [permissions.IsAuthenticated]

