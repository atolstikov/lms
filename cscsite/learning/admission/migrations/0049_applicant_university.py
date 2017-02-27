# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-02-27 14:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_university'),
        ('admission', '0048_applicant_university_other'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicant',
            name='university',
            field=models.ForeignKey(default=10, on_delete=django.db.models.deletion.PROTECT, related_name='applicants', to='core.University', verbose_name='Applicant|University'),
            preserve_default=False,
        ),
    ]
