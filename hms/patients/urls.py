from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('doctors/', views.list_doctors, name='list_doctors'),
    path('doctors/<int:doctor_id>/slots/', views.doctor_slots, name='doctor_slots'),
]
