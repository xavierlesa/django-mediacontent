# +-+ coding:utf8 +-+

import os
import uuid
import re
try:
    from PIL import Image
except ImportError:
    import Image
from django import template
from django.conf import settings
from django.contrib.sites.models import Site
from mediacontent.utils import convert_to_rgb, crop_aspect, resize

MEDIA_ROOT, MEDIA_URL = settings.MEDIA_ROOT, settings.MEDIA_URL
STATIC_ROOT, STATIC_URL = settings.STATIC_ROOT, settings.STATIC_URL
MEDIACONTENT_STATIC_PATH = getattr(settings, 'MEDIACONTENT_STATIC_PATH', MEDIA_ROOT)

register = template.Library()


def _create_tmp(image, preserve_name=False, preserve_path=False):
    path = image.filename
    fname = os.path.basename(path)
    fpath = os.path.dirname(path)
    imgid = 'tmp_' + fname # default name tmp_[FILENAME]

    if not preserve_name:
        imgid = uuid.uuid1().hex
        imgid = imgid + '.' + image.format.lower()

    if not preserve_path:
        fpath = MEDIACONTENT_STATIC_PATH

    filename = os.path.join(fpath, imgid)

    nimage = image.copy()
    nimage.save(filename)
    #return nimage
    return Image.open(filename)


def image_resize(context, image, size=None, max_width=None, max_height=None, *args, **kwargs):
    """
    {% image_resize image[url] size=75x75 or max_width=70 or max_height=75 %}
    """

    # Get instance or string
    if isinstance(image, basestring):
        image = Image.open(image)

    if size:
        size = size.split('x')

    image = resize(image, size, max_width, max_height)
    print image.size

    imgid = uuid.uuid1().hex
    imgid = imgid + '.jpg'
    fpath = MEDIACONTENT_STATIC_PATH
    filename = os.path.join(fpath, imgid)

    print 'save on', filename
    image.save(filename, 'JPEG', quality=70) # guarda la iamgen resized

    filename = os.path.basename(image.filename)
    image.url = STATIC_URL + filename

    return image


def image_crop(context, image, ratio=1.0, size=None, preserve_name=False, preserve_path=False):
    """
    {% image_crop image[url] [ratio=1.0] [size=None] %}
    """

    # Get instance or string
    if isinstance(image, basestring):
        image = Image.open(image)

    if size:
        size = size.split('x')
    
    path = image.filename
    i = path.rindex('/')
    imgid = 'tmp_' + path[i+1:]
    path = path[:i+1]

    if not preserve_name:
        imgid = uuid.uuid1().hex
        imgid = imgid + '.' + image.format.lower()

    if not preserve_path:
        path = MEDIACONTENT_STATIC_PATH + '/'

    filename = path + imgid

    nimage = crop_aspect(image, ratio, size)
    nimage.save(filename)
    
    image = Image.open(filename)
    url = filename
    url = re.sub(MEDIA_ROOT, MEDIA_URL, url)
    url = re.sub(STATIC_ROOT, STATIC_URL, url)
    image.url = url
    return image


def get_image_size(path):
    """
    {{ object.image.path|get_image_size }}
    """
    try:
        image = Image.open(path)
    except:
        return None

        
    return image.size

@register.assignment_tag(takes_context=True)
def get_video(context):
    result = """<video class="video-js vjs-default-skin" controls preload="auto" poster="%(poster)s" data-setup="{}" id="vid_%(id)s" width="470" height="264">
                <source src="//%(domain)s%(url)s" type='%(mime)s' />
            </video>"""
    obj = context.get('object', False)
    print 'obj', obj
    if obj:
        videos = obj.media_content.filter(mimetype__startswith="video")
        poster = obj.first_image

        if videos.exists:
            video = videos[0]
            return result % {
                'poster': poster and poster.content and poster.content.url or '',
                'domain': Site.objects.get_current().domain,
                'url': video.content.url,
                'mime': video.mimetype,
                'id': video.id,
            }

    return ''

@register.assignment_tag(takes_context=True)
def get_media_by_title(context, title=''):
    obj = context.get('object', False)

    if obj:
        res = obj.media_content.filter(title=title)
        if res.exists():
            return res[0]

    return ''

@register.filter
def get_youtube_id(url):
    regexs = {
        'youtube': r'^http:\/\/(?:www\.)?youtube.com\/watch\?(?=[^?]*v=(?P<id>[\w\-\_]+))(?:[^\s?]+)?$',
        'youtube_small': r'^http:\/\/(?:www\.)?youtu.be\/(?P<id>[\w\-\_]+)(?:[^\s?]+)?$',
    }

    for regex in regexs.values():
        passes_test = re.match(regex, url)
        if passes_test:
            return passes_test.groupdict()['id']
    return False


register.filter(get_image_size)
register.assignment_tag(takes_context=True)(image_resize)
register.assignment_tag(takes_context=True)(image_crop)
