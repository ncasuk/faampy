import datetime
import numpy as np
import os
import subprocess
import time
import tempfile

import georasters as gr

_TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

def conv_bearing_to_angle(bearing):
    """bearing is the angle on a compass

    """
    result = np.mod(450-bearing, 360)
    return result


def conv_angle_to_bearing(angle):
    result = np.mod(450-angle, 360)
    return result


def dec_to_dms_(deg, direction):
    """direction is either 'ns' or 'ew'

    """
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    if d < 0:
        direction = direction[1].upper()
    else:
        direction = direction[0].upper()
    result = '%s%.2i:%.2i:%f' % (direction, abs(d), m, sd)
    return result


def translate_coord(lon, lat, origin):
    """coordinate translation to a global origin

    """
    start_long = lon*0 + np.radians(origin[0])
    start_latt = lat*0 + np.radians(origin[1])
    end_long = np.radians(lon)
    end_latt = np.radians(lat)

    d_latt = end_latt - start_latt
    d_long = end_long - start_long
    d_latt = d_latt * 0.0
    a = np.sin(d_latt/2)**2 + np.cos(start_latt) * np.cos(end_latt) * np.sin(d_long/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    x = 6371.0 * c * 1000.0
    ix = np.where(end_long < start_long)
    x[ix] = x[ix] * -1.0

    d_latt = end_latt - start_latt
    d_long = end_long - start_long
    d_long = d_long * 0.0
    a = np.sin(d_latt/2)**2 + np.cos(start_latt) * np.cos(end_latt) * np.sin(d_long/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    y = 6371.0 * c * 1000.0
    ix = np.where(end_latt < start_latt)
    y[ix] = y[ix] * -1.0
    return(x,y)


def rotate_coord(x, y, angle):
    """coordinate system rotation

    """
    x_rot = x * np.cos(np.deg2rad(angle)) + y * np.sin(np.deg2rad(angle))
    y_rot = -x * np.sin(np.deg2rad(angle)) + y * np.cos(np.deg2rad(angle))
    return(x_rot, y_rot)


def get_wgs84_offset(coords):
    """Uses the GeoidEval routines from [1] to get the offset between GPS data and
    sea level.

    #to get the difference between WGS84 and mean sea level
    GeoidEval --input-file /tmp/tmpt35as

    example:
      >>> coord = [(50, 0), (51, 2), (54, 2)]
      >>> offset = get_wgs84_offset(coord)
      >>> print(offset
      [45.0389, 44.4422, 42.6927]

    [1] http://geographiclib.sourceforge.net/
    [2] http://www.esri.com/news/arcuser/0703/geoid1of3.html
    """
    #lon, lat = zip(*coord)
    if not isinstance(coords, list):
        coords = [coords, ]

    lon, lat = zip(*coords)
    lon_str = [dec_to_dms_(l, 'ns') for l in lon]
    lat_str = [dec_to_dms_(l, 'ew') for l in lat]
    coords_str =  zip(lon_str,  lat_str)
    fd, fn =  tempfile.mkstemp()
    fd = open(fn, 'w')
    fd.writelines(['%s %s\n' % l for l in coords_str])
    fd.close()
    geoideval = os.system('which GeoidEval')
    result = subprocess.check_output('%s --input-file %s' % (geoideval, fn),  shell=True)
    result = [float(r) for r in result.split()]
    return result


def calc_distance_to_point(coords, origin):
    #TODO
    if not isinstance(coords, list):
        coords = [coords, ]



def calc_distance_to_line(coords, line):
    """ This works in a cartesian coordinate system

    point should be list of tuples tuple (x, y)
    line should be tuple ((x1, y1), (x2, y2))
    """
    x3 = coords[0]
    y3 = coords[1]
    x1 = line[0][0]
    y1 = line[0][1]
    x2 = line[1][0]
    y2 = line[1][1]
    px = x2-x1
    py = y2-y1
    u = ((x3 - x1) * px + (y3 - y1) * py) / float(px*px + py*py)
    if u > 1:
        u = 1
    elif u < 0:
        u = 0
    x = x1 + u * px
    y = y1 + u * py
    dx = x - x3
    dy = y - y3
    dist = np.sqrt(dx*dx + dy*dy)
    return dist


#TODO: needs speed improvement
def simplify(coords, error=None, distance=None, timestep=None):
    """uses the simplify option from gpsbabel

    """
    import gpsbabel

    if not error:
        error = '0.2k'
    if not distance:
        distance = '10k'
    if not timestep:
        timestep = 120
    #crosstracked track
    (lon, lat, alt) = zip(*coords)
    now = datetime.datetime.utcnow()
    timestamp = [(now+datetime.timedelta(seconds=i)).strftime(_TIMESTAMP_FORMAT) for i in range(len(lon))]
    #gpxd = lonlatalt_to_gpx(lon, lat, alt)
    gpxr = gpsbabel.GPXRoute()
    n = len(lon)
    for i in range(n):
        gpxr.rtepts.append(gpsbabel.GPXWaypoint())
        gpxr.rtepts[-1].lat = lat[i]
        gpxr.rtepts[-1].lon = lon[i]
        gpxr.rtepts[-1].ele = alt[i]
        gpxr.rtepts[-1].time = timestamp[i]
    gpxd = gpsbabel.GPXData()
    gpxd.rtes.append(gpxr)

    track_ct = gpsbabel.GPSBabel()
    track_ct.procRoutes = True
    track_ct.setInGpx(gpxd)
    track_ct.addFilter('simplify', {'crosstrack': None, 'error': error})
    track_ct.captureStdOut()
    (retcode, gpxd_crosstracked) = track_ct.execCmd()

    lon_tmp, lat_tmp, alt_tmp, timestamp_tmp = ([], [], [], [])
    for rte in gpxd_crosstracked.rtes:
        for pt in rte.rtepts:
            lon_tmp.append(pt.lon)
            lat_tmp.append(pt.lat)
            alt_tmp.append(pt.ele)
            timestamp_tmp.append(pt.time)

    track_ip = gpsbabel.GPSBabel()
    track_ip.procRoutes = True
    track_ip.setInGpx(gpxd)
    track_ip.addFilter('position', {'distance': '50m'})
    track_ip.captureStdOut()
    (retcode, gpxd_interpolated) = track_ip.execCmd()

    for rte in gpxd_interpolated.rtes:
        for pt in rte.rtepts:
            if (pt.time.hour * 3600 + pt.time.minute * 60 + pt.time.second) % timestep == 0:
                lon_tmp.append(pt.lon)
                lat_tmp.append(pt.lat)
                alt_tmp.append(pt.ele)
                timestamp_tmp.append(pt.time)
    timesort = [time.mktime(tstamp.timetuple()) for tstamp in timestamp_tmp]
    ix = list(index for index, item in sorted(enumerate(timesort), key=lambda item: item[1]))
    lon = [float(lon_tmp[i]) for i in ix]
    lat = [float(lat_tmp[i]) for i in ix]
    alt = [float(alt_tmp[i]) for i in ix]
    return (lon, lat, alt)


def is_point_on_land(coords, shape_file=None):
    """Checks if a coords are over land or over water. This is done useing
    a shape file of world boundaries and looping over all Polygons to see
    if the point is in any of it.
    
    """
    
    import fiona
    from shapely.geometry import Point, shape

    if not shape_file:
        shape_file='/home/data/mapdata/other/tm_world/TM_WORLD_BORDERS-0.3.shp'

    lon, lat=coords
    pt=Point(lon, lat)
    try:    
        fc=fiona.open(shape_file)
    except:
        pass
    result=False
    for feature in fc:
        if shape(feature['geometry']).contains(pt):
          result=True
    fc.close()
    return result
 