# *-* coding:utf-8 *-*

try:
    from PIL import Image
except ImportError:
    import Image

# helper
def convert_to_rgb(image):
    """
    Convierte una imagen a su reresentación en RGB
    """
    if image.mode not in ('L', 'RGB'):
        image = image.convert('RGB')

    return image


def crop_aspect(image, ratio=1.0, size=None):
    """
    esto es para que cropee la imagen al aspecto
    fuente: http://stackoverflow.com/questions/4094744/how-can-i-take-an-image-and-get-a-3x2-ratio-image-cropped-from-the-center
    """
    imagewidth,imageheight = image.size

    # determine the dimensions of a crop area
    # which is no wider or taller than the image
    if int(imagewidth*ratio) > imageheight:
        cropheight,cropwidth = imageheight,int(imageheight/ratio)
    else:
        cropwidth,cropheight = imagewidth,int(imagewidth*ratio)

    # center the crop area on the image (dx and/or dy will be zero)
    dx,dy = (imagewidth-cropwidth)/2,(imageheight-cropheight)/2

    # crop, save, and return image data
    image = image.crop((dx,dy,cropwidth+dx,cropheight+dy))

    if size:
        image.thumbnail(size, Image.ANTIALIAS)

    return image


def resize(image, size=(75,75), max_width=None, max_height=None):
    image = convert_to_rgb(image)
    ow, oh = image.size

    if size:
        image.thumbnail(size, Image.ANTIALIAS)

    if max_width:
        rh = int(float(ow)/float(oh)*max_width)
        image.thumbnail((max_width, rh), Image.ANTIALIAS)

    if max_height:
        rw = int(float(ow)/float(oh)*max_height)
        image.thumbnail((rw, max_height), Image.ANTIALIAS)

    return image
