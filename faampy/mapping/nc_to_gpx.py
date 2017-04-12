#!/usr/bin/env python

"""
Creates a gpx file from a FAAM core netcdf data file.

GPX files are a standard xml-format, which is understood by many programs.
The gpx file from a flight can for example be used to georeference photographs
taken during a flight.

see: https://github.com/freefoote/gpscorrelate

The geotagged images can then in a next step be overlaid on maps using the
LonLat information from the file header.

"""

import datetime
import netCDF4
import os
import sys

from matplotlib.dates import num2date

from faampy.core.utils import get_mpl_time, get_base_time, get_fid

_TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

_GPX_HEADER = """<?xml version="1.0"?>
<gpx
 version="1.0"
 creator="ExpertGPS 1.1 - http://www.topografix.com"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xmlns="http://www.topografix.com/GPX/1/0"
 xsi:schemaLocation="http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd">
"""

_GPX_FOOTER = "</gpx>\n"

_GPX_RTE_TEMPLATE = "<rte>%s</rte>\n"

_GPX_RTEPT_TEMPLATE = """<rtept lat="%f" lon="%f">
 <ele>%f</ele>
 <time>%s</time>
</rtept>
"""

_GPX_TRK_TEMPLATE_START = "<trk><trkseg>\n"
_GPX_TRK_TEMPLATE_END = "</trkseg></trk>\n"

_GPX_TRKPT_TEMPLATE = """<trkpt lat="%f" lon="%f">
 <ele>%f</ele>
 <time>%s</time>
</trkpt>
"""


def lonlatalt_to_gpx(lon, lat, alt, *args):
    if args:
        timestamp = [t.strftime(_TIMESTAMP_FORMAT) for t in args[0]]
    else:
        now = datetime.datetime.utcnow()
        timestamp = [(now+datetime.timedelta(seconds=i)).strftime(_TIMESTAMP_FORMAT) for i in range(len(lon))]
    result = ""
    result += _GPX_HEADER
    result += _GPX_TRK_TEMPLATE_START
    trkp = [_GPX_TRKPT_TEMPLATE % (lat[i], lon[i], alt[i], timestamp[i]) for i in range(len(lat))]
    result += ''.join(trkp)
    result += _GPX_TRK_TEMPLATE_END
    result += _GPX_FOOTER
    return result


def nc_to_gpx(ncfile, outpath):
    ds = netCDF4.Dataset(ncfile, 'r')
    lon = ds.variables['LON_GIN'][:, 0]
    lat = ds.variables['LAT_GIN'][:, 0]
    alt = ds.variables['ALT_GIN'][:, 0]
    t = num2date(get_mpl_time(ds))

    outfilename = '%s_%s.gpx' % (get_fid(ds), get_base_time(ds).strftime('%Y%m%d'))
    outfile = os.path.join(outpath, outfilename)
    outtxt = lonlatalt_to_gpx(lon, lat, alt, t)
    f = open(outfile, 'w')
    f.write(outtxt)
    ds.close()
    f.close()


def _argparser():
    import argparse
    from argparse import RawTextHelpFormatter
    sys.argv.insert(0, 'faampy nc_to_gpx')
    parser = argparse.ArgumentParser(prog = 'faampy nc_to_gpx', description=__doc__,
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('ncfile',
                        action="store",
                        type=str,
                        help='input netCDF-file')
    parser.add_argument('outpath',
                        action="store",
                        nargs='?',
                        type=str,
                        default=os.environ['HOME'],
                        help='file name of output file')
    return parser
  
def main():
    parser = _argparser()
    args = parser.parse_args()
    nc_to_gpx(args.ncfile, args.outpath)


if __name__ == '__main__':
    main()
