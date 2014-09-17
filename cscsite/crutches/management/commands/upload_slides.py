from __future__ import print_function

from django.core.management import BaseCommand

from learning.models import Semester


class Command(BaseCommand):
    help = "Uploads slides to SlideShare and Yandex.Disk"

    def handle(self, *args, **options):
        current_semester = Semester.objects.first()
        for course_offering in current_semester.courseoffering_set.all():
            course_classes = course_offering.courseclass_set \
                .exclude(slides="").filter(other_materials="")

            for course_class in course_classes:
                print(course_offering, course_class, sep=":")
                course_class.upload_slides()


