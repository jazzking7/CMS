# Generated by Django 4.2.11 on 2024-05-27 15:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0024_alter_lead_agent_alter_user_is_lvl2_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agent',
            name='user',
            field=models.OneToOneField(limit_choices_to={'is_lvl1': True}, on_delete=django.db.models.deletion.CASCADE, related_name='agent', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='manager',
            name='user',
            field=models.OneToOneField(limit_choices_to={'is_lvl2': True}, on_delete=django.db.models.deletion.CASCADE, related_name='manager', to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='Supervisor',
        ),
    ]