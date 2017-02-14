#!/usr/bin/env python

"""
Script downloads the model output from the NCAS air quality from:

   https://sci.ncas.ac.uk/airquality/

and creates a kmz file that is viewable in google-earth. This allows for
example FAAM flight tracks to be overlaid on top of the model images

"""

import datetime
import requests
import shutil
import simplekml
import subprocess
import tempfile
import os
import sys

response = requests.get('https://sci.ncas.ac.uk/airquality/')

ROOT_URL='https://sci.ncas.ac.uk'


TEMPDIR=tempfile.mkdtemp()              # temporary directory where the png images will be saved
VARIABLES=['O3', 'NOx', 'PM25']         # variables for which models will be downloaded

# ground control points and boundaries are static for the NCAS air quality output and were derived using the georeferencer tool from qgis
gcps = "-gcp 209.743 43.3586 -8 60 -gcp 281.457 43.0282 -4 60 -gcp 352.443 42.896 0 60 -gcp 209.412 112.428 -8 58 -gcp 281.655 112.627 -4 58 -gcp 352.575 112.561 0 58 -gcp 209.412 178.458 -8 56 -gcp 281.853 178.59 -4 56 -gcp 352.575 178.226 0 56 -gcp 209.545 240.356 -8 54 -gcp 281.457 240.488 -4 54 -gcp 352.575 240.356 0 54 -gcp 209.743 299.809 -8 52 -gcp 281.721 299.313 -4 52 -gcp 352.509 299.809 0 52 -gcp 209.677 356.552 -8 50 -gcp 281.589 356.552 -4 50 -gcp 352.509 356.651 0 50 "
miny, maxy, minx, maxx = 47.186609484953294, 61.20747141385112, -19.282507889150953, 13.009442407021385


def get_image(url):
    """
    download image from the website

    :param url: http address

    """
    response = requests.get(url, stream=True)
    local_image_filename=os.path.join(TEMPDIR, os.path.split(url)[-1].encode('ascii'))
    with open(local_image_filename, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response
    return local_image_filename


def img_to_gtiff(img_filename, tif_filename):
    """convert png to geotiff using ground control points

    :param img_filename: model png image file name
    :param tif_filename: geo-tiff file warped to EPSG\:4326
    """
    tif_tmp_filename = tempfile.mkstemp(suffix='.tif')[1]

    cmd1 = """gdal_translate -of GTiff %s "%s" "%s" """ % (gcps, img_filename, tif_tmp_filename)
    cmd2 = """gdalwarp -t_srs EPSG:4326 -order -tps -co COMPRESS=NONE  "%s" "%s" """ % (tif_tmp_filename, tif_filename)

    proc1 = subprocess.Popen(cmd1, shell=True)
    proc1.wait()
    proc2 = subprocess.Popen(cmd2, shell=True)
    proc2.wait()
    return


def parse_ncas_airquality():
    image_lists = {v: [] for v in VARIABLES}
    lines = response.text.split('\n')
    for line in lines:
        if line.strip().startswith('images'):
            line = line.replace('\\/', '/')
            line = line.replace('"', '')
            line.encode('ascii')
            images = line[line.find("[")+1:line.find("]")]
            if 'O3_' in line:
                image_lists['O3'] = images.split(',')
            elif 'NOx_' in line:
                image_lists['NOx'] = images.split(',')
            elif 'PM25_' in line:
                image_lists['PM25'] = images.split(',')
    return image_lists


def process(outpath, limit=None):
    image_lists=parse_ncas_airquality()
    if not limit:
        limit = len(image_lists[image_lists.keys()[0]])
    kml = simplekml.Kml()
    for var in VARIABLES:
        folder = kml.newfolder(name=var)
        folder.open = 1
        for img in image_lists[var][0:limit]:
            image_filename = get_image(ROOT_URL+img.encode('ascii'))
            img_to_gtiff(image_filename, image_filename[:-3]+'tif')
            image_filename = image_filename[:-3]+'tif'
            timestamp = datetime.datetime.strptime(img.split('/')[-1][-17:-4].encode(), '%Y-%m-%d_%H')
            timestamp = timestamp.strftime('%Y-%m-%dT%H:%M')
            ground = folder.newgroundoverlay(name=timestamp)
            ground.visibility = 0
            ground.icon.href = image_filename
            ground.gxlatlonquad.coords = [(minx, miny), (maxx, miny),
                                          (maxx, maxy), (minx, maxy)]

    outfile = os.path.join(outpath, 'ncas_airquality_%s.kmz' % ''.join(image_lists[VARIABLES[0]][0].split('/')[-1][3:-7].split('-')))
    kml.savekmz(outfile)
    return outfile


def parser():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-o', '--outpath',
                        action="store",
                        default=os.environ['HOME'],
                        type=str,
                        help='outpath')
    parser.add_argument('-l', '--limit',
                        action="store",
                        type=int,
                        default=0,
                        help='maximum number of model images to be processed')
    return parser

def main():
    parser = parser()
    args = parser.parse_args()
    outfile = process(args.outpath)
    sys.stdout.write('Created ... %s. \n' % outfile)


if __name__ == '__main__':
    main()
