# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import optparse

from django.utils import timezone
from django.core.management.base import LabelCommand

from ...models import Snippet

class Command(LabelCommand):
    option_list = LabelCommand.option_list + (
        optparse.make_option('--dry-run', '-d', action='store_true', dest='dry_run',
            help='Don\'t do anything.'),
    )
    help = "Purges snippets that are expired"

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
