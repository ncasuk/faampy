#!/usr/bin/python

"""
Lidar curtain kmz creator for google-earth

"""

import datetime
import math
import netCDF4
import numpy as np
import os
import pandas as pd
import re
import shutil
import sys
import tempfile

import matplotlib.pyplot as plt

##################################################################################
"""
    Python implementation of Haversine formula
    Copyright (C) <2009>    Bartek Grony, Mobitel Monitoring sp. z o.o. <bartek@gorny.edu.pl>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.    If not, see <http://www.gnu.org/licenses/>.
"""



def recalculate_coordinate(val, _as=None):
    """
    Accepts a coordinate as a tuple (degree, minutes, seconds)
    You can give only one of them (e.g. only minutes as a floating point number) and it will be duly
    recalculated into degrees, minutes and seconds.
    Return value can be specified as 'deg', 'min' or 'sec'; default return value is a proper coordinate tuple.

    :param tuple val: coordinate as tuple (degree, minutes, seconds)
    """
    deg, min, sec = val
    # pass outstanding values from right to left
    min = (min or 0) + int(sec) / 60
    sec = sec % 60
    deg = (deg or 0) + int(min) / 60
    min = min % 60
    # pass decimal part from left to right
    dfrac, dint = math.modf(deg)
    min = min + dfrac * 60
    deg = dint
    mfrac, mint = math.modf(min)
    sec = sec + mfrac * 60
    min = mint
    if _as:
        sec = sec + min * 60 + deg * 3600
        if _as == 'sec': return sec
        if _as == 'min': return sec / 60
        if _as == 'deg': return sec / 3600
    return deg, min, sec


