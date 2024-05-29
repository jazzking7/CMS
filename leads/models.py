from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import os


class User(AbstractUser):
    is_lvl4 = models.BooleanField(default=False)
    is_lvl3 = models.BooleanField(default=False)
    is_lvl2 = models.BooleanField(default=False)
    is_lvl1 = models.BooleanField(default=False)


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name="userprofile", on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

class Lead(models.Model):
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    agent = models.ForeignKey("Agent", null=True, blank=True, on_delete=models.SET_NULL)
    manager = models.ForeignKey("Manager", null=True, blank=True, on_delete=models.SET_NULL)
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    quote = models.IntegerField(default=0)
    commission = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
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

    return os.path.join(directory, os.path.basename(target_file))

class FollowUp(models.Model):
    lead = models.ForeignKey(Lead, related_name="followups", on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    file = models.FileField(null=True, blank=True, upload_to=handle_upload_follow_ups)

    def __str__(self):
        return f"{self.lead.first_name} {self.lead.last_name}"


class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent', limit_choices_to={'is_lvl1': True})
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.email

class Manager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='manager', limit_choices_to={'is_lvl2': True})
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.email

# def post_user_created_signal(sender, instance, created, **kwargs):
#     if created:
#         UserProfile.objects.create(user=instance)


# post_save.connect(post_user_created_signal, sender=User)