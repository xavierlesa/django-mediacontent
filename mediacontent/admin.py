# -*- coding:utf-8 -*-
import mimetypes
from django.contrib import admin
from django.db import models
from django.conf.urls import patterns, url
from django import forms
from django.contrib.contenttypes.admin import GenericStackedInline
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.safestring import mark_safe
from django.conf import settings
from django.core import urlresolvers
from django.views.decorators.csrf import csrf_exempt
from mediacontent.models import MediaContent
from mediacontent.views import AjaxMediaAPIView

class AdminMediaContentWidget(AdminFileWidget):
    def __init__(self, attrs={}):
        super(AdminMediaContentWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        output = []
        if value and hasattr(value, "url"):
            mimetype = mimetypes.guess_type(value.url)[0]
            i = str(value.url).rindex('/')
            img_src = u'%sthumbnail_%s' % (unicode(value.url)[:i+1], unicode(value.url)[i+1:])

            if mimetype.split('/')[0] == 'image':
                output.append(u"<div style=\"overflow:hidden; width:100px; float:right\"><img src=\"%s\" /></div>" % (img_src))
            else:
                output.append(u"<div style=\"overflow:hidden; width:100px; float:right\"><img src=\"http://placehold.it/150x150&text=none\" /></div>")

        output.append(super(AdminMediaContentWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))


class MediaContentInline(GenericStackedInline):
    model = MediaContent
    extra = 1
    ct_field = 'content_type'
    ct_fk_field = 'object_pk'
    verbose_name = "Multimedia"
    verbose_name_plural = "Multimedias"

    fieldsets = (
            (None, {
                'fields': (
                    'title', 
                    'description', 
                    'thumbnail_only', 
                    'gallery_only', 
                    'sort_order', 
                    'content', 
                    'pub_date'
                    )
                }),
            )

    formfield_overrides = {
            models.FileField: {
                'widget': AdminMediaContentWidget
                },
            models.TextField: {
                'widget': forms.Textarea(
                    attrs = {
                        'cols':40, 
                        'rows':2
                        }
                    )}
                }

    verbose_name = u"multimedia"


class MediaContentAdmin(admin.ModelAdmin):
    list_display = (
            'get_content', 
            'title', 
            'content_type', 
            'get_content_object', 
            'get_thumbnail'
            )

    formfield_overrides = { 
            models.FileField: {
                'widget': AdminMediaContentWidget
                },
            models.TextField: {
                'widget': forms.Textarea(
                    attrs = {
                        'cols':40, 
                        'rows':2
                        }
                    )}
                }
  
    fieldsets = (
            (None, {
                'fields': (
                    'title', 
                    'description', 
                    'content_type', 
                    'object_pk', 
                    'mimetype', 
                    'thumbnail_only', 
                    'gallery_only', 
                    'sort_order', 
                    'content', 
                    'thumbnail', 
                    'gallery', 
                    'pub_date'
                    )
                }),
            )
    
    def get_content_object(self, obj):
        if obj.content_object:
            obj_url = urlresolvers.reverse('admin:%s_%s_change' % (
                obj.content_object._meta.app_label, obj.content_object._meta.model_name),
                args=(obj.content_object.id,))
        else:
            obj_url = '#'

        return u"<a href=\"%s\">%s</a>" % (obj_url, obj.content_object)

    get_content_object.short_description = 'content object'
    get_content_object.allow_tags = True

    def get_content(self, obj):
        return obj.content.name.split('/')[-1:][0]

    get_content.short_description = 'content'

    def get_mimetype(self, obj):
        img = settings.MEDIA_URL + 'img/mimes/' + obj.mimetype.replace('/', '-') + '.png'
        return u"<img src=\"%s\" align=\"left\"/><span style=\"margin:5px 0 0 5px\">%s</span>" % (img, obj.mimetype)

    get_mimetype.allow_tags = True
    get_mimetype.short_description = 'mimetype'

    def get_thumbnail(self, obj):
        img = obj.thumbnail

        if img:
            return u"<a href=\"\" class=\"th\"><img src=\"%s\" /></a>" % img.url

    get_thumbnail.allow_tags = True
    get_thumbnail.short_description = 'thumbnail'

    def get_urls(self):
        urls = super(MediaContentAdmin, self).get_urls()
        
        my_urls = patterns('',
            url(r'^_ajax/(?:(?P<mimetype>[\w]+)/)?(?:(?P<pk>[\d]+)/)?$', 
                self.admin_site.admin_view(csrf_exempt(AjaxMediaAPIView.as_view())), 
                name='ajax_mediacontent_api'
                ), 
        )

        return my_urls + urls


admin.site.register(MediaContent, MediaContentAdmin)
