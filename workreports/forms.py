from django import forms
from django.conf import settings
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UsernameField
from leads.models import WorkReport

User = get_user_model()

class WorkReportForm(forms.ModelForm):
    class Meta:
        model = WorkReport
        fields = (
            'title',
            'file',
        )
        
class WorkReportUpdateForm(forms.ModelForm):
    class Meta:
        model = WorkReport
        fields = (
            'title',
        )