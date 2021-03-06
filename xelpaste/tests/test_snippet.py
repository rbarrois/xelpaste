# -*- encoding: utf-8 -*-

from datetime import timedelta
import os.path

from django.core import management
from django.urls import reverse
from django.test.client import Client
from django.test import TestCase
from django.test.utils import override_settings

from libpaste.conf import settings
from libpaste.models import Snippet


class SnippetTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.new_url = reverse('snippet_new')
        self.upload_url = reverse('snippet_upload')
        self.EXAMPLE_IMAGE_PATH = os.path.join(
            os.path.dirname(__file__), 'testdata', 'image.png',
        )

    def valid_form_data(self):
        return {
            'content': u"Hello Wörld.\n\tGood Bye",
            'lexer': settings.LIBPASTE_LEXER_DEFAULT,
            'expires': settings.LIBPASTE_EXPIRE_DEFAULT,
            'author': "Someone",
        }

    def valid_upload_data(self):
        return {
            'expires': settings.LIBPASTE_EXPIRE_DEFAULT,
            'author': "Someone",
            'file': open(self.EXAMPLE_IMAGE_PATH, 'rb'),
        }


    def test_about(self):
        response = self.client.get(reverse('xelpaste_about'))
        self.assertEqual(response.status_code, 200)

    # -------------------------------------------------------------------------
    # New Snippet
    # -------------------------------------------------------------------------
    def test_empty(self):
        """
        The browser sent a content field but with no data.
        """
        # No data
        self.client.post(self.new_url, {})
        self.assertEqual(Snippet.objects.count(), 0)

        data = self.valid_form_data()

        # No content
        data['content'] = ''
        self.client.post(self.new_url, data)
        self.assertEqual(Snippet.objects.count(), 0)

        # Just some spaces
        data['content'] = '   '
        self.client.post(self.new_url, data)
        self.assertEqual(Snippet.objects.count(), 0)

        # Linebreaks or tabs only are not valid either
        data['content'] = '\n\t '
        self.client.post(self.new_url, data)
        self.assertEqual(Snippet.objects.count(), 0)

    def test_new_snippet(self):
        # Simple GET
        response = self.client.get(self.new_url, follow=True)

        # POST data
        data = self.valid_form_data()
        response = self.client.post(self.new_url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snippet.objects.count(), 1)
        self.assertContains(response, data['content'])

        # The unicode method contains the snippet id so we can easily print
        # the id using {{ snippet }}
        snippet = Snippet.objects.all()[0]
        self.assertTrue(snippet.secret_id in snippet.__unicode__())

    def test_new_upload(self):
        # Simple GET
        response = self.client.get(self.upload_url, follow=True)

        # POST data
        data = self.valid_upload_data()
        response = self.client.post(self.upload_url, data, follow=True)
        data['file'].close()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snippet.objects.count(), 1)

        snippet = Snippet.objects.get()
        self.assertContains(response, 'img src="/{}/raw"'.format(snippet.secret_id))

        # Get raw data
        response = self.client.get(reverse('snippet_details_raw', kwargs=dict(snippet_id=snippet.secret_id)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        with open(self.EXAMPLE_IMAGE_PATH, 'rb') as f:
            self.assertEqual(f.read(), response.content)

    def test_new_snippet_custom_lexer(self):
        # You can pass a lexer key in GET.l
        data = self.valid_form_data()
        url = '%s?l=haskell' % self.new_url
        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snippet.objects.count(), 1)

        # If you pass an invalid key it wont fail and just fallback
        # to the default lexer.
        data = self.valid_form_data()
        url = '%s?l=invalid-lexer' % self.new_url
        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snippet.objects.count(), 2)

    def test_new_spam_snippet(self):
        """
        The form has a `title` field acting as a honeypot, if its filled,
        the snippet is considered as spam. We let the user know its spam.
        """
        data = self.valid_form_data()
        data['title'] = u'Any content'
        response = self.client.post(self.new_url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snippet.objects.count(), 0)

    def test_new_snippet_onetime(self):
        """
        One-time snippets get deleted after two views.
        """
        # POST data
        data = self.valid_form_data()
        data['expires'] = 'onetime'

        # First view, the author gets redirected after posting
        response = self.client.post(self.new_url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snippet.objects.count(), 1)
        self.assertContains(response, data['content'])

        # Second View, another user looks at the snippet
        response = self.client.get(response.request['PATH_INFO'], follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snippet.objects.count(), 1)
        self.assertContains(response, data['content'])

        # Third/Further View, another user looks at the snippet but it was deleted
        response = self.client.get(response.request['PATH_INFO'], follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Snippet.objects.count(), 0)

    # -------------------------------------------------------------------------
    # Reply
    # -------------------------------------------------------------------------
    def test_reply(self):
        data = self.valid_form_data()
        response = self.client.post(self.new_url, data, follow=True)
        response = self.client.post(response.request['PATH_INFO'], data, follow=True)
        self.assertContains(response, data['content'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snippet.objects.count(), 2)

    def test_reply_invalid(self):
        data = self.valid_form_data()
        response = self.client.post(self.new_url, data, follow=True)
        del data['content']
        response = self.client.post(response.request['PATH_INFO'], data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snippet.objects.count(), 1)

    # -------------------------------------------------------------------------
    # Delete
    # -------------------------------------------------------------------------
    def test_snippet_delete_post(self):
        """
        You can delete a snippet by passing the slug in POST.snippet_id
        """
        data = self.valid_form_data()
        self.client.post(self.new_url, data, follow=True)
        snippet_id = Snippet.objects.all()[0].secret_id
        response = self.client.post(reverse('snippet_delete'),
            {'snippet_id': snippet_id}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snippet.objects.count(), 0)

    def test_snippet_delete_urlarg(self):
        """
        You can delete a snippet by having the snippet id in the URL.
        """
        data = self.valid_form_data()
        self.client.post(self.new_url, data, follow=True)
        snippet_id = Snippet.objects.all()[0].secret_id
        response = self.client.get(reverse('snippet_delete',
            kwargs={'snippet_id': snippet_id}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snippet.objects.count(), 0)

    def test_snippet_delete_that_doesnotexist_returns_404(self):
        data = self.valid_form_data()
        self.client.post(self.new_url, data, follow=True)

        # Pass a random snippet id
        response = self.client.post(reverse('snippet_delete'),
            {'snippet_id': 'doesnotexist'}, follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Snippet.objects.count(), 1)

        # Do not pass any snippet_id
        response = self.client.post(reverse('snippet_delete'), follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Snippet.objects.count(), 1)

    # -------------------------------------------------------------------------
    # Snippet Functions
    # -------------------------------------------------------------------------
    def test_raw(self):
        data = self.valid_form_data()
        self.client.post(self.new_url, data, follow=True)
        response = self.client.get(reverse('snippet_details_raw', kwargs={
            'snippet_id': Snippet.objects.all()[0].secret_id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, data['content'])

    # -------------------------------------------------------------------------
    # The diff function takes two snippet primary keys via GET.a and GET.b
    # and compares them.
    # -------------------------------------------------------------------------
    def test_snippet_diff_no_args(self):
        # Do not pass `a` or `b` is a bad request.
        response = self.client.get(reverse('snippet_diff'))
        self.assertEqual(response.status_code, 400)


    def test_snippet_diff_invalid_args(self):
        # Random snippet ids that dont exist
        url = '%s?a=%s&b=%s' % (reverse('snippet_diff'), 123, 456)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_snippet_diff_valid_nochanges(self):
        # A diff of two snippets is which are the same is OK.
        data = self.valid_form_data()
        self.client.post(self.new_url, data, follow=True)
        self.client.post(self.new_url, data, follow=True)

        self.assertEqual(Snippet.objects.count(), 2)
        a = Snippet.objects.all()[0].id
        b = Snippet.objects.all()[1].id
        url = '%s?a=%s&b=%s' % (reverse('snippet_diff'), a, b)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_snippet_diff_valid(self):
        # Create two valid snippets with different content.
        data = self.valid_form_data()
        self.client.post(self.new_url, data, follow=True)
        data['content'] = 'new content'
        self.client.post(self.new_url, data, follow=True)

        self.assertEqual(Snippet.objects.count(), 2)
        a = Snippet.objects.all()[0].id
        b = Snippet.objects.all()[1].id
        url = '%s?a=%s&b=%s' % (reverse('snippet_diff'), a, b)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    # -------------------------------------------------------------------------
    # History
    # -------------------------------------------------------------------------
    def test_snippet_history(self):
        response = self.client.get(reverse('snippet_history'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snippet.objects.count(), 0)

        data = self.valid_form_data()
        self.client.post(self.new_url, data, follow=True)
        response = self.client.get(reverse('snippet_history'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snippet.objects.count(), 1)

    def test_snippet_history_delete_all(self):
        # Empty list, delete all raises no error
        response = self.client.get(reverse('snippet_history') + '?delete-all', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snippet.objects.count(), 0)

        # Create two sample pasts
        data = self.valid_form_data()
        self.client.post(self.new_url, data, follow=True)
        data = self.valid_form_data()
        self.client.post(self.new_url, data, follow=True)
        self.assertEqual(Snippet.objects.count(), 2)

        # Delete all of them
        response = self.client.get(reverse('snippet_history') + '?delete-all', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Snippet.objects.count(), 0)

    @override_settings(LIBPASTE_MAX_SNIPPETS_PER_USER=2)
    def test_snippet_that_exceed_history_limit_get_trashed(self):
        """
        The maximum number of snippets a user can save in the session are
        defined by `LIBPASTE_MAX_SNIPPETS_PER_USER`. Exceed that number will
        remove the oldest snippet from the list.
        """
        # Create three snippets but since the setting is 2 only the latest two
        # will displayed on the history.
        data = self.valid_form_data()
        self.client.post(self.new_url, data, follow=True)
        self.client.post(self.new_url, data, follow=True)
        self.client.post(self.new_url, data, follow=True)

        response = self.client.get(reverse('snippet_history'), follow=True)
        one, two, three = Snippet.objects.order_by('published')

        # Only the last two are saved in the session
        self.assertEqual(len(self.client.session['snippet_list']), 2)
        self.assertFalse(one.id in self.client.session['snippet_list'])
        self.assertTrue(two.id in self.client.session['snippet_list'])
        self.assertTrue(three.id in self.client.session['snippet_list'])

        # And only the last two are displayed on the history page
        self.assertNotContains(response, one.secret_id)
        self.assertContains(response, two.secret_id)
        self.assertContains(response, three.secret_id)


    # -------------------------------------------------------------------------
    # Management Command
    # -------------------------------------------------------------------------
    def test_delete_management(self):
        # Create two snippets
        data = self.valid_form_data()
        self.client.post(self.new_url, data, follow=True)
        data = self.valid_form_data()
        self.client.post(self.new_url, data, follow=True)
        self.assertEqual(Snippet.objects.count(), 2)

        # But the management command will only remove snippets past
        # its expiration date, so change one to last month
        s = Snippet.objects.all()[0]
        s.expires = s.expires - timedelta(days=30)
        s.save()

        # You can call the management command with --dry-run which will
        # list snippets to delete, but wont actually do.
        management.call_command('cleanup_snippets', dry_run=True)
        self.assertEqual(Snippet.objects.count(), 2)

        # Calling the management command will delete this one
        management.call_command('cleanup_snippets')
        self.assertEqual(Snippet.objects.count(), 1)

    def test_delete_management_snippet_that_never_expires_will_not_get_deleted(self):
        """
        Snippets without an expiration date wont get deleted automatically.
        """
        data = self.valid_form_data()
        self.client.post(self.new_url, data, follow=True)

        self.assertEqual(Snippet.objects.count(), 1)

        s = Snippet.objects.all()[0]
        s.expires = None
        s.save()

        management.call_command('cleanup_snippets')
        self.assertEqual(Snippet.objects.count(), 1)

    def test_highlighting(self):
        # You can pass any lexer to the pygmentize function and it will
        # never fail loudly.
        from libpaste.highlight import pygmentize
        pygmentize('code', lexer_name='python')
        pygmentize('code', lexer_name='doesnotexist')

    # This is actually a bad test. It is possible to have duplicates
    # because even if its random, it can generate two random, equal strings.
    #
    # def test_random_slug_generation(self):
    #     """
    #     Generate 1000 random slugs, make sure we have no duplicates.
    #     """
    #     from libpaste.models import generate_secret_id
    #     result_list = []
    #     for i in range(0, 1000):
    #         result_list.append(generate_secret_id())
    #     self.assertEqual(len(set(result_list)), 1000)
