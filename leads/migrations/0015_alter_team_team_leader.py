# Generated by Django 4.2.11 on 2024-08-24 22:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import leads.models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0014_team_teammember_team_unique_team_name_per_leader'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='team_leader',
            field=models.ForeignKey(default=leads.models.get_default_team_leader, on_delete=django.db.models.deletion.CASCADE, related_name='team_leader', to=settings.AUTH_USER_MODEL),
        ),
    ]