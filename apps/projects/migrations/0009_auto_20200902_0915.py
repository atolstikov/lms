# Generated by Django 3.0.9 on 2020-09-02 09:15

from django.db import migrations, models
import projects.models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0008_auto_20200902_0819'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='presentation',
            field=models.FileField(blank=True, max_length=200, upload_to=projects.models.project_presentations_upload_to, verbose_name='Participants presentation'),
        ),
        migrations.AlterField(
            model_name='project',
            name='supervisor_presentation',
            field=models.FileField(blank=True, max_length=200, upload_to=projects.models.project_presentations_upload_to, verbose_name='Supervisor presentation'),
        ),
    ]