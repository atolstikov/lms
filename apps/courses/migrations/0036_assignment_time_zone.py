# Generated by Django 3.1.7 on 2021-04-13 13:33

import core.db.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0035_auto_20210227_1158'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='time_zone',
            field=core.db.fields.TimeZoneField(verbose_name='Time Zone', null=True),
        ),
    ]