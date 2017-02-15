#!/usr/bin/env python

"""
Photo album creator for google-earth from georeferenced photos.
Script produces  a kmz files for google-earth with all the photos
in the input folder. The images need to contain GPS location information.
This kind of information can be added to the image files using a tool
like gpscorrelate and a gpx file which contains the track of the flight.

"""

import os
import simplekml
import sys
import datetime as dt
import exifread as pex
import shutil
import tempfile

import faampy


def GetLatLong(fn):
    """
    Extract geoinformation (lon, lat, alt) from jpg image.

    :param string fn: image filename
    """
    metadata = pex.ImageMetadata(fn)
    metadata.read()
    Lat = metadata['Exif.GPSInfo.GPSLatitude'].human_value
    if metadata['Exif.GPSInfo.GPSLatitudeRef'].human_value == 'South':
        Lat = '-' + Lat
    Long = metadata['Exif.GPSInfo.GPSLongitude'].human_value
    if metadata['Exif.GPSInfo.GPSLongitudeRef'].human_value == 'West':
        Long = '-' + Long
    Alt = metadata['Exif.GPSInfo.GPSAltitude'].human_value

    # DateTime = metadata['Exif.Image.DateTime'].human_value #string
    if 'Exif.GPSInfo.DateStamp' in metadata.keys():
        DateTime = '%s %s' % (metadata['Exif.GPSInfo.DateStamp'].human_value,
                              metadata['Exif.GPSInfo.TimeStamp'].human_value)
    elif 'Exif.GPSInfo.GPSDateStamp' in metadata.keys():
        DateTime = '%s %s' % (metadata['Exif.GPSInfo.GPSDateStamp'].human_value,
                              metadata['Exif.GPSInfo.GPSTimeStamp'].human_value)
    else:
        pass

    DT = dt.datetime.strptime(DateTime, '%Y:%m:%d %H:%M:%S')  # Datetime object
    return (Lat, Long, Alt, DT)


def FormatLatLong(LatLongString):
    """
    Converts string to float

    """
    print(LatLongString)
    d = LatLongString.find('deg')
    Degrees = float(LatLongString[:d])
    m = LatLongString.find("'")
    Minutes = float(LatLongString[d+4:m])
    s = LatLongString.find('"')
    Seconds = float(LatLongString[m+2:s])
    decCoords = abs(Degrees) + Minutes/60.0 + Seconds/3600.0
    if Degrees < 0:
        decCoords = decCoords * -1
    return decCoords


def create_camera_icon():
    tmpdir = tempfile.mkdtemp()
    iconfilename = os.path.join(tmpdir, 'camera_32x32.png')
    #icon_path = os.path.join(_KMZ_TMP_DIRECTORY, 'icons')
    #os.mkdir(icon_path)
    src = os.path.join(faampy.__path___, 'files', 'icons',
                       'camera_32x32.png')
    shutil.copy(src, iconfilename)
    return iconfilename


def process(path):
    kml = simplekml.Kml()
    iconfilename = create_camera_icon()
    iconpath = kml.addfile(iconfilename)
    for (dirpath, dirnames, filenames) in os.walk(path):
        for filename in sorted(filenames):
            fullpath = os.path.join(dirpath, filename)
            try:
                Lat, Long, Alt, DT = GetLatLong(fullpath)
            except:
                Lat, Long, Alt, DT = (None, None, None, None)
            print '%s: Lat: %s, Long: %s, Alt: %s' % (fullpath, Lat, Long, Alt)
            if Lat:
                try:
                    x, y = (FormatLatLong(Lat), FormatLatLong(Long))
                except:
                    continue
                if x < 0:
                    Lat = Lat.strip('-') + 'S'
                else:
                    Lat = Lat + 'N'
                if y < 0:
                    Long = Long.strip('-') + 'W'
                else:
                    Long = Long + 'E'
                point = kml.newpoint(name=filename, coords=[(y,x)])
                picpath = kml.addfile(fullpath)
                print picpath
                fn = 'files/'+ os.path.splitext(filename)[0] + '.jpg' #Note: will not work if .JPG is used, must be lower case.
                balstylestring = ''
                balstylestring += "<![CDATA[<p><b>Date:</b> " + DT.strftime('%d-%m-%Y')
                balstylestring += ' <b>Time:</b> ' + DT.strftime("%H:%M:%S UTC")
                balstylestring += ' <p><b>Lon:</b> ' + Long + ' <b>Lat:</b> ' + Lat + ' <b>Alt:</b> ' + Alt
                balstylestring += '</p> <table width="500" cellpadding="0" cellspacing="0">  <tbody><tr><td><img width="100%" src="' + fn + '"></td></tr></tbody></table>]]>'
                point.style.balloonstyle.text = balstylestring
                point.style.iconstyle.icon.href='files/camera_icon_32x32.png'

    return kml


def _argparser():
    import argparse
    sys.argv.insert(0, 'faampy ge_photo_album')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', action="store", type=str,
                        help='directory which holds the photographs. All photographs in the directory will be added to the photo album.')
    parser.add_argument('outfile',
                        action="store",
                        type=str,
                        help='outfile name')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()
    kml = process(args.path)
    kml.savekmz(args.outfile, format=False)
    sys.stdout.write('Created ... %s. \n' % args.outfile)


if __name__ == '__main__':
    main()
