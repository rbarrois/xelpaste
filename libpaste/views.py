# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
import difflib
import json
import os

import sendfile

from django.shortcuts import render, get_object_or_404
from django.http import (Http404, HttpResponseRedirect, HttpResponseBadRequest,
    HttpResponse)
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.views.defaults import (page_not_found as django_page_not_found,
    server_error as django_server_error)
from django.views.decorators.csrf import csrf_exempt

from .conf import settings
from .forms import SnippetForm, SnippetUploadForm
from .models import Snippet
from .highlight import LEXER_WORDWRAP, LEXER_LIST
from .highlight import LEXER_DEFAULT, LEXER_KEYS

# -----------------------------------------------------------------------------
# Snippet Handling
# -----------------------------------------------------------------------------

def snippet_new(request, template_name='libpaste/snippet_new.html'):
    """
    Create a new snippet.
    """
    if request.method == "POST":
        snippet_form = SnippetForm(data=request.POST, request=request)
        if snippet_form.is_valid():
            new_snippet = snippet_form.save()
            url = new_snippet.get_absolute_url()
            return HttpResponseRedirect(url)
    else:
        snippet_form = SnippetForm(request=request)

    return render(request, template_name, {
        'snippet_form': snippet_form,
        'lexer_list': LEXER_LIST,
        'is_new': True,
        'page': 'snippet_new',
    })


def snippet_upload(request, template_name='libpaste/snippet_upload.html'):
    """
    Upload an existing snippet.
    """
    if request.method == "POST":
        snippet_form = SnippetUploadForm(data=request.POST, files=request.FILES, request=request)
        if snippet_form.is_valid():
            new_snippet = snippet_form.save()
            url = new_snippet.get_absolute_url()
            return HttpResponseRedirect(url)
        else:
            pass
    else:
        snippet_form = SnippetUploadForm(request=request)

    return render(request, template_name, {
        'snippet_form': snippet_form,
        'is_new': True,
        'page': 'snippet_upload',
    })


def snippet_details(request, snippet_id, template_name='libpaste/snippet_details.html', is_raw=False):
    """
    Details list view of a snippet. Handles the actual view, reply and
    tree/diff view.
    """
    snippet = get_object_or_404(Snippet, secret_id=snippet_id)

    # One time snippet get deleted if the view count matches our limit
    if snippet.expire_type == Snippet.EXPIRE_ONETIME \
    and snippet.view_count >= settings.LIBPASTE_ONETIME_LIMIT:
        snippet.delete()
        raise Http404()

    # Increase the view count of the snippet
    snippet.view_count += 1
    snippet.save()

    # When rendering binary snippet, let the front-end server serve the media
    if snippet.file and is_raw:
        return sendfile.sendfile(request, snippet.file.path)

    tree = snippet.get_root()
    tree = tree.get_descendants(include_self=True)

    new_snippet_initial = {
        'content': snippet.content,
        'lexer': snippet.lexer,
    }

    form_class = SnippetForm
    if snippet.file:
        form_class = SnippetUploadForm
    if request.method == "POST":
        snippet_form = form_class(
            data=request.POST,
            files=request.FILES,
            request=request,
            initial=new_snippet_initial)
        if snippet_form.is_valid():
            new_snippet = snippet_form.save(parent=snippet)
            url = new_snippet.get_absolute_url()
            return HttpResponseRedirect(url)
    else:
        snippet_form = form_class(
            initial=new_snippet_initial,
            request=request)

    response = render(request, template_name, {
        'snippet_form': snippet_form,
        'snippet': snippet,
        'lexers': LEXER_LIST,
        'lines': range(snippet.get_linecount()),
        'tree': tree,
        'wordwrap': snippet.lexer in LEXER_WORDWRAP,
        'page': 'snippet_details',
    })

    if is_raw:
        response['Content-Type'] = 'text/plain;charset=UTF-8'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    else:
        return response


