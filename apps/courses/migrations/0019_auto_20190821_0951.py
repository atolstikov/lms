# Generated by Django 2.2.4 on 2019-08-21 09:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0018_auto_20190821_0950'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='course',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='course',
            constraint=models.UniqueConstraint(fields=('meta_course', 'semester', 'branch'), name='unique_course_for_branch_in_a_term'),
        ),
    ]