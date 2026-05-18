from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction, IntegrityError
from doctors.models import AvailabilitySlot
from patients.models import PatientProfile
from .models import Appointment
from .calendar_service import create_appointment_calendar_events
from accounts.email_service import send_booking_confirmation
from doctors.decorators import patient_required


@patient_required
def book_slot(request, slot_id):
    """
    Design Decision — Race Condition Handling:
    We use SELECT FOR UPDATE inside a DB transaction to lock the slot row
    before checking is_booked. This prevents two concurrent requests from
    both seeing is_booked=False and creating duplicate bookings.
    The OneToOneField on Appointment is a second line of defence at the DB level.
    """
    if request.method != 'POST':
        return redirect('list_doctors')

    patient_profile = get_object_or_404(PatientProfile, user=request.user)

    try:
        with transaction.atomic():
            # Lock the row — any concurrent request waits here
            slot = AvailabilitySlot.objects.select_for_update().get(id=slot_id)

            if slot.is_booked:
                messages.error(request, 'Sorry, this slot was just booked by someone else.')
                return redirect('doctor_slots', doctor_id=slot.doctor.id)

            slot.is_booked = True
            slot.save(update_fields=['is_booked'])

            appointment = Appointment.objects.create(slot=slot, patient=patient_profile)

        # Outside transaction: non-critical side-effects
        send_booking_confirmation(appointment)
        create_appointment_calendar_events(appointment)

        messages.success(request, 'Appointment booked successfully!')
        return redirect('patient_dashboard')

    except AvailabilitySlot.DoesNotExist:
        messages.error(request, 'Slot not found.')
        return redirect('list_doctors')
    except IntegrityError:
        # OneToOneField uniqueness constraint triggered — concurrent booking
        messages.error(request, 'This slot was just taken. Please choose another.')
        return redirect('list_doctors')
