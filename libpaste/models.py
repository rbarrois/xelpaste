# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from random import SystemRandom

from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

import mptt

from .conf import settings
from .highlight import LEXER_DEFAULT

R = SystemRandom()

def generate_secret_id(length=settings.LIBPASTE_SLUG_LENGTH, alphabet=settings.LIBPASTE_SLUG_CHOICES):
    return ''.join([R.choice(alphabet) for i in range(length)])


class Snippet(models.Model):
    EXPIRE_TIME = 1
    EXPIRE_KEEP = 2
    EXPIRE_ONETIME = 3
    EXPIRE_CHOICES = (
        (EXPIRE_TIME, _(u'Expire by timestamp')),
        (EXPIRE_KEEP, _(u'Keep Forever')),
        (EXPIRE_ONETIME, _(u'One time snippet')),
    )

    secret_id = models.CharField(_(u'Secret ID'), max_length=255, blank=True, null=True)
    author = models.CharField(_(u"Author"), max_length=255, blank=True, null=True, default='')
    content = models.TextField(_(u'Content'))
    lexer = models.CharField(_(u'Lexer'), max_length=30, default=LEXER_DEFAULT)
    published = models.DateTimeField(_(u'Published'), auto_now_add=True)
    expire_type = models.PositiveSmallIntegerField(_(u'Expire Type'),
        choices=EXPIRE_CHOICES, default=EXPIRE_CHOICES[0][0])
    expires = models.DateTimeField(_(u'Expires'), blank=True, null=True)
    view_count = models.PositiveIntegerField(_('View count'), default=0)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    file = models.FileField(
        _(u"File"), upload_to=settings.LIBPASTE_UPLOAD_TO, max_length=255, null=True, blank=True)
    content_type = models.CharField(_(u"Content type"), max_length=255, blank=True, null=True)

    class Meta:
        ordering = ('-published',)
        db_table = 'xelpaste_snippet'

    def get_linecount(self):
        return len(self.content.splitlines())

    @property
    def remaining_views(self):
        if self.expire_type == self.EXPIRE_ONETIME:
            remaining = settings.LIBPASTE_ONETIME_LIMIT - self.view_count
            return remaining > 0 and remaining or 0
        return None

    @property
    def is_single(self):
        return self.is_root_node() and not self.get_children()

    @property
    def is_image(self):
        return self.content_type.startswith("image/") if self.content_type else False

    def save(self, *args, **kwargs):
        if not self.secret_id:
            self.secret_id = generate_secret_id()
        super(Snippet, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('snippet_details', kwargs={'snippet_id': self.secret_id})

    def __unicode__(self):
        return self.secret_id

mptt.register(Snippet, order_insertion_by=['content'])
