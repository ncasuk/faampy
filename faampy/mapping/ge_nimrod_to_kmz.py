#!/usr/bin/python

"""
Extracts all rain radar data from the tar file and:

- creates a 8bit png image file with a custom colour palette
- convertes the png to a gtiff and adds the projection ESPG:27700=OSGB1936
- warpes the gtiff image to EPSG:4326
- creates one kmz file with a folder which contains all gtiff-4326 files as groundoverlays

The original UKMO nimrod data files can be downloaded from CEDA_. 

.. note:: The script is very wasteful in terms of disk space. The temporary folder
          that is created for storing the image files can grow to several GB. The script
          deletes the temporary folder by default.

.. _CEDA: http://badc.nerc.ac.uk/browse/badc/ukmo-nimrod/data/composite/uk-1km/
"""

# TODO: Add legend to kmz file

import datetime
import gdal
import numpy as np
import subprocess
import shutil
import tempfile
from PIL import Image

import os, sys
import struct, array, time


_KML_HEADER="""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Folder>
    <name>%s</name>
    <open>0</open>
"""

_KML_GROUNDOVERLAY="""<GroundOverlay>
        <TimeSpan>
            <begin>%s</begin>
            <end>%s</end>
        </TimeSpan>
        <name>%s</name>
        <visibility>0</visibility>
        <open>0</open>
        <color>b5ffffff</color>
        <Icon>
            <href>files/%s</href>
            <viewBoundScale>0.75</viewBoundScale>
        </Icon>
        <LatLonBox>
            <north>%f</north>
            <south>%f</south>
            <east>%f</east>
            <west>%f</west>
        </LatLonBox>
</GroundOverlay>
"""

_KML_FOOTER="""</Folder>
</kml>
"""


#see: http://badc.nerc.ac.uk/browse/badc/ukmo-nimrod/doc/radar_key.gif
#((bin_lower_threshold, bin_upper_threshold), (R, G, B))
_PALETTE=[(( 0.00,  0.25),  ( 15,  31, 151)),   # darkblue
          (( 0.25,  0.50),  (  2,  77, 178)),   # mediumblue
          (( 0.50,  1.00),  ( 58, 108, 255)),   # lightblue
          (( 1.00,  2.00),  (  5, 182,   5)),   # green
          (( 2.00,  4.00),  (220, 205,   7)),   # yellow
          (( 4.00,  8.00),  (255, 154,   0)),   # orange
          (( 8.00, 16.00),  (202,  49,  51)),   # fuchsia
          ((16.00, 32.00),  (255,   2, 255)),   # white
          ((-2.00, -0.5),   (150, 150, 150))]   # lightgrey


#taken from: http://badc.nerc.ac.uk/browse/badc/ukmo-nimrod/software/python/read_nimrod.py
def read_nimrod(pathed_file, quite=True):

    file_id=open(pathed_file,"rb")
    record_length,=struct.unpack(">l", file_id.read(4))
    if record_length != 512:
        sys.stdout.write("Unexpected record length: %i" % record_length)
        sys.exit(1)

    gen_ints=array.array("h")
    gen_reals=array.array("f")
    spec_reals=array.array("f")
    characters=array.array("c")
    spec_ints=array.array("h")

    gen_ints.read(file_id, 31)
    gen_ints.byteswap()

    gen_reals.read(file_id, 28)
    gen_reals.byteswap()

    spec_reals.read(file_id, 45)
    spec_reals.byteswap()
    characters.read(file_id, 56)
    spec_ints.read(file_id, 51)
    spec_ints.byteswap()

    record_length,=struct.unpack(">l", file_id.read(4))
    if record_length != 512:
        raise ("Unexpected record length", record_length)

    #for i in range(len(gen_ints)): print i+1, gen_ints[i]
    #for i in range(len(gen_reals)): print i+32, gen_reals[i]
    chars=characters.tostring()

    if not quite:
        sys.stdout.write("\nDate %4.4d%2.2d%2.2d Time %2.2d:%2.2d Grid %d x %d\n" %(gen_ints[0], gen_ints[1], gen_ints[2], gen_ints[3], gen_ints[4], gen_ints[15], gen_ints[16]))
        sys.stdout.write("start northing %.1f, row interval %.1f, start easting %.1f, column interval %.1f\n"  %(gen_reals[2], gen_reals[3], gen_reals[4], gen_reals[5]))
        sys.stdout.write("Units are %s\n" % chars[0:8])
        sys.stdout.write("Data source is %s\n" % chars[8:32])
        sys.stdout.write("Parameter is %s\n" % chars[32:55])
        for i in range(gen_ints[22]):
            print(i+108, spec_ints[i])
        for i in gen_reals:
            print(i)
        for i in spec_reals:
            print(i)
    #Read data
    cols=gen_ints[15]
    rows=gen_ints[16]
    array_size=cols*rows

    record_length,=struct.unpack(">l", file_id.read(4))
    if record_length != array_size*2:
        raise ("Unexpected record length", record_length)

    data=array.array("h")
    try:
        data.read(file_id, array_size)
        record_length,=struct.unpack(">l", file_id.read(4))
        if record_length != array_size*2:
            raise ("Unexpected record length", record_length)
        data.byteswap()
    except:
        sys.stdout.write("Read failed\n")
    file_id.close()
    result={'data':             np.array(data),
            'cols':             cols,
            'rows':             rows,
            'start_northing':   gen_reals[2],
            'row_interval':     gen_reals[3],
            'start_easting':    gen_reals[4],
            'column_interval':  gen_reals[5],
            'year':             gen_ints[0],
            'month':            gen_ints[1],
            'day':              gen_ints[2],
            'hour':             gen_ints[3],
            'min':              gen_ints[4]}
    return result


