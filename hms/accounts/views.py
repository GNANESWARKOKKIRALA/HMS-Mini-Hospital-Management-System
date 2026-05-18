from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .forms import DoctorSignUpForm, PatientSignUpForm, EmailLoginForm
from .models import User
from .email_service import send_welcome_email
import requests
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import os


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def doctor_signup(request):
    if request.method == 'POST':
        form = DoctorSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            send_welcome_email(user)
            messages.success(request, 'Welcome! Your doctor account has been created.')
            return redirect('doctor_dashboard')
    else:
        form = DoctorSignUpForm()
    return render(request, 'accounts/doctor_signup.html', {'form': form})


def patient_signup(request):
    if request.method == 'POST':
        form = PatientSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            send_welcome_email(user)
            messages.success(request, 'Welcome! Your patient account has been created.')
            return redirect('patient_dashboard')
    else:
        form = PatientSignUpForm()
    return render(request, 'accounts/patient_signup.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = EmailLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    if request.user.is_doctor():
        return redirect('doctor_dashboard')
    elif request.user.is_patient():
        return redirect('patient_dashboard')
    return redirect('login')


# ─── Google OAuth2 ────────────────────────────────────────────────────────────

def _build_flow():
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=settings.GOOGLE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    return flow


@login_required
def google_auth(request):
    flow = _build_flow()
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
    )
    request.session['google_auth_state'] = state
    return redirect(auth_url)


@login_required
def google_callback(request):
    state = request.session.get('google_auth_state')
    flow = _build_flow()
    flow.fetch_token(authorization_response=request.build_absolute_uri())

    credentials = flow.credentials
    user = request.user
    user.google_access_token = credentials.token
    user.google_refresh_token = credentials.refresh_token
    user.google_token_expiry = credentials.expiry
    user.save()

    messages.success(request, 'Google Calendar connected successfully!')
    return redirect('dashboard')
