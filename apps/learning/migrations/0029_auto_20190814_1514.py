# Generated by Django 2.2.4 on 2019-08-14 15:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0028_auto_20190814_0920'),
        ('core', '0011_venue'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='venue',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.Venue', verbose_name='CourseClass|Venue'),
        ),
    ]