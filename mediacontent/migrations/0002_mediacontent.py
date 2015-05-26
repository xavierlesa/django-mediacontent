# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('mediacontent', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MediaContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('object_pk', models.PositiveIntegerField()),
                ('mimetype', models.CharField(max_length=100, blank=True)),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('thumbnail_only', models.BooleanField(default=False, help_text=b'Indica si se usa como thumbnail del objeto asociado')),
                ('gallery_only', models.BooleanField(default=False, help_text=b'Indica si se usa para gallery del objeto asociado')),
                ('content', models.FileField(max_length=300, upload_to=b'media')),
                ('thumbnail', models.ImageField(max_length=300, upload_to=b'medoa', blank=True)),
                ('gallery', models.ImageField(max_length=300, upload_to=b'media', blank=True)),
                ('pub_date', models.DateTimeField(blank=True)),
                ('content_type', models.ForeignKey(related_name='content_type_set_for_mediacontent', verbose_name='content type', to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ('sort_order', 'pub_date'),
            },
        ),
    ]
