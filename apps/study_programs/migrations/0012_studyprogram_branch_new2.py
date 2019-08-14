# Generated by Django 2.2.4 on 2019-08-14 09:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_branch'),
        ('study_programs', '0011_auto_20190813_1738'),
        ('learning', '0025_auto_20190813_1742'),
    ]

    operations = [
        migrations.AddField(
            model_name='studyprogram',
            name='branch_new2',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='study_programs_new', to='core.Branch', verbose_name='Branch'),
            preserve_default=False,
        ),
    ]