def calc_kmz_boundaries(tiff_file):
    ds=gdal.Open(tiff_file)
    width=ds.RasterXSize
    height=ds.RasterYSize
    gt=ds.GetGeoTransform()
    minx=gt[0]
    miny=gt[3] + width*gt[4] + height*gt[5]
    maxx=gt[0] + width*gt[1] + height*gt[2]
    maxy=gt[3]
    ds=None
    return(miny, maxy, minx, maxx)


def get_palette():
    palette=_PALETTE
    img_palette=[0,0,0] + [item for sublist in palette for item in sublist[1]]
    return img_palette


def data_to_img(data, dim, img_filename):
    """Converts the nimrod data array to an 8-bit png file with a custom palette.

    """
    cols=dim[0]
    rows=dim[1]
    im=Image.fromarray(np.uint8(data.reshape(cols, rows)), 'P')
    png_palette=get_palette()
    im.putpalette(png_palette)
    im.save(img_filename, transparency=0)


def img_to_gtiff(nimrod, img_filename):
    """The original data array is in EPSG 27700. Each pixel represents 1000x1000m

    """
    tif_27700_filename=os.path.splitext(img_filename)[0] + '_epsg27700.tif'
    tif_filename = os.path.splitext(img_filename)[0] + '.tif'
    tif_filename = os.path.join(os.path.dirname(tif_filename), 'files',
                                os.path.basename(tif_filename))
    # the datum of the data array is the British National grid OSGB1936 == EPSG27700 (http://spatialreference.org/ref/epsg/27700/
    # The corner values are derived from the information in the nimrod header
    # see read_nimrod function:
    #     print "start northing %.1f, row interval %.1f, start easting %.1f, column interval %.1f\n"  %(gen_reals[2], gen_reals[3], gen_reals[4], gen_reals[5])
    # every pixel is 1000mx1000m in size and the array is 2175x1725 big
    translate_str = "-a_srs EPSG:27700 -a_ullr %i %i %i %i" % (nimrod['start_easting'],
                                                               nimrod['start_northing'],
                                                               nimrod['start_easting']+nimrod['rows']*nimrod['row_interval'],
                                                               nimrod['start_northing']-nimrod['cols']*nimrod['column_interval'])

    #Add projection/datum information to the img and output a gtiff-file
    cmd="""gdal_translate -q -of GTiff %s "%s" "%s" """ % (translate_str, img_filename, tif_27700_filename)
    proc=subprocess.Popen(cmd, shell=True)
    proc.wait()
    #reproject the just created tif-file to EPSG:4326, which is the projection google-earth needs
    cmd="""gdalwarp -q -t_srs EPSG:4326 -srcnodata 0 -dstalpha "%s" "%s" """ % (tif_27700_filename, tif_filename)
    proc=subprocess.Popen(cmd, shell=True)
    proc.wait()
    return tif_filename


def gtiff_to_kmz(kmz_filename, date):
    """convert geo-tiff file into kmz file. One large kml file is created
    which will contain a number of GroundOverlays

    """
    kml=_KML_HEADER % ('ukmo-rain-radar %s' % (date.strftime('%Y-%m-%d')))

    file_list=[os.path.join(_TEMP_FOLDER, 'files', f) for f in os.listdir(os.path.join(_TEMP_FOLDER, 'files'))]
    file_list.sort()
    for f in file_list:
        time_span_begin=datetime.datetime.strptime(os.path.basename(f).split('_')[2], '%Y%m%d%H%M') - datetime.timedelta(seconds=150)
        time_span_begin=time_span_begin.strftime('%Y-%m-%dT%H:%M:00Z')
        time_span_end=datetime.datetime.strptime(os.path.basename(f).split('_')[2], '%Y%m%d%H%M') + datetime.timedelta(seconds=150)
        time_span_end=time_span_end.strftime('%Y-%m-%dT%H:%M:00Z')
        time_stamp=datetime.datetime.strptime(os.path.basename(f).split('_')[2], '%Y%m%d%H%M').strftime('%Y-%m-%d %H:%M')
        miny, maxy, minx, maxx=calc_kmz_boundaries(f)
        kml += _KML_GROUNDOVERLAY % (time_span_begin,
                                     time_span_end,
                                     time_stamp,
                                     os.path.basename(f),
                                     miny, maxy, minx, maxx)
    kml += _KML_FOOTER
    f=open(os.path.join(_TEMP_FOLDER, 'doc.kml'), 'w')
    f.write(kml)
    f.close()
    cmd="""cd %s && zip -rq %s doc.kml files/ """ % (_TEMP_FOLDER, kmz_filename)
    proc=subprocess.Popen(cmd, shell=True)
    proc.wait()


