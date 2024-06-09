from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from leads.models import (UserProfile, Folder, 
                          FolderDocument)

User = get_user_model()


class FolderCreateForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = (
            'name',
        )

class FolderContentCreateForm(forms.ModelForm):
    file = forms.FileField(widget = forms.TextInput(attrs={
            "name": "files",
            "type": "File",
            "class": "form-control",
            "multiple": "True",
        }), required=False)
    class Meta:
        model = FolderDocument
        fields = (
            'title',
            'description',
            'file',
            'url',
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

class FolderContentUpdateForm(forms.ModelForm):
    class Meta:
        model = FolderDocument
        fields = (
            'title',
            'description',
            'url',
        )