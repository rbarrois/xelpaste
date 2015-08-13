# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from django import forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .conf import settings
from .models import Snippet
from .highlight import LEXER_LIST, LEXER_DEFAULT, LEXER_KEYS



class BaseSnippetForm(forms.ModelForm):
    lexer = forms.ChoiceField(
        label=_(u'Lexer'),
        initial=LEXER_DEFAULT,
        choices=LEXER_LIST,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    expires = forms.ChoiceField(
        label=_(u'Expires'),
        choices=settings.LIBPASTE_EXPIRE_CHOICES,
        initial=settings.LIBPASTE_EXPIRE_DEFAULT,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    author = forms.CharField(
        label=_(u"Author"),
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    not_spam = forms.BooleanField(
        label=_(u"This is *not* spam"),
        initial=False,
        required=False,
    )

    # Honeypot field
    title = forms.CharField(
        label=_(u'Title'),
        required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'class': 'form-control'}),
    )

    class Meta:
        model = Snippet
        exclude = []

    def __init__(self, request, *args, **kwargs):
        super(BaseSnippetForm, self).__init__(*args, **kwargs)
        self.request = request
        self.likely_spam = False

        # Set the recently used lexer if we have any
        session_lexer = self.request.session.get('lexer')
        if session_lexer and session_lexer in LEXER_KEYS:
            self.fields['lexer'].initial = session_lexer

        session_author = self.request.session.get('author')
        if session_author:
            self.fields['author'].initial = session_author

        # if the lexer is given via GET, set it
        if 'l' in request.GET and request.GET['l'] in LEXER_KEYS:
            self.fields['lexer'].initial = request.GET['l']

    def clean(self):
        # The `title` field is a hidden honeypot field. If its filled,
        # this is likely spam.
        if self.cleaned_data.get('title'):
            raise forms.ValidationError('This snippet was identified as Spam.')
        return self.cleaned_data

    def clean_expires(self):
        expires = self.cleaned_data['expires']

        if expires == u'never':
            self.cleaned_data['expire_type'] = Snippet.EXPIRE_KEEP
            return None

        if expires == u'onetime':
            self.cleaned_data['expire_type'] = Snippet.EXPIRE_ONETIME
            return None

        self.cleaned_data['expire_type'] = Snippet.EXPIRE_TIME
        return expires

    def save(self, parent=None, *args, **kwargs):
        # Set parent snippet
        if parent:
            self.instance.parent = parent

        # Add expire datestamp. None indicates 'keep forever', use the default
        # null state of the db column for that.
        self.instance.expire_type = self.cleaned_data['expire_type']

        expires = self.cleaned_data['expires']
        if expires:
            self.instance.expires = timezone.now() + \
                datetime.timedelta(seconds=int(expires))

        # Save snippet in the db
        super(BaseSnippetForm, self).save(*args, **kwargs)

        # Add the snippet to the user session list
        if self.request.session.get('snippet_list', False):
            if len(self.request.session['snippet_list']) >= settings.LIBPASTE_MAX_SNIPPETS_PER_USER:
                self.request.session['snippet_list'].pop(0)
            self.request.session['snippet_list'] += [self.instance.pk]
        else:
            self.request.session['snippet_list'] = [self.instance.pk]

        # Save the lexer in the session so we can use it later again
        self.request.session['lexer'] = self.cleaned_data['lexer']

        if self.cleaned_data['author']:
            self.request.session['author'] = self.cleaned_data['author']

        return self.instance


class SnippetForm(BaseSnippetForm):
    content = forms.CharField(
        label=_('Content'),
        widget=forms.Textarea(attrs={'placeholder': _('Awesome code goes here...'), 'class': 'form-control'}),
        max_length=settings.LIBPASTE_MAX_CONTENT_LENGTH,
    )

    class Meta(BaseSnippetForm.Meta):
        fields = (
            'content',
            'lexer',
            'author',
        )

    def clean_content(self):
        content = self.cleaned_data.get('content', '')
        if content.strip() == '':
            raise forms.ValidationError(_('Please fill out this field.'))
        return content

    def clean(self):
        cleaned_data = super(SnippetForm, self).clean()
        for badword, trigger in settings.LIBPASTE_BADWORD_TRIGGERS.items():
            if self.cleaned_data.get('content', '').count(badword) >= trigger and not self.cleaned_data['not_spam']:
                self.likely_spam = True
                self._errors['content'] = self.error_class([_("This snippet looks like spam.")])
        return cleaned_data


class SnippetUploadForm(BaseSnippetForm):
    file = forms.FileField(
        label=_('File'),
        max_length=settings.LIBPASTE_MAX_FILE_LENGTH,
    )

    class Meta(BaseSnippetForm.Meta):
        fields = (
            'file',
            'author',
        )

    def __init__(self, *args, **kwargs):
        super(SnippetUploadForm, self).__init__(*args, **kwargs)
        self.fields['lexer'].required = False

    def clean_file(self):
        fd = self.cleaned_data.get('file')
        if fd is not None:
            content = fd.read()
            fd.seek(0)
            if content.strip() == '':
                raise forms.ValidationError(_('Please fill out this field.'))
        return fd

    def save(self, parent=None, *args, **kwargs):
        # File descriptor from form contains content type.
        fd = self.cleaned_data['file']

        # Using file upload for copy/pasting a whole file
        if fd.content_type.startswith('text/'):
            self.instance.content = fd.read()
            self.instance.file = None
        else:
            self.instance.content_type = fd.content_type

        return super(SnippetUploadForm, self).save(parent, *args, **kwargs)
