# Generated by Django 2.2.4 on 2019-08-14 09:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0027_auto_20190814_0919'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invitation',
            name='branch',
        ),
        migrations.RenameField(
            model_name='invitation',
            old_name='branch_new2',
            new_name='branch',
        ),
    ]
