# *-* coding:utf-8 *-*
"""
Una app para cargar contenidos multimedia

"""
import mimetypes
import datetime
import os
try:
    from Pillow import Image
except ImportError:
    try:
        from PIL import Image
    except ImportError:
        import Image

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes import generic
from django.utils.encoding import force_unicode
from mediacontent.utils import convert_to_rgb, crop_aspect, resize

def_sizes = {
    'thumb': (75,75),
    'gallery': (250, 250),
    'normal': (600,600)
    }

CONTENT_MEDIA_SIZE = getattr(settings, 'CONTENT_MEDIA_SIZE', def_sizes)
CONTENT_MEDIA_PATH = getattr(settings, 'CONTENT_MEDIA_PATH', 'mediacontent')


class MediaContentManager(models.Manager):
    def get_for_model(self, model):
        ct = ContentType.objects.get_for_model(model)
        qs = self.get_query_set().filter(content_type=ct)

        if isinstance(model, models.Model):
            qs = qs.filter(object_pk=force_unicode(model._get_pk_val()))
        return qs


class MediaContent(models.Model):
    def _get_ct(self):
        mcls = ContentType.objects.get(pk=self.content_type.pk)

        # esto fixea el problema de multise y _default_manager
        if self.content_object:
            return self.content_object
        try:
            cls = mcls.get_object_for_this_type(pk=self.object_pk)
        except mcls.model_class().DoesNotExist:
            cls = mcls.model_class()
        return cls

    def get_content_path(self, filename):
        cls = self._get_ct()
        return u'%s/%s/%s/%s' % (CONTENT_MEDIA_PATH, cls._meta.module_name, self.object_pk, filename)
    
    def get_thumb_path(self, filename):
        cls = self._get_ct()
        return u'%s/%s/%s/thumbnail_%s' % (CONTENT_MEDIA_PATH, cls._meta.module_name, self.mimetype, filename)

    def get_gallery_path(self, filename):
        cls = self._get_ct()
        return u'%s/%s/%s/gallery_%s' % (CONTENT_MEDIA_PATH, cls._meta.module_name, self.mimetype, filename)

    def content_path(self, filename):
        return self.get_content_path(filename)

    def thumb_path(self, filename):
        return self.get_thumb_path(filename)

    def gallery_path(self, filename):
        return self.get_gallery_path(filename)

    def get_sizes(self):
        return CONTENT_MEDIA_SIZE


    content_type = models.ForeignKey(ContentType, verbose_name=_('content type'), related_name="content_type_set_for_%(class)s")
    object_pk = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_pk')
    
    mimetype = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    content = models.FileField(upload_to=content_path, max_length=300)
    thumbnail = models.ImageField(upload_to=thumb_path, blank=True, max_length=300)
    gallery = models.ImageField(upload_to=gallery_path, blank=True, max_length=300)

    #hay que actualizar la DB y generar todas las fechas por defecto
    pub_date = models.DateTimeField(blank=True)

    objects = MediaContentManager()

    class Meta:
        ordering = ('pub_date','id')


    def __init__(self, *args, **kwargs):
        super(MediaContent, self).__init__(*args, **kwargs)
        self.__original_image = self.content

    def __unicode__(self):
        return unicode(self.title)

    def save(self, *args, **kwargs):

        changed_image = self.content != self.__original_image

        if not self.id and not self.pub_date:
            self.pub_date = datetime.datetime.today()
        
        crop_original = kwargs.get('crop_original', False)
        
        super(MediaContent, self).save(*args, **kwargs)
        self.mimetype = mimetypes.guess_type(self.content.path)[0]

        if self.mimetype:
            content_type = self.mimetype.replace('/', '_')
        else:
            # assume everything else is text/plain
            content_type = 'text_plain'
        
        i = self.content.name.rindex('/')
        thumbnail = u'%sthumbnail_%s' % (unicode(self.content.name[:i+1]), unicode(self.content.name[i+1:]))
        gallery = u'%sgallery_%s' % (unicode(self.content.name[:i+1]), unicode(self.content.name[i+1:]))
        orig = self.content.name

        if (not self.thumbnail or not self.gallery or changed_image) and content_type.split('_')[0]=='image':
            img_path = self.content.path

            if content_type == 'image_svg+xml':
                try:
                    from nebula.mediacontent import svg_to_png
                    svg_to_png.convert(img_path, svg_to_png.new_name(img_path))
                    img_path = svg_to_png.new_name(img_path)
                    self.content.name = self.content.name[:-3] + self.content.name[-3:].replace('svg', 'png')
                except:
                    pass

            image = Image.open(img_path)
            image = convert_to_rgb(image)
            image = crop_aspect(image, ratio=1.0)

            # hace el thumb
            image_thumb = resize(image.copy(), size=self.get_sizes()['thumb'])
            image_thumb.save(os.path.join(settings.MEDIA_ROOT, thumbnail))
            self.thumbnail = thumbnail

            # guarda la imagen para gallery
            image_gallery = resize(image.copy(), size=self.get_sizes()['gallery'])
            image_gallery.save(os.path.join(settings.MEDIA_ROOT, gallery))
            self.gallery = gallery

            # guarda la imagen al tamaño máximo
            if crop_original:
                image_normal = resize(image.copy(), size=self.get_sizes()['normal'])
                image_normal.save(os.path.join(settings.MEDIA_ROOT, orig))


        elif (not self.thumbnail or not self.gallery or changed_image) and content_type == 'application_pdf':
            print 'carga un pdf'

            # Crea una imagen de la primer pagina de un PDF
            from subprocess import call

            cmd = "gs -q -dQUIET -dPARANOIDSAFER -dBATCH -dNOPAUSE -dNOPROMPT \
                    -dMaxBitmap=500000000 -dLastPage=1 -dAlignToPixels=0 -dGridFitTT=0 \
                    -sDEVICE=jpeg -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -r150 \
                    -sOutputFile=%(fileout)s %(filein)s"

            filein = os.path.join(settings.MEDIA_ROOT, self.content.name)
            filejpg = self.content.name[:-3] + self.content.name[-3:].replace('pdf', 'jpg')
            fileout = os.path.join(settings.MEDIA_ROOT, filejpg)

            if not os.access(filein, os.R_OK):
                raise 'not access %s' % filein

            files = { 
                'filein': filein.replace(' ', '\ '),
                'fileout': fileout.replace(' ', '\ '), 
            }

            # devuelve 0 si esta OK
            if not call(cmd % files, shell=True):

                i = filejpg.rindex('/')

                thumbnail = u'%sthumbnail_%s' % (unicode(filejpg[:i+1]), unicode(filejpg[i+1:]))
                gallery = u'%sgallery_%s' % (unicode(filejpg[:i+1]), unicode(filejpg[i+1:]))

                image = Image.open(fileout)
                image = convert_to_rgb(image)
                #image = crop_aspect(image, ratio=1.0)

                # hace el thumb
                image_thumb = resize(image.copy(), size=None, max_width=self.get_sizes()['gallery'][0])
                image_thumb.save(os.path.join(settings.MEDIA_ROOT, thumbnail))
                self.thumbnail = thumbnail

                # guarda la imagen para gallery
                #image_gallery = image.copy()
                image_gallery = resize(image.copy(), size=None, max_width=self.get_sizes()['normal'][0])
                image.save(os.path.join(settings.MEDIA_ROOT, gallery))
                self.gallery = gallery

                # borra la original porque es un PDF
                try:
                    os.remove(fileout)
                except (OSError, ValueError):
                    pass
            
        super(MediaContent, self).save(*args, **kwargs)



    def delete(self, *args, **kwargs):
        try:
            os.remove(self.content.path)
        except (OSError, ValueError):
            pass
        try:
            os.remove(self.gallery.path)
        except (OSError, ValueError):
            pass
        try:
            os.remove(self.thumbnail.path)
        except (OSError, ValueError):
            pass
        return super(MediaContent, self).delete(*args, **kwargs)

    def get_header(self):
        return self.mimetype.split('/')[0]
    
    def get_file_name(self):
        return self.content.name.split('/')[-1]
