from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class DoctorSignUpForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    specialty = forms.CharField(required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'specialty', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.ROLE_DOCTOR
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Create doctor profile
            from doctors.models import DoctorProfile
            DoctorProfile.objects.create(
                user=user,
                specialty=self.cleaned_data['specialty']
            )
        return user


class PatientSignUpForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    phone = forms.CharField(required=False, max_length=20)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'date_of_birth', 'phone', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.ROLE_PATIENT
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Create patient profile
            from patients.models import PatientProfile
            PatientProfile.objects.create(
                user=user,
                date_of_birth=self.cleaned_data['date_of_birth'],
                phone=self.cleaned_data.get('phone', '')
            )
        return user


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'autofocus': True}))
