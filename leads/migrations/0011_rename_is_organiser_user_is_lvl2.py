# Generated by Django 4.2.11 on 2024-05-24 15:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0010_rename_is_agent_user_is_lvl1'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='is_organiser',
            new_name='is_lvl2',
        ),
    ]
