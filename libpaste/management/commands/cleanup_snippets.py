# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import argparse

from django.utils import timezone
from django.core.management.base import BaseCommand

from ...models import Snippet

class Command(BaseCommand):
    help = "Purges snippets that are expired"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', '-n',
            action='store_true',
            dest='dry_run',
            help="Don't do anything",
        )

    def handle(self, *args, **options):
        deleteable_snippets = Snippet.objects.filter(
            expires__isnull=False,
            expire_type=Snippet.EXPIRE_TIME,
            expires__lte=timezone.now()
        )
        self.stdout.write(u"%s snippets gets deleted:\n" % deleteable_snippets.count())
        for d in deleteable_snippets:
            self.stdout.write(u"- %s (%s)\n" % (d.secret_id, d.expires))
        if options.get('dry_run'):
            self.stdout.write(u'Dry run - Not actually deleting snippets!\n')
        else:
            deleteable_snippets.delete()
