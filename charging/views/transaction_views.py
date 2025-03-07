

from rest_framework import viewsets
from charging.models import Transaction
from charging.serializers.transaction_serializers import TransactionSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['charger', 'user_id_tag', 'start_time', 'stop_time']
