# Generated by Django 2.1.1 on 2018-10-31 12:08

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('learning', '0007_auto_20181031_1155'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CourseOfferingNews',
            new_name='CourseNews',
        ),
    ]