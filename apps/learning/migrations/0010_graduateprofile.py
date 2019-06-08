# Generated by Django 2.2.1 on 2019-06-04 11:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import learning.models
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('learning', '0009_auto_20190515_1758'),
    ]

    operations = [
        migrations.CreateModel(
            name='GraduateProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('graduation_at', models.DateField(help_text='Graduation ceremony date', verbose_name='Graduation at')),
                ('photo', sorl.thumbnail.fields.ImageField(blank=True, upload_to=learning.models.graduate_photo_upload_to, verbose_name='Photo')),
                ('testimonial', models.TextField(blank=True, help_text='Testimonial about Computer Science Center', verbose_name='Testimonial')),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='graduate_profile', to=settings.AUTH_USER_MODEL, verbose_name='Student')),
            ],
            options={
                'verbose_name': 'Graduate Profile',
                'verbose_name_plural': 'Graduate Profiles',
            },
        ),
    ]