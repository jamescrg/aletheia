from django.db import models

from apps.matters.models import Matter


class Event(models.Model):
    LOCATION_CHOICES = [
        ("Zoom", "Zoom"),
        ("Virtual", "Virtual"),
        ("Phone", "Phone"),
        ("In-person", "In-person"),
    ]

    user_id = models.IntegerField(null=True)
    matter = models.ForeignKey(Matter, on_delete=models.CASCADE, null=True)
    date = models.DateField(null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    party = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=255, null=True)
    location = models.CharField(
        max_length=50, choices=LOCATION_CHOICES, blank=True, null=True
    )
    status = models.CharField(max_length=50, null=True)
    google_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.description} : {self.id}"

    class Meta:
        db_table = "app_event"