def snippet_delete(request, snippet_id=None):
    """
    Delete a snippet. This is allowed by anybody as long as he knows the
    snippet id. I got too many manual requests to do this, mostly for legal
    reasons and the chance to abuse this is not given anyway, since snippets
    always expire.
    """
    snippet_id = snippet_id or request.POST.get('snippet_id')
    if not snippet_id:
        raise Http404('No snippet id given')
    snippet = get_object_or_404(Snippet, secret_id=snippet_id)
    snippet.delete()
    return HttpResponseRedirect(reverse('snippet_new'))


def snippet_history(request, template_name='libpaste/snippet_list.html'):
    """
    Display the last `n` snippets created by this user (and saved in his
    session).
    """
    snippet_list = None
    snippet_id_list = request.session.get('snippet_list', None)
    if snippet_id_list:
        snippet_list = Snippet.objects.filter(pk__in=snippet_id_list)

    if 'delete-all' in request.GET:
        if snippet_list:
            for s in snippet_list:
                s.delete()
        return HttpResponseRedirect(reverse('snippet_history'))

    return render(request, template_name, {
        'snippets_max': settings.LIBPASTE_MAX_SNIPPETS_PER_USER,
        'snippet_list': snippet_list,
        'page': 'snippet_history',
    })


def snippet_diff(request, template_name='libpaste/snippet_diff.html'):
    """
    Display a diff between two given snippet secret ids.
    """
    if request.GET.get('a') and request.GET.get('a').isdigit() \
    and request.GET.get('b') and request.GET.get('b').isdigit():
        try:
            fileA = Snippet.objects.get(pk=int(request.GET.get('a')))
            fileB = Snippet.objects.get(pk=int(request.GET.get('b')))
        except ObjectDoesNotExist:
            return HttpResponseBadRequest(u'Selected file(s) does not exist.')
    else:
        return HttpResponseBadRequest(u'You must select two snippets.')

    class DiffText(object):
        pass

    diff = DiffText()

    if fileA.content != fileB.content:
        d = difflib.unified_diff(
            fileA.content.splitlines(),
            fileB.content.splitlines(),
            'Original',
            'Current',
            lineterm=''
        )

        diff.content = '\n'.join(d).strip()
        diff.lexer = 'diff'
    else:
        diff.content = _(u'No changes were made between this two files.')
        diff.lexer = 'text'

    return render(request, template_name, {
        'snippet': diff,
        'fileA': fileA,
        'fileB': fileB,
        'page': 'snippet_diff',
    })


# -----------------------------------------------------------------------------
# API Handling
# -----------------------------------------------------------------------------

def _format_default(s):
    """The default response is the snippet URL wrapped in quotes."""
    return u'"%s%s"' % (settings.LIBPASTE_BASE_URL.rstrip('/'), s.get_absolute_url())

def _format_url(s):
    """The `url` format returns the snippet URL, no quotes, but a linebreak after."""
    return u'%s%s\n' % (settings.LIBPASTE_BASE_URL.rstrip('/'), s.get_absolute_url())

def _format_json(s):
    """The `json` format export."""
    return json.dumps({
        'url': u'%s%s' % (settings.LIBPASTE_BASE_URL.rstrip('/'), s.get_absolute_url()),
        'content': s.content,
        'lexer': s.lexer,
    })


FORMAT_MAPPING = {
    'default': _format_default,
    'url': _format_url,
    'json': _format_json,
}


def _get_value(request, field, default = ''):
    val = request.POST.get(field) or request.GET.get(field) or default
    return val.strip()


@csrf_exempt
def snippet_api(request):
    content = request.POST.get('content', '').strip()
    lexer = _get_value(request, 'lexer', LEXER_DEFAULT)
    format = _get_value(request, 'format', 'default')
    author = _get_value(request, 'author')

    if not content:
        return HttpResponseBadRequest('No content given')

    if lexer not in LEXER_KEYS:
        return HttpResponseBadRequest('Invalid lexer given. Valid lexers are: %s' %
            ', '.join(LEXER_KEYS))

    s = Snippet.objects.create(
        content=content,
        lexer=lexer,
        expires=timezone.now() + datetime.timedelta(seconds=60*60*24*30),
        author=author,
    )
    s.save()

    if format not in FORMAT_MAPPING:
        response = _format_default(s)
    else:
        response = FORMAT_MAPPING[format](s)

    return HttpResponse(response)


