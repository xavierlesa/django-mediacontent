#!/usr/bin/python

import cairo
import rsvg
import os
import sys

def convert(data, ofile, maxwidth=0, maxheight=0):

    svg = rsvg.Handle(data)

    x = width = svg.props.width
    y = height = svg.props.height
    #print "actual dims are " + str((width, height))
    #print "converting to " + str((maxwidth, maxheight))

    yscale = xscale = 1

    if (maxheight != 0 and width > maxwidth) or (maxheight != 0 and height > maxheight):
        x = maxwidth
        y = float(maxwidth)/float(width) * height
        #print "first resize: " + str((x, y))
        if y > maxheight:
            y = maxheight
            x = float(maxheight)/float(height) * width
            #print "second resize: " + str((x, y))
        xscale = float(x)/svg.props.width
        yscale = float(y)/svg.props.height

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, x, y)
    context = cairo.Context(surface)
    context.scale(xscale, yscale)
    svg.render_cairo(context)
    surface.write_to_png(ofile)

def new_name(file):
    os.path.splitext(file)
    return '.'.join([os.path.splitext(file)[0],'png'])

if __name__ == '__main__':
    files = sys.argv[1:]
    for file in files:
        convert(file, new_name(file))
