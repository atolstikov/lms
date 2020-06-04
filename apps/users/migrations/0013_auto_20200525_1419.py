# Generated by Django 2.2.10 on 2020-05-25 14:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_auto_20200525_1032'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='enrollmentcertificate',
            options={'verbose_name': 'Student Reference', 'verbose_name_plural': 'Student References'},
        ),
        migrations.AddField(
            model_name='enrollmentcertificate',
            name='student_profile',
            field=models.ForeignKey(default=6230, on_delete=django.db.models.deletion.CASCADE, related_name='certificates_of_participation', to='users.StudentProfile', verbose_name='Student'),
            preserve_default=False,
        ),
    ]