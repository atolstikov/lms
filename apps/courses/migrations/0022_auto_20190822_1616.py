# Generated by Django 2.2.4 on 2019-08-22 16:16

from django.db import migrations


def set_new_venue(apps, schema_editor):
    CourseClass = apps.get_model('courses', 'CourseClass')
    LearningSpace = apps.get_model('courses', 'LearningSpace')
    for cc in CourseClass.objects.select_related("course"):
        cc.venue_new = LearningSpace.objects.get(location_id=cc.venue_id,
                                                 branch_id=cc.course.branch_id)
        cc.save(update_fields=['venue_new'])


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0021_courseclass_venue_new'),
    ]

    operations = [
        migrations.RunPython(set_new_venue)
    ]