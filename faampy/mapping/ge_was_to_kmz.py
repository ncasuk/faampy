#!/usr/bin/python

'''
WAS log as google-earth overlay. Filling times are represented
as lines showing the location of the bottle fill.

'''

import netCDF4
import numpy as np
import os
import re
import sys
import shutil
import tempfile
import zipfile

import faampy

_KML_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengi
s.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">

<Folder>
<Style id="was">
  <IconStyle>
    <Icon>
      <href>icons/was_bottle_32x32.png</href>
    </Icon>
  </IconStyle>
  <LineStyle>
    <color>#ff0000ff</color>
    <width>8</width>
  </LineStyle>
</Style>

    <name>%s</name>
        <open>0</open>
"""

_KML_FOOTER = """</Folder>
</kml>"""

_KML_WAS_BOTTLE = """<Placemark>
  <name>%s@%i m</name>
  <description>
     %s to %s@%im
  </description>
  <styleUrl>#was</styleUrl>
  <MultiGeometry>
  <Point>
  <altitudeMode>absolute</altitudeMode>
      <coordinates>
        %8.4f,%8.4f,%8.2f
      </coordinates>
    </Point>
    <LineString>
      <altitudeMode>absolute</altitudeMode>
      <coordinates>
      %s
      </coordinates>
    </LineString>
   </MultiGeometry>
   </Placemark>
"""

# global variables
_KMZ_TMP_DIRECTORY = tempfile.mkdtemp()
_FID = ''

def __zip__(outfile):
    files4zipping = []
    for root, subFolders, files in os.walk(_KMZ_TMP_DIRECTORY):
        for f in files:
            files4zipping.append(os.path.join(root,f))
    zip = zipfile.ZipFile(outfile, mode='w')
    for file in files4zipping:
        zipname = file[len(_KMZ_TMP_DIRECTORY) + (len(os.sep)):]
        zip.write(file, zipname)
    return


def __setup_kmz__():
    icon_path = os.path.join(_KMZ_TMP_DIRECTORY, 'icons')
    os.mkdir(icon_path)
    icon_file = os.path.join(os.path.dirname(faampy.__file__),
                             '..', 'files', 'icons',
                             'was_bottle_32x32.png')
    shutil.copy(icon_file, icon_path)


def t2s(s):
    s = s.split(':')
    result = int(s[0]) * 3600 + int(s[1]) * 60 + int(s[2])
    return result


def get_index(ds, secs):
    ix = np.where(ds.variables['Time'][:] == secs)
    return ix[0]


def read_was_log(was_log_file):
    result = []
    f = open(was_log_file, 'r')
    lines = f.readlines()
    f.close()
    for line in lines:
        if (line.strip()[0]).isdigit():
            result.append(str.split(line))
    return result


def parse_was_log(was_log_file, ds):
    was_log_lines = read_was_log(was_log_file)
    plcmark_txt = ""
    for was in was_log_lines:
        if not was:
            continue
        # get coordinates for bottle start
        s_secs = t2s(was[1])
        s_ix = int(get_index(ds, s_secs))
        e_secs = t2s(was[2])
        e_ix = int(get_index(ds, e_secs))
        if len(ds.variables['ALT_GIN'][:].shape) == 2:
            s_lon = ds.variables['LON_GIN'][:][s_ix, 0]
            s_lat = ds.variables['LAT_GIN'][:][s_ix, 0]
            s_alt = ds.variables['ALT_GIN'][:][s_ix, 0]
            # get coordinates for bottle end
            e_lon = ds.variables['LON_GIN'][:][e_ix, 0]
            e_lat = ds.variables['LAT_GIN'][:][e_ix, 0]
            e_alt = ds.variables['ALT_GIN'][:][e_ix, 0]
        else:
            s_lon = ds.variables['LON_GIN'][:][s_ix]
            s_lat = ds.variables['LAT_GIN'][:][s_ix]
            s_alt = ds.variables['ALT_GIN'][:][s_ix]
            # get coordinates for bottle end
            e_lon = ds.variables['LON_GIN'][:][e_ix]
            e_lat = ds.variables['LAT_GIN'][:][e_ix]
            e_alt = ds.variables['ALT_GIN'][:][e_ix]

        linstring_txt = "%f,%f,%f\n%f,%f,%f" % (s_lon, s_lat, s_alt,
                                                e_lon, e_lat, e_alt)
        plcmark_txt += _KML_WAS_BOTTLE % (_FID+': ' +was[0], s_alt, was[1], was[2], s_alt, s_lon, s_lat, s_alt, linstring_txt)
    return plcmark_txt


def process(was_log_file, ncfile, outpath):
    global _FID

    __setup_kmz__()
    _FID = re.search('[b,B]\d{3}', ncfile).group()
    ds = netCDF4.Dataset(ncfile, 'r')
    if hasattr(ds, 'title'):
        flight_desc = str(ds.title).split()[2] + '-' + str(ds.title).split()[4] + '-WAS-Bottles'
    elif hasattr(ds, 'Title'):
        flight_desc = str(ds.Title).split()[2] + '-' + str(ds.Title).split()[4] + '-WAS-Bottles'
    else:
        flight_desc = ''
    was_kml = open(os.path.join(_KMZ_TMP_DIRECTORY, 'doc.kml'), 'w')
    plcmark_txt = parse_was_log(was_log_file, ds)
    ds.close()
    was_kml.write(_KML_HEADER % (flight_desc))
    was_kml.write(plcmark_txt)
    was_kml.write(_KML_FOOTER)
    was_kml.close()
    __zip__(os.path.join(outpath, 'faam-was_%s.kmz' % _FID))


def __get_ncfile__(path, fid):
    pattern = '.*core_faam.*%s_.*.nc' % str.lower(fid)
    for root, subFolders, files in os.walk(path):
        for f in files:
            if re.match(pattern, f):
                return os.path.join(root, f)


def _argparser():
    import argparse
    sys.argv.insert(0, 'faampy ge_was_to_kmz')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('was_log_file', action="store", type=str,
                        help='Input WAS log file or folder which contains log files.')
    parser.add_argument('ncfile', action="store", type=str,
                       help='input netCDF-file or path to netcdf files.')
    parser.add_argument('outpath', action="store", type=str,
                        help='outpath for kmz file')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()    
    if os.path.isdir(args.was_log_file):
        tmp = os.listdir(args.was_log_file)
        new_list = []
        for t in tmp:
            if re.match('[b,B]\d{3}.WAS', t):
                new_list.append(os.path.join(args.was_log_file, t))
        args.was_log_file = new_list
    else:
        args.was_log_file = [args.was_log_file, ]

    for was_log_file in args.was_log_file:
        if os.path.isdir(args.ncfile):
            ncfile = __get_ncfile__(args.ncfile, os.path.basename(os.path.splitext(was_log_file)[0]))
        else:
            ncfile = args.ncfile
        try:
            process(was_log_file, ncfile, args.outpath)
        except:
            sys.stdout.write('Problem processing ... %s\n' % (os.path.basename(was_log_file)))


if __name__ == '__main__':
    main()
