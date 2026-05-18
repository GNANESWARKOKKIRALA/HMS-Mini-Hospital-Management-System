from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .decorators import doctor_required
from .models import AvailabilitySlot, DoctorProfile
from .forms import AvailabilitySlotForm
from appointments.models import Appointment
import datetime


@doctor_required
def doctor_dashboard(request):
    profile = get_object_or_404(DoctorProfile, user=request.user)
    today = datetime.date.today()
    upcoming_slots = AvailabilitySlot.objects.filter(
        doctor=profile, date__gte=today
    ).order_by('date', 'start_time')
    upcoming_appointments = Appointment.objects.filter(
        slot__doctor=profile,
        slot__date__gte=today
    ).select_related('patient__user', 'slot').order_by('slot__date', 'slot__start_time')

    context = {
        'profile': profile,
        'upcoming_slots': upcoming_slots,
        'upcoming_appointments': upcoming_appointments,
        'google_connected': bool(request.user.google_access_token),
    }
    return render(request, 'doctors/dashboard.html', context)


@doctor_required
def add_slot(request):
    profile = get_object_or_404(DoctorProfile, user=request.user)
    if request.method == 'POST':
        form = AvailabilitySlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.doctor = profile
            try:
                slot.save()
                messages.success(request, 'Availability slot added successfully.')
            except Exception:
                messages.error(request, 'A slot at that time already exists.')
            return redirect('doctor_dashboard')
    else:
        form = AvailabilitySlotForm()
    return render(request, 'doctors/add_slot.html', {'form': form})


@doctor_required
def delete_slot(request, slot_id):
    profile = get_object_or_404(DoctorProfile, user=request.user)
    slot = get_object_or_404(AvailabilitySlot, id=slot_id, doctor=profile)
    if slot.is_booked:
        messages.error(request, 'Cannot delete a booked slot.')
    else:
        slot.delete()
        messages.success(request, 'Slot deleted.')
    return redirect('doctor_dashboard')
