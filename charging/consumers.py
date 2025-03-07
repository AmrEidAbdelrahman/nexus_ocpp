from channels.generic.websocket import AsyncWebsocketConsumer
from ocpp.v16 import ChargePoint as cp
from asgiref.sync import sync_to_async
from ocpp.v16 import call_result
from django.utils import timezone
from ocpp.routing import on
from charging.models import Charger, Transaction
import json
import logging
from django.contrib.auth import get_user_model


from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

class JWTAuthMiddleware(BaseMiddleware):
    """Custom middleware to authenticate WebSocket connections using JWT."""
    
    async def __call__(self, scope, receive, send):
        query_string = scope["query_string"].decode()
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]
        print("token => ", token)

        if token:
            validated_user = await self.get_user_from_token(token)
            print("validated_user => ", validated_user)
            scope["user"] = validated_user
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token):
        """Validate the JWT token and return the authenticated user."""
        try:
            validated_token = JWTAuthentication().get_validated_token(token)
            return JWTAuthentication().get_user(validated_token)
        except Exception:
            return AnonymousUser()


class ChargePointHandler(cp):
    """ Custom OCPP handler that extends ChargePoint. """

    @on("BootNotification")
    async def on_boot_notification(self, **kwargs):
        """Register a charger when it starts up."""
        charge_point_vendor = kwargs.get("charge_point_vendor")
        charge_point_model = kwargs.get("charge_point_model")

        charger, created = await sync_to_async(Charger.objects.get_or_create)(
            charger_id=self.id,
            defaults={"model": charge_point_model, "vendor": charge_point_vendor}
        )
        if not created:
            charger.last_seen = timezone.now()
            await sync_to_async(charger.save)()

        print(f"Registered Charger: {charger.charger_id}")
        return call_result.BootNotification(
            current_time=timezone.now().isoformat(),
            interval=10,
            status="Accepted"
        )

    @on("Heartbeat")
    async def on_heartbeat(self, **kwargs):
        """Update charger last seen timestamp."""
        charger = await sync_to_async(Charger.objects.filter(charger_id=self.id).first)()
        if charger:
            charger.last_seen = timezone.now()
            await sync_to_async(charger.save)()

        print(f"Heartbeat received from {self.id}")
        return call_result.Heartbeat(current_time=timezone.now().isoformat())

    @on("Authorize")
    async def on_authorize(self, id_tag):
        """Validate RFID card before starting a session."""
        user = await sync_to_async(User.objects.filter(username=id_tag).first)()
        if user:
            return call_result.Authorize(id_tag_info={"status": "Accepted"})
        return call_result.Authorize(id_tag_info={"status": "Invalid"})

    @on("StartTransaction")
    async def on_start_transaction(self, connector_id, id_tag, meter_start, timestamp, **kwargs):
        """Start a charging session."""
        charger = await sync_to_async(Charger.objects.filter(charger_id=self.id, connected_user=self.user).first)()
        if not charger:
            return call_result.StartTransaction(id_tag_info={"status": "Rejected"}, transaction_id="0")
        
        transaction_id = int(timezone.now().timestamp())
        transaction = await sync_to_async(Transaction.objects.create)(
            transaction_id=transaction_id,
            charger=charger,
            user_id_tag=id_tag,
            start_time=timezone.now()
        )

        print(f"Started Transaction: {transaction.transaction_id}")
        return call_result.StartTransaction(
            transaction_id=transaction.transaction_id,
            id_tag_info={"status": "Accepted"}
        )

    @on("StopTransaction")
    async def on_stop_transaction(self, transaction_id, meter_stop, timestamp, **kwargs):
        """End a charging session."""
        transaction = await sync_to_async(Transaction.objects.filter(transaction_id=transaction_id, user=self.user).first)()
        if not transaction:
            return call_result.StopTransaction(id_tag_info={"status": "Invalid"})

        transaction.stop_time = timezone.now()
        transaction.energy_consumed = meter_stop / 1000.0  # Assuming meter_stop is in Wh
        await sync_to_async(transaction.save)()

        print(f"Stopped Transaction: {transaction.transaction_id}")
        return call_result.StopTransaction(id_tag_info={"status": "Accepted"})

    @on("RemoteStartTransaction")
    async def on_remote_start_transaction(self, id_tag, connector_id, **kwargs):
        """Start a transaction from the backend."""
        return call_result.RemoteStartTransaction(status="Accepted")

    @on("RemoteStopTransaction")
    async def on_remote_stop_transaction(self, transaction_id, **kwargs):
        """Stop a transaction from the backend."""
        transaction = await sync_to_async(Transaction.objects.filter(transaction_id=transaction_id).first)()
        if not transaction:
            return call_result.RemoteStopTransaction(status="Rejected")

        transaction.stop_time = timezone.now()
        await sync_to_async(transaction.save)()
        return call_result.RemoteStopTransaction(status="Accepted")


class ChargePointConsumer(AsyncWebsocketConsumer):
    """ WebSocket consumer for handling OCPP connections. """

    async def connect(self):
        """Handle new WebSocket connection."""
        self.charger_id = self.scope["url_route"]["kwargs"]["charger_id"]
        self.group_name = "ocpp_" + self.charger_id
        self.user = self.scope["user"]

        if not self.user or self.user.is_anonymous:
            await self.close()
            return

        self.cp = ChargePointHandler(self.charger_id, self)

        await self.assign_charger_to_user()
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"Charger {self.charger_id} connected by {self.user.username}")

    async def assign_charger_to_user(self):
        """Assign charger to authenticated user if not already assigned."""
        charger = await database_sync_to_async(Charger.objects.filter(charger_id=self.charger_id).first)()
        if charger and charger.connected_user is None:
            charger.connected_user = self.user
            await database_sync_to_async(charger.save)()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection by unassigning the user from the charger."""
        print(f"Charger {self.charger_id} disconnected by {self.user.username if self.user.is_authenticated else 'Unknown'}")
        print(f"Close connection with {self.user}")
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        charger = await database_sync_to_async(Charger.objects.filter(charger_id=self.charger_id, connected_user=self.user).first)()
        print(f"Charger: {charger}")
        if charger:
            charger.connected_user = None
            await database_sync_to_async(charger.save)()

        if charger:
            charger.last_seen = timezone.now()
            await database_sync_to_async(charger.save)()


    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        print(f"Received message from {self.charger_id}", text_data)
        message = str(text_data)
        await self.cp.route_message(message)

    async def ocpp_message(self, event):
        """Handle messages sent from `channel_layer.send()`."""
        logging.info(f"WebSocket sending OCPP message to {self.charger_id}: {json.dumps(event['message'])}")
        await self.send(text_data=json.dumps(event["message"]))
