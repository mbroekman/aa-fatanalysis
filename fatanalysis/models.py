from django.db import models
from allianceauth.eveonline.models import EveCharacter
from django.utils import timezone

class UploadPeriod(models.Model):
    PERIOD_CHOICES = (
        (30, '30 Days'),
        (90, '90 Days'),
    )
    upload_date = models.DateTimeField(default=timezone.now)
    uploader = models.CharField(max_length=255)
    period_type = models.IntegerField(choices=PERIOD_CHOICES)
    
    def __str__(self):
        return f"{self.get_period_type_display()} Upload ({self.upload_date.strftime('%Y-%m-%d %H:%M')})"

class FatEntry(models.Model):
    period = models.ForeignKey(UploadPeriod, on_delete=models.CASCADE, related_name='fat_entries')
    character = models.ForeignKey(EveCharacter, on_delete=models.SET_NULL, null=True, blank=True)
    character_name = models.CharField(max_length=255)
    total_fats = models.IntegerField(default=0)
    
    # Stores dynamic fleet types (e.g. Strategic, QRF, Astartes) without hardcoding columns
    fat_details = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.character_name} - {self.total_fats} FATs"
