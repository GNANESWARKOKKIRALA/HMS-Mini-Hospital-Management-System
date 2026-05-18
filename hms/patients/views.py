from django.shortcuts import render, get_object_or_404
from doctors.models import DoctorProfile, AvailabilitySlot
from appointments.models import Appointment
from .models import PatientProfile
from doctors.decorators import patient_required
import datetime


@patient_required
def patient_dashboard(request):
    profile = get_object_or_404(PatientProfile, user=request.user)
    my_appointments = Appointment.objects.filter(
        patient=profile
    ).select_related('slot__doctor__user', 'slot').order_by('slot__date', 'slot__start_time')

    context = {
        'profile': profile,
        'my_appointments': my_appointments,
        'google_connected': bool(request.user.google_access_token),
    }
    return render(request, 'patients/dashboard.html', context)


@patient_required
def list_doctors(request):
    today = datetime.date.today()
    # Only show doctors who have at least one available future slot
    doctors = DoctorProfile.objects.filter(
        availability_slots__date__gte=today,
        availability_slots__is_booked=False
    ).distinct()
    return render(request, 'patients/list_doctors.html', {'doctors': doctors})


@patient_required
def doctor_slots(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    today = datetime.date.today()
    import datetime as dt
    now_time = dt.datetime.now().time()

    slots = AvailabilitySlot.objects.filter(
        doctor=doctor,
        is_booked=False,
        date__gte=today,
    ).order_by('date', 'start_time')

    # Filter out past slots for today
    available_slots = [
        s for s in slots
        if s.date > today or (s.date == today and s.start_time > now_time)
    ]

    return render(request, 'patients/doctor_slots.html', {
        'doctor': doctor,
        'slots': available_slots,
    })