def untar(tar_file):
    """
    extract all data files from the tar-file into a temporary directory.

    """
    cmd1="""tar xvf %s -C %s > /dev/null""" % (tar_file, _TEMP_FOLDER)
    cmd2="""gunzip -q %s/*gz""" % (_TEMP_FOLDER)
    proc=subprocess.Popen(cmd1, shell=True)
    proc.wait()
    proc=subprocess.Popen(cmd2, shell=True)
    proc.wait()


def scale_data(data):
    """
    Units of the nimrod data are mm/h*32.
    """
    palette=_PALETTE
    tmp=data
    for i in range(len(palette)):
        lthre=palette[i][0][0]
        uthre=palette[i][0][1]
        ix=np.where((data/32. > lthre) & (data/32. <= uthre))[0]
        tmp[ix]=i + 1
    return tmp


def create_kmz_filename(tar_file, outpath):
    """creates a kmz filename which contains location, resolution, and date
    """
    # TODO: Needs adjusting when the script is adapted to handle other data files than the 1km-UK-composite
    kmz_filename=os.path.join(outpath, 'ukmo-rain-radar_uk_1km_%s.kmz' % (os.path.basename(tar_file).split('_')[2]))
    date=datetime.datetime.strptime(os.path.basename(tar_file).split('_')[2], '%Y%m%d')
    return (kmz_filename, date)


def process(tar_file, outpath):
    untar(tar_file)
    data_file_list=os.listdir(_TEMP_FOLDER)
    data_file_list.sort()
    for d in data_file_list:
        if d.endswith('dat'):
            nimrod=read_nimrod(os.path.join(_TEMP_FOLDER, d))
            data=scale_data(nimrod['data'])
            #dimensions
            dim=(nimrod['cols'], nimrod['rows'])
            img_filename=os.path.join(_TEMP_FOLDER, os.path.splitext(d)[0]+'.png')
            data_to_img(data, dim, img_filename)
            img_to_gtiff(nimrod, img_filename)
    kmz_filename, date=create_kmz_filename(tar_file, outpath)
    gtiff_to_kmz(kmz_filename, date)
    sys.stdout.write('\nKMZ written to: %s \n' % (kmz_filename))


def _argparser():
    import argparse
    from argparse import RawTextHelpFormatter
    sys.argv.insert(0, 'faampy ge_nimrod_to_kmz')
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('rain_radar_tar_file', action="store", type=str, help='MetOffice compressed rain radar file')
    parser.add_argument('-o', '--outpath', action="store", type=str, required=False,
                        default=os.path.expanduser('~'),
                        help='Directory where the kmz file will be stored. Default: $HOME.')
    parser.add_argument('-k', '--keep-folder', action="store_true", required=False, default=False,
                        help='If option is set the temporary directory will *not* be deleted. Default: False')
    return parser


def main():
    global _TEMP_FOLDER, _NUM_PROCESSES
    _TEMP_FOLDER=tempfile.mkdtemp(dir=os.path.join(os.path.expanduser('~'), 'tmp'))
    if not os.path.exists(os.path.join(_TEMP_FOLDER, 'files')):
        os.mkdir(os.path.join(_TEMP_FOLDER, 'files'))
    parser = _argparser()
    args = parser.parse_args()
    # test that the input file is the 1km-composite
    if not args.rain_radar_tar_file.endswith('1km-composite.dat.gz.tar'):
        sys.stdout.write('Sorry, script currently only works with the UK 1km composite file. \nLeaving ... \n')
        sys.exit()
    start_time = time.time()
    process(args.rain_radar_tar_file, args.outpath)
    # clean_up behind ourselves
    if not args.keep_folder:
        sys.stdout.write('Deleting temporary folder %s ... \n' % (_TEMP_FOLDER))
        shutil.rmtree(_TEMP_FOLDER)
    else:
        sys.stdout.write('Keeping files in %s \n' % (_TEMP_FOLDER))
    sys.stdout.write('Processing time %i seconds ... \n' % (time.time()-start_time))
    sys.stdout.write('Leaving ... \n\n')


if __name__ == '__main__':
    main()