def points2distance(start, end):
    """
        Calculate distance (in kilometers) between two points given as (long, latt) pairs
        based on Haversine formula (http://en.wikipedia.org/wiki/Haversine_formula).
        Implementation inspired by JavaScript implementation from http://www.movable-type.co.uk/scripts/latlong.html
        Accepts coordinates as tuples (deg, min, sec), but coordinates can be given in any form - e.g.
        can specify only minutes:
        (0, 3133.9333, 0)
        is interpreted as
        (52.0, 13.0, 55.998000000008687)
        which, not accidentally, is the lattitude of Warsaw, Poland.
    """
    start_long = math.radians(recalculate_coordinate(start[0], 'deg'))
    start_latt = math.radians(recalculate_coordinate(start[1], 'deg'))
    end_long = math.radians(recalculate_coordinate(end[0], 'deg'))
    end_latt = math.radians(recalculate_coordinate(end[1], 'deg'))
    d_latt = end_latt - start_latt
    d_long = end_long - start_long
    a = math.sin(d_latt/2)**2 + math.cos(start_latt) * math.cos(end_latt) * math.sin(d_long/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    #return 6371 * c
    return 6378.137 * c
#################################################################



KML_HEADER_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"
xmlns:gx="http://www.google.com/kml/ext/2.2"
xmlns:kml="http://www.opengis.net/kml/2.2"
xmlns:atom="http://www.w3.org/2005/Atom">"""

KML_FOLDER_EXPANDABLE_START_TEMPLATE = """<Folder><name>%s</name><open>0</open>"""

KML_FOLDER_START_TEMPLATE = """<Folder><name>%s</name><open>0</open>
<Style><ListStyle><listItemType>checkHideChildren</listItemType><bgColor>00ffffff</bgColor><maxSnippetLines>2</maxSnippetLines></ListStyle></Style>"""
KML_FOLDER_END_TEMPLATE = """</Folder>"""

#Input: lon, lat, curtain_ref, img_ref, img_ref
KML_PLACEMARK_TEMPLATE = """<Placemark>
<name>%s</name>
<Style id="default"></Style>
<Model id="curtain_model_N">
<altitudeMode>absolute</altitudeMode>
<Location>
<longitude>%.2f</longitude>
<latitude>%.2f</latitude>
<altitude>0</altitude>
</Location>
<Orientation>
<heading>%.2f</heading>
<tilt>0</tilt>
<roll>0</roll>
</Orientation>
<Scale>
<x>1</x>
<y>1</y>
<z>1</z>
</Scale>
<Link>
<href>files/%s</href>
</Link>
<ResourceMap>
<Alias>
<targetHref>%s</targetHref>
<sourceHref>../images/%s</sourceHref>
</Alias>
</ResourceMap>
</Model>
</Placemark>
"""

KML_FOOTER_TEMPLATE = """</kml>"""

DAE_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema"
version="1.4.1">
<asset>
<contributor>
<authoring_tool>Google SketchUp 6.0.312</authoring_tool>
</contributor>
<unit name="meters" meter="1.0" />
<up_axis>Z_UP</up_axis>
</asset>
<library_images>
<image id="kdm-kml_curtain-image" name="kdm-kml_curtain-image">
<init_from>../images/%s</init_from>
</image>
</library_images>
<library_materials>
<material id="kdm-kml_curtainID" name="kdm-kml_curtain">
<instance_effect url="#kdm-kml_curtain-effect" />
</material>
</library_materials>
<library_effects>
<effect id="kdm-kml_curtain-effect" name="kdm-kml_curtain-effect">
<profile_COMMON>
<newparam sid="kdm-kml_curtain-image-surface">
<surface type="2D">
<init_from>kdm-kml_curtain-image</init_from>
</surface>
</newparam>
<newparam sid="kdm-kml_curtain-image-sampler">
<sampler2D>
<source>kdm-kml_curtain-image-surface</source>
</sampler2D>
</newparam>
<technique sid="COMMON">
<phong>
<emission>
<color>0.000000 0.000000 0.000000 1</color>
</emission>
<ambient>
<color>0.000000 0.000000 0.000000 1</color>
</ambient>
<diffuse>
<texture texture="kdm-kml_curtain-image-sampler"
texcoord="UVSET0" />
</diffuse>
<specular>
<color>0.000000 0.000000 0.000000 1</color>
</specular>
<shininess>
<float>20.000000</float>
</shininess>
<reflectivity>
<float>0.100000</float>
</reflectivity>
<transparent>
<color>1 1 1 1</color>
</transparent>
<transparency>
<float>0.000000</float>
</transparency>
</phong>
</technique>
</profile_COMMON>
</effect>
</library_effects>
<library_geometries>
<geometry id="mesh1-geometry" name="mesh1-geometry">
<mesh>
<source id="mesh1-geometry-position">
<!-- 1: -Width,Left,Bottom. 3: Width,Right,Bottom. 6:Width,Top,Left 8/11: Height. 9:Width,Top,Left -->
<!--                                                       0 1 2 3     4 5 6     7 8   9   10 11         -->
<!--
                       <float_array id="mesh1-geometry-position-array" count="12">0 0 0 109.5 0 0 -20.5 0 300 112 0 300</float_array>
                       <float_array id="mesh1-geometry-position-array" count="12">0 0 0 100 0 0 0 0 100 100 0 100</float_array>
                       <float_array id="mesh1-geometry-position-array" count="12">-50 0 0 50  0 0 -50 0 100 50 0 100</float_array>
                       <float_array id="mesh1-geometry-position-array" count="12">-50 0 0 50  0 0 -50 0 100 50 0 100</float_array>
                       <float_array id="mesh1-geometry-position-array" count="12">-0.5 0 0 0.5  0 0 -0.5 0 1 0.5 0  1</float_array>
                                   -->
<!--                                                       0    1 2 3     4 5 6    7 8    9    10 11         -->
<float_array id="mesh1-geometry-position-array" count="12">
%s
</float_array>
<technique_common>
<accessor source="#mesh1-geometry-position-array" count="4"
stride="3">
<param name="X" type="float" />
<param name="Y" type="float" />
<param name="Z" type="float" />
</accessor>
</technique_common>
</source>
<source id="mesh1-geometry-normal">
<float_array id="mesh1-geometry-normal-array" count="6">0 -0.0254 0
0 0.0254 0</float_array>
<technique_common>
<accessor source="#mesh1-geometry-normal-array" count="2"
stride="3">
<param name="X" type="float" />
<param name="Y" type="float" />
<param name="Z" type="float" />
</accessor>
</technique_common>
</source>
<source id="mesh1-geometry-uv">
<float_array id="mesh1-geometry-uv-array" count="8">0 0 1 0 0 1 1
1</float_array>
<technique_common>
<accessor source="#mesh1-geometry-uv-array" count="4" stride="2">
<param name="S" type="float" />
<param name="T" type="float" />
</accessor>
</technique_common>
</source>
<vertices id="mesh1-geometry-vertex">
<input semantic="POSITION" source="#mesh1-geometry-position" />
</vertices>
<triangles material="kdm-kml_curtain" count="4">
<input semantic="VERTEX" source="#mesh1-geometry-vertex"
offset="0" />
<input semantic="NORMAL" source="#mesh1-geometry-normal"
offset="1" />
<input semantic="TEXCOORD" source="#mesh1-geometry-uv" offset="2"
set="0" />
<p>0 0 0 1 0 1 2 0 2 0 1 0 2 1 2 1 1 1 3 0 3 2 0 2 1 0 1 3 1 3 1 1
1 2 1 2</p>
</triangles>
</mesh>
</geometry>
</library_geometries>
<library_visual_scenes>
<visual_scene id="SketchUpScene" name="SketchUpScene">
<node id="Model" name="Model">
<node id="mesh1" name="mesh1">
<instance_geometry url="#mesh1-geometry">
<bind_material>
<technique_common>
<instance_material symbol="kdm-kml_curtain"
target="#kdm-kml_curtainID">
<bind_vertex_input semantic="UVSET0" input_semantic="TEXCOORD"
input_set="0" />
</instance_material>
</technique_common>
</bind_material>
</instance_geometry>
</node>
</node>
</visual_scene>
</library_visual_scenes>
<scene>
<instance_visual_scene url="#SketchUpScene" />
</scene>
</COLLADA>
"""

#<!-- 1: -Width,Left,Bottom.
#3: Width,Right,Bottom.
#6:Width,Top,Left
#8/11: Height.
#9:Width,Top,Left -->
DAE_VALUES_TEMPLATE = """0.0 0 0
%.1f 0 0
0.0 0 %.1f
%.1f 0 %.1f
"""


def get_data(lidar_datafile):
    """
    Getting lidar data from netcdf and store those in a dictionary. Signals
    are filtered using thresholds derived by percentile.

    """
    ids = netCDF4.Dataset(lidar_datafile)

    l_ds = {}
    l_ds['Time'] = netCDF4.num2date(ids.variables['Time'][:], ids.variables['Time'].units)
    l_ds['Longitude'] = ids.variables['Longitude'][:]
    l_ds['Latitude'] = ids.variables['Latitude'][:]
    l_ds['Altitude'] = ids.variables['Altitude'][:]
    l_ds['rangeCorrected_0'] = ids.variables['rangeCorrected_0'][:]
    l_ds['rangeCorrected_1'] = ids.variables['rangeCorrected_1'][:]

    for var in ['rangeCorrected_0', 'rangeCorrected_1']:
        _perc_05 = np.percentile(l_ds[var], 2)
        _perc_95 = np.percentile(l_ds[var], 98)
        l_ds[var][l_ds[var] < _perc_05] = np.nan
        l_ds[var][l_ds[var] > _perc_95] = np.nan
    return l_ds


def convert_bearing(hdg):
    """Heading value conversion."""
    #hdg is strange:
    #0 = East, 45 = SE, 90 = South, 180 = West
    result = hdg - 90.0
    if result < 0:
        result = result + 360.0
    return result


def get_run_bearing(ldata_run):
    """inspired by
    http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points

    """
    lon1 = float(ldata_run['Longitude'][:][0])
    lon2 = float(ldata_run['Longitude'][:][-1])
    lat1 = float(ldata_run['Latitude'][:][0])
    lat2 = float(ldata_run['Latitude'][:][-1])
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    Base = 6371 * c
    dLon = lon2 - lon1
    y = math.sin(dLon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360.0) % 360.0
    return bearing


# TODO: Use the faampy flight summary module instead
def parse_flightsummary(flight_summary_file):
    """
    Get runs and its start and end time
    from flight summary.

    """
    result = []
    f = open(flight_summary_file, 'r')
    lines = f.readlines()
    f.close()
    for line in lines:
        if line.lower().startswith('date:'):
            basetime = datetime.datetime.strptime(line.split(':')[1].strip(),
                                                  '%d/%m/%Y')
        if 'run' in str.lower(line[17:28]):
            try:
                name = str.strip(line[17:28])
                stime = line[0:6]
                etime = line[8:14]
                #if run is shorter than 5min we don't bother
                if time2secs(etime)-time2secs(stime) > 300:
                    result.append((name,
                                   basetime+datetime.timedelta(seconds=time2secs(stime)),
                                   basetime+datetime.timedelta(seconds=time2secs(etime))))
            except:
                pass
    return result


# TODO: replace the local routine with the faampy.util one
def time2secs(time_string):
    """
    converts time string of the format HHMMSS into seconds past midnight

    :param time string: HHMMSS

    """
    time_string = str.strip(time_string)
    result = float(time_string[0:2])*3600.+ \
             float(time_string[2:4])*60+ \
             float(time_string[4:6])
    return result


def extract_run_data(ldata, var, start_time=None, end_time=None, start_index=None, end_index=None):
    """
    Extracts data
    :param start_time: datetime.datetime object
    :param end_time: datetime.datetime object
    :param start_index:
    :param end_index
    """
    if (start_time and end_time):
        lidar_time = ldata['Time']
        s_ind = np.where(lidar_time > pd.Timestamp(start_time))[0][0]
        e_ind = np.where(lidar_time < pd.Timestamp(end_time))[0][-1]
    else:
        s_ind = start_index
        e_ind = end_index
    run_data = {}
    run_data['Time'] = ldata['Time'][s_ind:e_ind]
    run_data['Longitude'] = ldata['Longitude'][s_ind:e_ind]
    run_data['Latitude'] = ldata['Latitude'][s_ind:e_ind]
    run_data['Altitude'] = ldata['Altitude']
    run_data['rangeCorrected_0'] = np.array(ldata['rangeCorrected_0'][:,s_ind:e_ind])
    run_data['rangeCorrected_1'] = np.array(ldata['rangeCorrected_1'][:,s_ind:e_ind])
    return run_data


def get_run_length(ldata_run):
    """
    :return float run_length: run length in meters
    """
    lon1 = float(ldata_run['Longitude'][:][0])
    lon2 = float(ldata_run['Longitude'][:][-1])
    lat1 = float(ldata_run['Latitude'][:][0])
    lat2 = float(ldata_run['Latitude'][:][-1])
    run_length = points2distance(((lon1, 0, 0), (lat1, 0, 0)), ((lon2, 0, 0), (lat2, 0, 0)))
    return run_length * 1000. #convert to meters


def get_run_start_coordinates(ldata_run):
    """
    :return tuple coords: start coordinates (lon, lat) of Lidar run
    """
    lon = ldata_run['Longitude'][0]
    lat = ldata_run['Latitude'][0]
    return (lon, lat)


def lidar_plot(ds, var, step, img_filename):
    """
    Plot lidar profile as heatmap.

    """
    colormap = plt.get_cmap('jet')

    x = ds['Time'][::step]
    y = ds['Altitude'][:]
    z = ds[var][:,::step]
    plt.contourf(x, y, z, colormap=colormap)
    plt.xlim(x.min(), x.max())
    plt.ylim(0, 10000)
    figure = plt.figure(1, (10, 8), 80)
    # remove any margins
    plt.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
    figure.savefig(img_filename)
    plt.close()


def process(lidar_file, flight_summary_file, step=10, alt_scale_factor=5, outpath=None):

    fid = re.findall('_[BbCc]\d{3}_', lidar_file)[0][1:-1].lower()

    # set up temporary directory structure where all the data for the kmz
    # will be stored
    ROOT_TMP_PATH = tempfile.mktemp()
    os.mkdir(ROOT_TMP_PATH)
    # create temporary folders for the images and dae files
    os.mkdir(os.path.join(ROOT_TMP_PATH, 'files'))
    os.mkdir(os.path.join(ROOT_TMP_PATH, 'images'))

    ds = get_data(lidar_file)

    kml_doc = ''   # empty kml document
    img_cnt = 0
    kml_doc += KML_HEADER_TEMPLATE
    kml_doc += KML_FOLDER_EXPANDABLE_START_TEMPLATE % (fid + ' Lidar ')
    event_cnt = 0

    fltsumm = parse_flightsummary(flight_summary_file)

    for var in ['rangeCorrected_0', 'rangeCorrected_1']:
        kml_doc += KML_FOLDER_START_TEMPLATE % (var)
        for event_cnt in range(len(fltsumm)):
            run_data = extract_run_data(ds,
                                        var,
                                        start_time=fltsumm[event_cnt][1],
                                        end_time=fltsumm[event_cnt][2])


            kml_doc += KML_FOLDER_START_TEMPLATE % (fltsumm[event_cnt][0])
            max_length = 300
            # Individual sections should not be longer than 300 seconds. So we
            # split them up if they are
            for i in range(0, len(run_data['Time']), max_length):
                data =  extract_run_data(run_data, var, start_index=i, end_index=i+max_length)
                img_name = os.path.join(ROOT_TMP_PATH, 'images', 'lidar_%.4i.png' % img_cnt)
                lidar_plot(data, var, step, img_name)
                slon, slat = get_run_start_coordinates(data)
                run_bearing = get_run_bearing(data)
                run_bearing = convert_bearing(run_bearing)
                kml_doc += KML_PLACEMARK_TEMPLATE % (img_name, slon, slat, run_bearing, 'curtain_%.4i.dae' % img_cnt,
                                                     img_name, img_name)
                run_length = get_run_length(data)
                run_altitude = 10000.0 * alt_scale_factor
                # print(slon, slat, run_bearing, run_length, run_altitude)
                dae_values = DAE_VALUES_TEMPLATE % (run_length, run_altitude, run_length, run_altitude)

                f = open(os.path.join(ROOT_TMP_PATH, 'files', 'curtain_%.4i.dae' % img_cnt), 'w')
                f.write(DAE_TEMPLATE % (os.path.basename(img_name), dae_values))
                f.close()
                img_cnt += 1
            kml_doc += KML_FOLDER_END_TEMPLATE
        kml_doc  += KML_FOLDER_END_TEMPLATE

    kml_doc += KML_FOLDER_END_TEMPLATE
    kml_doc += KML_FOOTER_TEMPLATE

    f = open(os.path.join(ROOT_TMP_PATH, 'doc.kml'), 'w')
    f.write(kml_doc)
    f.close()
    # print(ROOT_TMP_PATH)
    kmz_filename = os.path.join(outpath, '%s_lidar_curtain.kmz' % (fid))
    sys.stdout.write('File written to: %s' % (kmz_filename))
    shutil.make_archive(kmz_filename, 'zip', ROOT_TMP_PATH)
    shutil.move(kmz_filename+'.zip', kmz_filename)



def _argparser():
    import argparse
    if not __name__ == '__main__':
        sys.argv.insert(0, 'faampy ge_lidar_curtain')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lidar_file', action="store", type=str,
                        help='metoffice lidar level 1 file.')
    parser.add_argument('flight_summary', action="store", type=str,
                        help='common flight-summary file as stored at the BADC.')
    parser.add_argument('-s', '--step', action="store", type=int, default=2, required=False,
                        help='step size for lidar data plots. If for example step=5, \
                        then only every fifth lidar profile is used. Using this option can speed up the process.')
    parser.add_argument('-a', '--alt-scale-factor', action="store", type=int, default=5, required=False,
                        help='multiplies the altitude by this factor e.g. with \
                        the default alt-scale-factor of 5: 10000m becomes 50000m in google-earth.')
    parser.add_argument('-o', '--outpath', action="store", type=str,
                        default=os.path.expanduser('~'), required=False,
                        help='outpath for kmz file')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()
    print(args)
    process(args.lidar_file,
            args.flight_summary,
            step=args.step,
            alt_scale_factor=args.alt_scale_factor,
            outpath=args.outpath)


if __name__ == '__main__':
    main()




#ROOT_DATA_PATH = '/home/axel/Dropbox/raw_lidar_netcdf/'
#import os
#flight_summary_file = os.path.join(ROOT_DATA_PATH, 'flight-sum_faam_20150812_r0_b923.txt')
#lidar_datafile = os.path.join(ROOT_DATA_PATH, 'metoffice-lidar_faam_20150812_r0_B923_level1.nc')

#ds = get_data(lidar_datafile)


#process(lidar_datafile,
#        flight_summary_file,
#        step=2,
#        alt_scale_factor=5)

