# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-03-15 12:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0050_auto_20170303_1500'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicant',
            name='course',
            field=models.CharField(choices=[('1', '1 course bachelor, speciality'), ('2', '2 course bachelor, speciality'), ('3', '3 course bachelor, speciality'), ('4', '4 course bachelor, speciality'), ('5', 'last course speciality'), ('6', '1 course magistracy'), ('7', '2 course magistracy'), ('8', 'postgraduate'), ('9', 'graduate')], help_text='Applicant|course', max_length=355, verbose_name='Course'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='city',
            field=models.ForeignKey(default='spb', on_delete=django.db.models.deletion.CASCADE, to='core.City', verbose_name='City'),
        ),
    ]
