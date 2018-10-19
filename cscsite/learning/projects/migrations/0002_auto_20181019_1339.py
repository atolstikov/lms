# Generated by Django 2.1.1 on 2018-10-19 13:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('learning', '0002_auto_20181019_1339'),
        ('core', '0002_auto_20180730_1437'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='reviewer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Project reviewer'),
        ),
        migrations.AddField(
            model_name='reportcomment',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Author'),
        ),
        migrations.AddField(
            model_name='reportcomment',
            name='report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='projects.Report'),
        ),
        migrations.AddField(
            model_name='report',
            name='project_student',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='projects.ProjectStudent'),
        ),
        migrations.AddField(
            model_name='projectstudent',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.Project'),
        ),
        migrations.AddField(
            model_name='projectstudent',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='project',
            name='city',
            field=models.ForeignKey(default='spb', on_delete=django.db.models.deletion.CASCADE, to='core.City', verbose_name='City'),
        ),
        migrations.AddField(
            model_name='project',
            name='reviewers',
            field=models.ManyToManyField(blank=True, limit_choices_to=models.Q(('groups', 9), ('is_superuser', True), _connector='OR'), related_name='project_reviewers', to=settings.AUTH_USER_MODEL, verbose_name='Reviewers'),
        ),
        migrations.AddField(
            model_name='project',
            name='semester',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='learning.Semester', verbose_name='Semester'),
        ),
        migrations.AddField(
            model_name='project',
            name='students',
            field=models.ManyToManyField(through='projects.ProjectStudent', to=settings.AUTH_USER_MODEL, verbose_name='Students'),
        ),
        migrations.AlterUniqueTogether(
            name='review',
            unique_together={('report', 'reviewer')},
        ),
        migrations.AlterUniqueTogether(
            name='projectstudent',
            unique_together={('student', 'project')},
        ),
    ]
