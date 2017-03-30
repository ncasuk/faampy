#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
import imghdr

import faampy

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

# https://gist.githubusercontent.com/erans/983821/raw/a0fc31610ab044946387cef81ee3ff3b117ab0a6/get_lat_lon_exif_pil.py

def get_exif_data(image):
    """Returns a dictionary from the exif data of an PIL Image item. Also converts the GPS Tags"""
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]

                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value

    return exif_data

def _get_if_exist(data, key):
    if key in data:
        return data[key]
		
    return None
	
def _convert_to_degress(value):
    """Helper function to convert the GPS coordinates stored in the EXIF to degress in float format"""
    d0 = value[0][0]
    d1 = value[0][1]
    d = float(d0) / float(d1)

    m0 = value[1][0]
    m1 = value[1][1]
    m = float(m0) / float(m1)

    s0 = value[2][0]
    s1 = value[2][1]
    s = float(s0) / float(s1)

    return d + (m / 60.0) + (s / 3600.0)


def _convert_to_dms(deg, direction):
    m,s = divmod(deg*3600,60)
    d,m = divmod(m,60)
    #z = round(s, 2)
    if direction == 'NS':    
        if d >= 0:
            _dir = 'N'
        else:
            _dir = 'S'
    elif direction == 'EW':    
        if d >= 0:
            _dir = 'E'
        else:
            _dir = 'W'
    return "%id %i' %.2f\" %s" % (abs(d), abs(m), abs(s), _dir)
    
    
def get_lat_lon(exif_data):
    """Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)"""
    lat = None
    lon = None
    alt = None
    gps_datetime = None

    if "GPSInfo" in exif_data:		
        gps_info = exif_data["GPSInfo"]

        gps_latitude = _get_if_exist(gps_info, "GPSLatitude")
        gps_latitude_ref = _get_if_exist(gps_info, 'GPSLatitudeRef')
        gps_longitude = _get_if_exist(gps_info, 'GPSLongitude')
        gps_longitude_ref = _get_if_exist(gps_info, 'GPSLongitudeRef')
        gps_altitude = _get_if_exist(gps_info, 'GPSAltitude')
        if gps_altitude:
            alt = float(gps_altitude[0])/float(gps_altitude[1])
        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = _convert_to_degress(gps_latitude)
            if gps_latitude_ref != "N":                     
                lat = 0 - lat

            lon = _convert_to_degress(gps_longitude)
            if gps_longitude_ref != "E":
                lon = 0 - lon
        DateTime = gps_info['GPSDateStamp']+'T'+':'.join(['%i' % i[0] for i in gps_info['GPSTimeStamp']])
        gps_datetime = dt.datetime.strptime(DateTime, '%Y:%m:%dT%H:%M:%S')

    return (lat, lon, alt, gps_datetime)


def process(path):
    kml = simplekml.Kml()
    iconfilename = os.path.join(os.path.dirname(os.path.realpath(faampy.__file__)), 
                       '..', 'files', 'icons', 'camera_32x32.png')
    iconpath = kml.addfile(iconfilename)
    for (dirpath, dirnames, filenames) in os.walk(path):
        for filename in sorted(filenames):
            fullpath = os.path.join(dirpath, filename)
            _type = imghdr.what(fullpath)
            if _type != 'jpeg':
                continue
            img = Image.open(fullpath)
            exif_data = get_exif_data(img)
            img.close()
            Lat, Long, Alt, DT = get_lat_lon(exif_data)
            sys.stdout.write('%s: Lat: %s, Long: %s, Alt: %s\n' % (fullpath, Lat, Long, Alt))
            if Lat:
                x, y = Lat, Long
                point = kml.newpoint(name=filename, coords=[(y,x)])
                picpath = kml.addfile(fullpath)
                #print picpath
                fn = 'files/'+ os.path.splitext(filename)[0] + '.jpg' #Note: will not work if .JPG is used, must be lower case.
                balstylestring = ''
                balstylestring += "<![CDATA[<p><b>Date:</b> " + DT.strftime('%d-%m-%Y')
                balstylestring += ' <b>Time:</b> ' + DT.strftime("%H:%M:%S UTC")
                balstylestring += ' <p><b>Lon:</b> ' + _convert_to_dms(x, 'EW') + ' <b>Lat:</b> ' + _convert_to_dms(y, 'NS') + ' <b>Alt:</b> ' + str(int(Alt))+ 'm'
                balstylestring += '</p> <table width="500" cellpadding="0" cellspacing="0">  <tbody><tr><td><img width="100%" src="' + fn + '"></td></tr></tbody></table>]]>'
                point.style.balloonstyle.text = balstylestring
                point.style.iconstyle.icon.href = 'files/camera_32x32.png'
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
    kml.savekmz(args.outfile, format=True)
    sys.stdout.write('Created ... %s. \n' % args.outfile)


if __name__ == '__main__':
    main()
