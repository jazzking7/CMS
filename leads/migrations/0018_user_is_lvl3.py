# Generated by Django 4.2.11 on 2024-05-26 02:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0017_alter_lead_agent'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_lvl3',
            field=models.BooleanField(default=True),
        ),
    ]