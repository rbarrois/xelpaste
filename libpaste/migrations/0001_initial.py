# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Snippet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('secret_id', models.CharField(verbose_name='Secret ID', max_length=255, null=True, blank=True)),
                ('author', models.CharField(verbose_name='Author', max_length=255, default='', null=True, blank=True)),
                ('content', models.TextField(verbose_name='Content')),
                ('lexer', models.CharField(verbose_name='Lexer', max_length=30, default='python')),
                ('published', models.DateTimeField(verbose_name='Published', auto_now_add=True)),
                ('expire_type', models.PositiveSmallIntegerField(verbose_name='Expire Type', choices=[(1, 'Expire by timestamp'), (2, 'Keep Forever'), (3, 'One time snippet')], default=1)),
                ('expires', models.DateTimeField(verbose_name='Expires', null=True, blank=True)),
                ('view_count', models.PositiveIntegerField(verbose_name='View count', default=0)),
                ('file', models.FileField(verbose_name='File', max_length=255, upload_to='snippets', null=True, blank=True)),
                ('content_type', models.CharField(verbose_name='Content type', max_length=255, null=True, blank=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', models.ForeignKey(to='libpaste.Snippet', related_name='children', null=True, blank=True)),
            ],
            options={
                'db_table': 'xelpaste_snippet',
                'ordering': ('-published',),
            },
        ),
    ]
