from django import forms
from .models import AvailabilitySlot
import datetime


class AvailabilitySlotForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))

    class Meta:
        model = AvailabilitySlot
        fields = ['date', 'start_time', 'end_time']

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if date and date < datetime.date.today():
            raise forms.ValidationError('Slot date cannot be in the past.')

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError('End time must be after start time.')

        return cleaned_data
