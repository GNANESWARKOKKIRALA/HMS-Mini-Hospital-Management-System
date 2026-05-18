from django.db import models
from django.conf import settings
from doctors.models import AvailabilitySlot
from patients.models import PatientProfile


class Appointment(models.Model):
    slot = models.OneToOneField(
        AvailabilitySlot,
        on_delete=models.CASCADE,
        related_name='appointment'
    )
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    booked_at = models.DateTimeField(auto_now_add=True)

    # Google Calendar event IDs (stored after creation)
    patient_calendar_event_id = models.CharField(max_length=200, blank=True)
    doctor_calendar_event_id = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.patient.user.get_full_name()} → {self.slot}"
