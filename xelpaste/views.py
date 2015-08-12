import datetime
import difflib
import json
import os

import requests
import sendfile

from django.shortcuts import (render_to_response, get_object_or_404)
from django.template.context import RequestContext
from django.http import (Http404, HttpResponseRedirect, HttpResponseBadRequest,
    HttpResponse)
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.views.defaults import (page_not_found as django_page_not_found,
    server_error as django_server_error)
from django.views.decorators.csrf import csrf_exempt

from xelpaste.conf import settings
from xelpaste.forms import SnippetForm, SnippetUploadForm
from xelpaste.models import Snippet
from xelpaste.highlight import LEXER_WORDWRAP, LEXER_LIST
from xelpaste.highlight import LEXER_DEFAULT, LEXER_KEYS

# -----------------------------------------------------------------------------
# Snippet Handling
# -----------------------------------------------------------------------------

def snippet_new(request, template_name='xelpaste/snippet_new.html'):
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

    template_context = {
        'snippet_form': snippet_form,
        'lexer_list': LEXER_LIST,
        'is_new': True,
    }

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )


def snippet_upload(request, template_name='xelpaste/snippet_upload.html'):
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

    template_context = {
        'snippet_form': snippet_form,
        'is_new': True,
    }

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request),
    )


def snippet_details(request, snippet_id, template_name='xelpaste/snippet_details.html', is_raw=False):
    """
    Details list view of a snippet. Handles the actual view, reply and
    tree/diff view.
    """
    snippet = get_object_or_404(Snippet, secret_id=snippet_id)

    # One time snippet get deleted if the view count matches our limit
    if snippet.expire_type == Snippet.EXPIRE_ONETIME \
    and snippet.view_count >= settings.DPASTE_ONETIME_LIMIT:
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

    template_context = {
        'snippet_form': snippet_form,
        'snippet': snippet,
        'lexers': LEXER_LIST,
        'lines': range(snippet.get_linecount()),
        'tree': tree,
        'wordwrap': snippet.lexer in LEXER_WORDWRAP and 'True' or 'False',
    }

    response = render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )

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


def snippet_history(request, template_name='xelpaste/snippet_list.html'):
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

    template_context = {
        'snippets_max': settings.DPASTE_MAX_SNIPPETS_PER_USER,
        'snippet_list': snippet_list,
    }

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )


def snippet_diff(request, template_name='xelpaste/snippet_diff.html'):
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

    template_context = {
        'snippet': diff,
        'fileA': fileA,
        'fileB': fileB,
    }

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )


def snippet_gist(request, snippet_id): # pragma: no cover
    """
    Put a snippet on Github Gist.
    """
    snippet = get_object_or_404(Snippet, secret_id=snippet_id)
    data = {
        'description': 'the description for this gist',
        'public': False,
        'files': {
            '%s_snippet.py' % settings.DPASTE_DOMAIN: {
                'content': snippet.content,
            }
        }
    }

    try:
        payload = json.dumps(data)
        response = requests.post('https://api.github.com/gists', data=payload)
        response_dict = json.loads(response.content)
        gist_url = response_dict.get('html_url')

    # Github could be down, could return invalid JSON, it's rare
    except:
        return HttpResponse('Creating a Github Gist failed. Sorry, please go back and try again.')

    return HttpResponseRedirect(gist_url)


# -----------------------------------------------------------------------------
# Static pages
# -----------------------------------------------------------------------------

def about(request, template_name='xelpaste/about.html'):
    """
    A rather static page, we need a view just to display a couple of
    statistics.
    """
    template_context = {
        'total': Snippet.objects.count(),
        'stats': Snippet.objects.values('lexer').annotate(
            count=Count('lexer')).order_by('-count')[:5],
    }

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )


# -----------------------------------------------------------------------------
# API Handling
# -----------------------------------------------------------------------------

def _format_default(s):
    """The default response is the snippet URL wrapped in quotes."""
    return u'"%s%s"' % (settings.DPASTE_BASE_URL, s.get_absolute_url())

def _format_url(s):
    """The `url` format returns the snippet URL, no quotes, but a linebreak after."""
    return u'%s%s\n' % (settings.DPASTE_BASE_URL, s.get_absolute_url())

def _format_json(s):
    """The `json` format export."""
    return json.dumps({
        'url': u'%s%s' % (settings.DPASTE_BASE_URL, s.get_absolute_url()),
        'content': s.content,
        'lexer': s.lexer,
    })


FORMAT_MAPPING = {
    'default': _format_default,
    'url': _format_url,
    'json': _format_json,
}

@csrf_exempt
def snippet_api(request):
    content = request.POST.get('content', '').strip()
    lexer = request.REQUEST.get('lexer', LEXER_DEFAULT).strip()
    format = request.REQUEST.get('format', 'default').strip()

    if not content:
        return HttpResponseBadRequest('No content given')

    if not lexer in LEXER_KEYS:
        return HttpResponseBadRequest('Invalid lexer given. Valid lexers are: %s' %
            ', '.join(LEXER_KEYS))

    s = Snippet.objects.create(
        content=content,
        lexer=lexer,
        expires=timezone.now() + datetime.timedelta(seconds=60*60*24*30)
    )
    s.save()

    if not format in FORMAT_MAPPING:
        response = _format_default(s)
    else:
        response = FORMAT_MAPPING[format](s)

    return HttpResponse(response)


# -----------------------------------------------------------------------------
# Custom 404 and 500 views. Its easier to integrate this as a app if we
# handle them here.
# -----------------------------------------------------------------------------

def page_not_found(request, template_name='xelpaste/404.html'):
    return django_page_not_found(request, template_name) # pragma: no cover

def server_error(request, template_name='xelpaste/500.html'):
    return django_server_error(request, template_name) # pragma: no cover