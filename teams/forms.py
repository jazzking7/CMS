from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from leads.models import ( Team, TeamMember, UserRelation, User)

User = get_user_model()


class TeamCreateForm(forms.ModelForm):
    team_leader = forms.ModelChoiceField(queryset=User.objects.none(), required=False)

    class Meta:
        model = Team
        fields = ('name', 'team_leader')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        print(user)
        super(TeamCreateForm, self).__init__(*args, **kwargs)

        if user.is_lvl2:
            # Level 2 users should be set as the team leader automatically
            self.fields['team_leader'].queryset = User.objects.filter(id=user.id)
            self.fields['team_leader'].initial = user
            self.fields['team_leader'].widget = forms.HiddenInput()
        elif user.is_lvl3 or user.is_lvl4:
            # Level 3 and Level 4 users should choose from level 2 users they supervise
            supervised_users = User.objects.filter(
                id__in=UserRelation.objects.filter(supervisor=user).values_list('user', flat=True),
                is_lvl2=True  # Ensure only level 2 users are included
            )
            if supervised_users.exists():
                self.fields['team_leader'].queryset = supervised_users
            else:
                # If no level 2 users are under supervision, set the user as the team leader
                self.fields['team_leader'].queryset = User.objects.filter(id=user.id)
                self.fields['team_leader'].initial = user

class TeamUpdateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name']

class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ['member']
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the user from the view's form kwargs
        super(TeamMemberForm, self).__init__(*args, **kwargs)

        # Default queryset, in case user is not provided
        self.fields['member'].queryset = User.objects.none()

        if user:
            if user.is_lvl2:
                # If lvl2, show only lvl1 users who share the same supervisor as the request user
                supervisor = UserRelation.objects.filter(user=user).first()
                if supervisor:
                    self.fields['member'].queryset = User.objects.filter(
                        is_lvl1=True, userrelation__supervisor=supervisor.supervisor
                    )
            elif user.is_lvl3:
                # If lvl3, show all lvl1 users under their management
                lvl1_users = User.objects.filter(
                    is_lvl1=True, userrelation__supervisor__in=UserRelation.objects.filter(supervisor=user)
                )
                self.fields['member'].queryset = lvl1_users
            elif user.is_lvl4:
                # If lvl4, show all lvl1 users
                self.fields['member'].queryset = User.objects.filter(is_lvl1=True)


class UserCreateForm(forms.ModelForm):

    email = forms.EmailField(required=True)

#
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput, required=True)

    def __init__(self, *args, **kwargs):
        self.is_updating = kwargs.pop('is_updating', False)
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name')

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