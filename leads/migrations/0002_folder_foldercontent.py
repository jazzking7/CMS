# Generated by Django 4.2.11 on 2024-06-08 03:10

from django.db import migrations, models
import django.db.models.deletion
import leads.models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Folder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('organisation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='leads.userprofile')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subfolders', to='leads.folder')),
            ],
        ),
        migrations.CreateModel(
            name='FolderContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('file', models.FileField(blank=True, null=True, upload_to=leads.models.handle_upload_custom_files)),
                ('url', models.URLField(blank=True, null=True)),
                ('folder', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='contents', to='leads.folder')),
                ('organisation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='leads.userprofile')),
            ],
        ),
    ]