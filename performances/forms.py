from django import forms
from django.conf import settings
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UsernameField
from leads.models import Lead, FollowUp, CaseField, CaseValue, handle_upload_follow_ups, UserRelation, User