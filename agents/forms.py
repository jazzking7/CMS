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

#
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput, required=True)

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
#
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if not self.is_updating:
            if not password1:
                raise ValidationError("Password is required.")
            if password1 != password2:
                raise ValidationError("Passwords do not match.")
        elif password1 or password2:
            if password1 != password2:
                raise ValidationError("Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password1 = self.cleaned_data.get('password1')
        if password1:
            user.set_password(password1)
        if commit:
            user.save()
        return user
    
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

    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput, required=True)

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
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        email = cleaned_data.get('email')
        username = cleaned_data.get('username')

        if not self.is_updating:
            if not password1:
                raise ValidationError("Password is required.")
            if password1 != password2:
                raise ValidationError("Passwords do not match.")
        elif password1 or password2:
            if password1 != password2:
                raise ValidationError("Passwords do not match.")
            
                # Check email and username fields
        if not self.is_updating:
            if email and User.objects.filter(email=email).exists():
                raise ValidationError("A user with this email already exists.")
            if username and User.objects.filter(username=username).exists():
                raise ValidationError("A user with this username already exists.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password1 = self.cleaned_data.get('password1')
        if password1:
            user.set_password(password1)
        if commit:
            user.save()
        return user
    
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
                queryset=User.objects.filter(is_lvl3=True),
                required=True,
                label="Supervisor"
            )
            if current_supervisor:
                self.fields['organisor'].initial = current_supervisor

    class Meta:
        model = User
        fields = ( 'first_name', 'last_name', 'user_level')