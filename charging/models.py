from django.db import models
from django.utils import timezone

class Charger(models.Model):
    charger_id = models.CharField(max_length=100, unique=True)
    model = models.CharField(max_length=100)
    vendor = models.CharField(max_length=100)
    last_seen = models.DateTimeField(auto_now=True)
    connected_user = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.model} ({self.charger_id})"

class Transaction(models.Model):
    transaction_id = models.CharField(max_length=100, unique=True)
    charger = models.ForeignKey(Charger, on_delete=models.CASCADE)
    user_id_tag = models.CharField(max_length=50)
    start_time = models.DateTimeField(default=timezone.now)
    stop_time = models.DateTimeField(null=True, blank=True)
    energy_consumed = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Transaction {self.transaction_id} for {self.charger.charger_id}"
