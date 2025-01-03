from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.auth import get_user_model
import os
import datetime
# from storages.backends.s3boto3 import S3Boto3Storage
from django.core.files.base import ContentFile

class User(AbstractUser):
    is_lvl4 = models.BooleanField(default=False)
    is_lvl3 = models.BooleanField(default=False)
    is_lvl2 = models.BooleanField(default=False)
    is_lvl1 = models.BooleanField(default=False)

    def __str__(self):
        displayed_name = self.username if len(self.first_name) == 0 or len(self.last_name) == 0 else (self.first_name + ' ' + self.last_name)
        return displayed_name


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name="userprofile", on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

class UserRelation(models.Model):
    user = models.ForeignKey(User, related_name='user_name', on_delete=models.CASCADE)
    supervisor = models.ForeignKey(User, related_name='supervisor', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.username} supervised by {self.supervisor.username}'

class Lead(models.Model):
    STATUS_CHOICES  = [
        ('进行中', '进行中'),
        ('已完成', '已完成'),
        ('待跟进', '待跟进'),
        ('待递交', '待递交'),
        ('取消', '取消'),
    ]

    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20,null=True, blank=True,)
    agent = models.ForeignKey(User, null=True, blank=True, related_name='agent_leads' ,on_delete=models.SET_NULL, default=None)
    manager = models.ForeignKey(User, null=True, blank=True, related_name='manager_leads', on_delete=models.SET_NULL, default=None)
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    quote = models.IntegerField(default=0)
    commission = models.IntegerField(default=0)
    co_commission = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES , null=True, blank=True)
    description = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class CaseField(models.Model):
    FIELD_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
    ]
    name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'user'], name='unique_casefield_per_user')
        ]

    def __str__(self):
        return self.name

class CaseValue(models.Model):
    lead = models.ForeignKey(Lead, related_name="extrafields", on_delete=models.CASCADE)
    field = models.ForeignKey(CaseField, on_delete=models.CASCADE)
    value_text = models.CharField(max_length=255, blank=True, null=True)
    value_number = models.IntegerField(default=0, blank=True, null=True)
    value_date = models.DateField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Ensure that only the appropriate value field is set
        if self.field.field_type == 'text':
            self.value_number = None
            self.value_date = None
        elif self.field.field_type == 'number':
            self.value_text = None
            self.value_date = None
        elif self.field.field_type == 'date':
            self.value_text = None
            self.value_number = None
        super().save(*args, **kwargs)

# TO BE UPDATED
def handle_upload_follow_ups(instance, filename):
    directory = f"lead_followups/lead_{instance.lead.pk}/"
    full_directory = os.path.join(settings.MEDIA_ROOT, directory)

    if not os.path.exists(full_directory):
        os.makedirs(full_directory)

    name, ext = os.path.splitext(filename)
    
    target_file = os.path.join(full_directory, filename)
    
    if os.path.exists(target_file):
        count = 1
        while os.path.exists(target_file):
            modified_filename = f"{name}_{count}{ext}"
            target_file = os.path.join(full_directory, modified_filename)
            count += 1
    result = os.path.join(directory, os.path.basename(target_file))
    return result

class FollowUp(models.Model):
    lead = models.ForeignKey(Lead, related_name="followups", on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    file = models.FileField(null=True, blank=True, upload_to=handle_upload_follow_ups)

    def __str__(self):
        return f"{self.lead.first_name} {self.lead.last_name}"
    
class Folder(models.Model):
    
    name = models.CharField(max_length=255)
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='subfolders', null=True, blank=True)

    def __str__(self):
        return self.name
    
def handle_upload_custom_files(instance, filename):
    directory = ""
    if instance.folder:
        directory = f"documents/{instance.organisation}/folder_{instance.folder.pk}/"
    else:
        directory = f"documents/{instance.organisation}/folder_root/"

    full_directory = os.path.join(settings.MEDIA_ROOT, directory)

    if not os.path.exists(full_directory):
        os.makedirs(full_directory)

    name, ext = os.path.splitext(filename)
    
    target_file = os.path.join(full_directory, filename)
    
    if os.path.exists(target_file):
        count = 1
        while os.path.exists(target_file):
            modified_filename = f"{name}_{count}{ext}"
            target_file = os.path.join(full_directory, modified_filename)
            count += 1
    result = os.path.join(directory, os.path.basename(target_file))
    return result
    
class FolderDocument(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='contents', blank=True, null=True)
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    file = models.FileField(upload_to=handle_upload_custom_files, blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title if self.title else "NoName"

# Team leader on delete -> ?
# Assuming each leader has one team
# Member of one team cannot be in another team
# Default if not providing a teamleader is set to a lvl4 user
def get_default_team_leader():
    User = get_user_model()
    lvl4_user = User.objects.filter(is_lvl4=True).first()
    return lvl4_user.id if lvl4_user else 1

class Team(models.Model):
    name = models.CharField(max_length=255, default="team1")
    team_leader = models.ForeignKey(User, related_name='team_leader', on_delete=models.CASCADE, default=get_default_team_leader)
    date_added = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'team_leader'], name='unique_team_name_per_leader')
        ]

    def __str__(self):
        return self.name if self.name else "NoName"

class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure that a user can only be a member of a team once
        constraints = [
            models.UniqueConstraint(fields=['team', 'member'], name='unique_team_member')
        ]

    def __str__(self):
        return self.member.username if self.member else "NoName"

def handle_upload_work_report(instance, filename):
    directory = f"workreports/{instance.organisation}/"

    full_directory = os.path.join(settings.MEDIA_ROOT, directory)

    if not os.path.exists(full_directory):
        os.makedirs(full_directory)

    name, ext = os.path.splitext(filename)
    
    target_file = os.path.join(full_directory, filename)
    
    if os.path.exists(target_file):
        count = 1
        while os.path.exists(target_file):
            modified_filename = f"{name}_{count}{ext}"
            target_file = os.path.join(full_directory, modified_filename)
            count += 1
    result = os.path.join(directory, os.path.basename(target_file))
    return result
    
class WorkReport(models.Model):
    title = models.CharField(max_length=500, default="work_report")
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    file = models.FileField(upload_to=handle_upload_work_report, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return self.title if self.title else "NoName"