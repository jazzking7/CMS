from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from leads.models import UserProfile

User = get_user_model()


class AgentModelForm(forms.ModelForm):
    LEVEL_CHOICES = (
        ('lvl1', 'Level 1 (Agent)'),
        ('lvl2', 'Level 2 (Manager)'),
    )
    user_level = forms.ChoiceField(choices=LEVEL_CHOICES, widget=forms.RadioSelect)
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        self.is_updating = kwargs.pop('is_updating', False)
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'user_level')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not self.is_updating and User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not self.is_updating and User.objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username
    
class UpdateAgentForm(forms.ModelForm):
    LEVEL_CHOICES = (
        ('lvl1', 'Level 1 (Agent)'),
        ('lvl2', 'Level 2 (Manager)'),
    )
    user_level = forms.ChoiceField(choices=LEVEL_CHOICES, widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        self.is_updating = kwargs.pop('is_updating', False)
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ( 'first_name', 'last_name', 'user_level')

class UserModelForm(forms.ModelForm):
    LEVEL_CHOICES = (
        ('lvl1', 'Level 1 (Agent)'),
        ('lvl2', 'Level 2 (Manager)'),
        ('lvl3', 'Level 3 (Supervisor/Organisor)'),
    )
    user_level = forms.ChoiceField(choices=LEVEL_CHOICES, widget=forms.RadioSelect)
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        self.is_updating = kwargs.pop('is_updating', False)
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'user_level')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username
    
class UpdateUserForm(forms.ModelForm):
    LEVEL_CHOICES = (
        ('lvl1', 'Level 1 (Agent)'),
        ('lvl2', 'Level 2 (Manager)'),
        ('lvl3', 'Level 3 (Supervisor)'),
    )
    user_level = forms.ChoiceField(choices=LEVEL_CHOICES, widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        self.curr_lvl = kwargs.pop('lvl')
        current_supervisor = kwargs.pop('curr_sup')
        super().__init__(*args, **kwargs)

        if self.curr_lvl in ['lvl1', 'lvl2']:
            self.fields['organisor'] = forms.ModelChoiceField(
                queryset=UserProfile.objects.filter(user__is_lvl3=True),
                required=True,
                label="Supervisor"
            )
            if current_supervisor:
                self.fields['organisor'].initial = current_supervisor

    class Meta:
        model = User
        fields = ( 'first_name', 'last_name', 'user_level')