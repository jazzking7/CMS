from django import forms
from django.conf import settings
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UsernameField
from .models import Lead, FollowUp, CaseField, CaseValue, handle_upload_follow_ups, UserRelation, User
import os

User = get_user_model()


class LeadModelForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = (
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'description',
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        instance = kwargs.get('instance') 
        super(LeadModelForm, self).__init__(*args, **kwargs)
        
        up = None

        if self.user.is_lvl3:
            up = self.user.userprofile
        elif self.user.is_lvl2:
            sr = UserRelation.objects.get(user=self.user)
            up = sr.supervisor.userprofile
        elif self.user.is_lvl1:
            sr = UserRelation.objects.get(user=self.user)
            up = sr.supervisor.userprofile

        additional_fields = CaseField.objects.filter(user=up)
        for field in additional_fields:
            if field.field_type == 'text':
                self.fields[field.name] = forms.CharField(label=field.name, required=False)
            elif field.field_type == 'number':
                self.fields[field.name] = forms.IntegerField(label=field.name, required=False)
            elif field.field_type == 'date':
                self.fields[field.name] = forms.DateField(label=field.name, required=False)
            # Add more field types as needed
        
        if instance:
            for case_value in instance.extrafields.all():
                if case_value.field.field_type == 'text':
                    self.initial[case_value.field.name] = case_value.value_text
                elif case_value.field.field_type == 'number':
                    self.initial[case_value.field.name] = case_value.value_number
                elif case_value.field.field_type == 'date':
                    self.initial[case_value.field.name] = case_value.value_date

    def save(self, commit=True):
        Lead = super(LeadModelForm, self).save(commit=False)
        if commit:
            up = None

            if self.user.is_lvl3:
                up = self.user.userprofile
            elif self.user.is_lvl2:
                sr = UserRelation.objects.get(user=self.user)
                up = sr.supervisor.userprofile
            elif self.user.is_lvl1:
                sr = UserRelation.objects.get(user=self.user)
                up = sr.supervisor.userprofile


            for field in CaseField.objects.filter(user=up):
                field_name = field.name
                value = self.cleaned_data[field_name]
                case_value, created = CaseValue.objects.get_or_create(lead=Lead, field=field)
                if field.field_type == 'text':
                    case_value.value_text = value
                elif field.field_type == 'number':
                    case_value.value_number = value
                elif field.field_type == 'date':
                    case_value.value_date = value
                case_value.save()
        return Lead


class LeadUpdateForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = (
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'description',
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.instance = kwargs.get('instance', None)
        instance = kwargs.get('instance')
        org = instance.organisation if instance else None
        super(LeadUpdateForm, self).__init__(*args, **kwargs)

        CHOICES = [
            ('进行中', '进行中'),
            ('已完成', '已完成'),
            ('待跟进', '待跟进'),
            ('待递交', '待递交'),
            ('取消', '取消'),
        ]
        
        if self.user.is_lvl3 or self.user.is_lvl4:

            # Add quote and commission fields for lvl3 users
            self.fields['quote'] = forms.IntegerField(label='Quote', required=True, initial=instance.quote if instance else None)
            self.fields['commission'] = forms.IntegerField(label='Commission', required=True, initial=instance.commission if instance else None)

            user_set = User.objects.filter(
                Q(is_lvl3=True, userprofile=org) |
                Q(Q(is_lvl1=True) | Q(is_lvl2=True), user_name__supervisor__userprofile=org)
            )

            self.fields['agent'] = forms.ModelChoiceField(queryset=user_set, initial=instance.agent, required=False)
            self.fields['manager'] = forms.ModelChoiceField(queryset=user_set, initial=instance.manager, required=False)
   
        self.fields['status'] = forms.ChoiceField(
                choices=Lead.STATUS_CHOICES,
                label='Status',
                required=False,
                initial=instance.status
            )

        additional_fields = CaseField.objects.filter(user=org)
        for field in additional_fields:
            if field.field_type == 'text':
                self.fields[field.name] = forms.CharField(label=field.name, required=False)
            elif field.field_type == 'number':
                self.fields[field.name] = forms.IntegerField(label=field.name, required=False)
            elif field.field_type == 'date':
                self.fields[field.name] = forms.DateField(label=field.name, required=False)
            # Add more field types as needed
        
        if instance:
            for case_value in instance.extrafields.all():
                if case_value.field.field_type == 'text':
                    self.initial[case_value.field.name] = case_value.value_text
                elif case_value.field.field_type == 'number':
                    self.initial[case_value.field.name] = case_value.value_number
                elif case_value.field.field_type == 'date':
                    self.initial[case_value.field.name] = case_value.value_date

    def save(self, commit=True):
        Lead = super(LeadUpdateForm, self).save(commit=True)
        if commit:

            nonp = []
            for field in CaseField.objects.filter(user=self.instance.organisation):
                field_name = field.name
                nonp.append(field_name)
                value = self.cleaned_data[field_name]
                case_value, created = CaseValue.objects.get_or_create(lead=Lead, field=field) # !
                if field.field_type == 'text':
                    case_value.value_text = value
                elif field.field_type == 'number':
                    case_value.value_number = value
                elif field.field_type == 'date':
                    case_value.value_date = value
                case_value.save()

            for field_name in [f.name for f in Lead._meta.get_fields() if f.name not in nonp]:
                if field_name in self.cleaned_data:  # Check if the field is present in the cleaned data
                    setattr(Lead, field_name, self.cleaned_data[field_name])
            
        return Lead

class FollowUpModelForm(forms.ModelForm):

    file = forms.FileField(widget = forms.TextInput(attrs={
        "name": "files",
        "type": "File",
        "class": "form-control",
        "multiple": "True",
    }), required=False)
    class Meta:
        model = FollowUp
        fields = (
            'notes',
            'file'
        )

    def save(self, commit=True, files=None, suppressed=True):
        if suppressed:
            return None

        instance = super().save(commit=False)

        if files:
            return None

        if commit:
            instance.save()
        return instance

class FollowUpUpdateModelForm(forms.ModelForm):
    class Meta:
        model = FollowUp
        fields = (
            'notes',
        )

class LeadForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    age = forms.IntegerField(min_value=0)