# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand, CommandError
from post_office import mail
from post_office.models import EmailTemplate, Email
from post_office.utils import get_email_template

from learning.admission.management.commands._utils import CurrentCampaignsMixin, \
    ValidateTemplatesMixin
from learning.admission.models import Campaign, Applicant


class Command(ValidateTemplatesMixin, CurrentCampaignsMixin, BaseCommand):
    TEMPLATE_REGEXP = "admission-{year}-{city_code}-interview-{type}"
    help = """
    For selected campaign generate emails about admission results
    based on interview results.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--city', type=str,
            help='City code to restrict current campaigns')
        parser.add_argument(
            '--from', type=str,
            default='CS центр <info@compscicenter.ru>',
            help='Override default `From` header')

    def handle(self, *args, **options):
        city_code = options["city"]
        campaigns = self.get_current_campaigns(city_code)
        if input(self.CURRENT_CAMPAIGNS_AGREE) != "y":
            self.stdout.write("Canceled")
            return

        self.validate_templates(campaigns, types=Applicant.FINAL_STATUSES)

        header_from = options["from"]

        for campaign in campaigns:
            self.stdout.write("{}:".format(campaign))
            context = {
                'SUBJECT_CITY': campaign.city.name
            }
            # Generate emails for each status
            for status in Applicant.FINAL_STATUSES:
                template_name = self.get_template_name(campaign, status)
                template = get_email_template(template_name)
                applicants = Applicant.objects.filter(campaign_id=campaign.pk,
                                                      status=status)
                generated = 0
                for a in applicants.iterator():
                    if a.status in Applicant.FINAL_STATUSES:
                        recipients = [a.email]
                        # Note: This check doesn't work with
                        # `render_on_delivery=False`
                        if not Email.objects.filter(to=recipients,
                                                    template=template).exists():
                            mail.send(
                                recipients,
                                sender=header_from,
                                template=template,
                                context=context,
                                render_on_delivery=True,
                                backend='ses',
                            )
                            generated += 1
                self.stdout.write(f"Status: {status}. Generated: {generated}")



