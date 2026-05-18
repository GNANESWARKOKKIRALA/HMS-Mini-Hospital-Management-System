from django.db import models
from django.conf import settings
import datetime


class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    specialty = models.CharField(max_length=100)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} — {self.specialty}"


class AvailabilitySlot(models.Model):
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='availability_slots'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']
        # Prevent duplicate slots for the same doctor at same time
        unique_together = ('doctor', 'date', 'start_time')

    def is_future(self):
        import datetime
        now = datetime.datetime.now()
        slot_dt = datetime.datetime.combine(self.date, self.start_time)
        return slot_dt > now

    def __str__(self):
        return f"Dr. {self.doctor.user.get_full_name()} | {self.date} {self.start_time}–{self.end_time}"
