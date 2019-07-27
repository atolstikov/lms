# Generated by Django 2.2.3 on 2019-07-27 17:40

from django.db import migrations

def copy_branch(apps, schema_editor):
    Campaign = apps.get_model('admission', 'Campaign')
    for sp in Campaign.objects.select_related('branch'):
        sp.branch_new_id = sp.branch.code
        sp.save(update_fields=['branch_new_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0017_auto_20190727_1740'),
    ]

    operations = [
        migrations.RunPython(copy_branch)
    ]
