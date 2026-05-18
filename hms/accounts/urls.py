from django.urls import path
from . import views

urlpatterns = [
    path('signup/doctor/', views.doctor_signup, name='doctor_signup'),
    path('signup/patient/', views.patient_signup, name='patient_signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('google/', views.google_auth, name='google_auth'),
    path('google/callback/', views.google_callback, name='google_callback'),
]
