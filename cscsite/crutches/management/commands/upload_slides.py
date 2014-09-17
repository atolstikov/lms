import posixpath

from django.core.management import BaseCommand

from learning.models import Semester
from learning.slides import upload_to_slideshare, upload_to_yandex


class Command(BaseCommand):
    help = "Uploads slides to SlideShare and Yandex.Disk"

    def handle(self, *args, **options):
        current_semester = Semester.objects.first()
        for course_offering in current_semester.courseoffering_set.all():
            course_classes = course_offering.course_class_set \
                .exclude(slides="").filter(other_matrial="")

            for course_class in course_classes:
                print(course_class)
                course_class.upload_slides()


