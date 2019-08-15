# Generated by Django 2.2.4 on 2019-08-14 09:22

from django.db import migrations


def copy_branch(apps, schema_editor):
    M = apps.get_model('library', 'Stock')
    for o in M.objects.select_related('branch'):
        if o.branch_id:
            o.branch_new2_id = o.branch.id
            o.save(update_fields=["branch_new2_id"])


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0007_stock_branch_new2'),
    ]

    operations = [
        migrations.RunPython(copy_branch)
    ]