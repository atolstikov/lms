# Generated by Django 2.2.10 on 2020-02-07 13:40

import core.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20200207_1340'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='branch',
            managers=[
                ('objects', core.models.BranchManager()),
            ],
        ),
    ]