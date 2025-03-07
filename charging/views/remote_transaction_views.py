from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from charging.models import Charger, Transaction
import json
import logging

class RemoteTransactionViewSet(viewsets.ViewSet):
    """
    A viewset for viewing and editing remote transactions.
    """

    @action(detail=False, methods=["post"], url_path="start")
    def start_transaction(self, request):
        """API to remotely start a transaction."""
        charger_id = request.data.get("charger_id")
        id_tag = request.data.get("id_tag")
        connector_id = request.data.get("connector_id", 1)

        charger = Charger.objects.filter(charger_id=charger_id).first()
        if not charger:
            return Response({"error": "Charger not found"}, status=404)

        # Send OCPP message to charger
        channel_layer = get_channel_layer()
        message = [2, "12350", "RemoteStartTransaction", {"idTag": id_tag, "connectorId": connector_id}]
        logging.debug(f"Sending OCPP message to {charger_id}: {json.dumps(message)}")

        async_to_sync(channel_layer.group_send)(f"ocpp_{charger_id}", {
            "type": "ocpp.message",
            "action": "RemoteStartTransaction",
            "message": message
        })
        logging.debug(f"Sending OCPP message to {charger_id}: {json.dumps(message)}")


        return Response({"status": "Request sent"})
    
    @action(detail=False, methods=["post"], url_path="stop")
    def stop_transaction(self, request):
        """API to remotely stop a transaction."""
        transaction_id = request.data.get("transaction_id")

        transaction = Transaction.objects.filter(transaction_id=transaction_id).first()
        if not transaction:
            return Response({"error": "Transaction not found"}, status=404)

        # Send OCPP message to charger
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.send)(f"ocpp_{transaction.charger.charger_id}", {
            "type": "ocpp.message",
            "action": "RemoteStopTransaction",
            "message": [2, "12351", "RemoteStopTransaction", {"transactionId": transaction_id}]
        })

        return Response({"status": "Request sent"})
