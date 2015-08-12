# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.template import Library
from libpaste.highlight import pygmentize

register = Library()

@register.filter
def in_list(value, arg):
    return value in arg

@register.filter
def highlight(snippet):
    h = pygmentize(snippet.content, snippet.lexer)
    h = h.replace(u'  ', u' &nbsp;')
    h = h.replace(u'\t', ' &nbsp; &nbsp;')
    return h.splitlines()
