# Generated by Django 4.2.11 on 2024-05-22 20:54

from django.db import migrations, models
import django.db.models.deletion
import leads.models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0008_lead_date_added_lead_description_lead_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='converted_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='profile_pictures/'),
        ),
        migrations.CreateModel(
            name='FollowUp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('file', models.FileField(blank=True, null=True, upload_to=leads.models.handle_upload_follow_ups)),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followups', to='leads.lead')),
            ],
        ),
    ]
