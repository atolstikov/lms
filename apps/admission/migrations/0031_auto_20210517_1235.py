# Generated by Django 3.1.7 on 2021-05-17 12:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("admission", "0030_auto_20210517_0843"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="interview",
            constraint=models.UniqueConstraint(
                fields=("applicant", "section"),
                name="unique_interview_section_per_applicant",
            ),
        ),
    ]
