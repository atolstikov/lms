# Generated by Django 2.1.1 on 2018-11-01 10:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0013_auto_20181101_0904'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='assignment',
            options={'ordering': ['created', 'course'], 'verbose_name': 'Assignment', 'verbose_name_plural': 'Assignments'},
        ),
        migrations.RenameField(
            model_name='assignment',
            old_name='course_offering',
            new_name='course',
        ),
    ]