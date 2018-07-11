# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-07-05 15:21
from __future__ import unicode_literals

from django.db import migrations


def forward(apps, schema_editor):
    InterviewInvitation = apps.get_model("admission", "InterviewInvitation")
    for invitation in InterviewInvitation.objects.all():
        invitation.streams.add(invitation.stream)


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0032_auto_20180705_1520'),
    ]

    operations = [
        migrations.RunPython(forward)
    ]