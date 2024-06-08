from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from leads.models import (UserProfile, Folder, 
                          FolderDocument
                          )


User = get_user_model()


class FolderCreateForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = (
            'name',
        )

class FolderContentCreateForm(forms.ModelForm):
    class Meta:
        model = FolderDocument
        fields = (
            'title',
            'description',
            'file',
            'url',
        )

class FolderContentUpdateForm(forms.ModelForm):
    class Meta:
        model = FolderDocument
        fields = (
            'title',
            'description',
            'url',
        )