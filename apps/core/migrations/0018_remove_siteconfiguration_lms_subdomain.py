# Generated by Django 3.2.12 on 2022-02-11 12:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20220209_1614'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='siteconfiguration',
            name='lms_subdomain',
        ),
    ]
