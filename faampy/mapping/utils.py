import datetime
import numpy as np
import os
import subprocess
import sys
import time
import tempfile

import georasters as gr

_TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

def conv_bearing_to_angle(bearing):
    """Converts a compass bearing to and angle.

    :param float angle: bearing in degrees
    """
    result = np.mod(450-bearing, 360)
    return result


def conv_angle_to_bearing(angle):
    """Converts and angle to a compass bearing.
    
    :param float angle: angle
    :returns float: compass bearing in degrees
    """
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
    """Coordinate translation with respect to a new origin.

    :param float lon: longitude
    :param float lat: latitude
    :param tuple origin: coordinates of origin as tuple (longitude, latitude)
    :returns tuple (x, y): coordinates of translated point; units is meters
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
    return (x,y)


def rotate_coord(x, y, angle):
    """Coordinate system rotation
    
    :param float x: x coordinate
    :param float y: y coordinate
    :param float angle: rotation angle; anit-counter clockwise
    :returns: rotated coordinate tuple (x, y) 
    :rtype: float
    """
    x_rot = x * np.cos(np.deg2rad(angle)) + y * np.sin(np.deg2rad(angle))
    y_rot = -x * np.sin(np.deg2rad(angle)) + y * np.cos(np.deg2rad(angle))
    return (x_rot, y_rot)


def get_wgs84_offset(coords):
    """Uses the GeoidEval routines from [1] to get the offset between GPS height
    and mean sea level. GPS height is the height above the theoretical WGS84
    spheroid. The offset around the UK is ~50m. For further details see the article
    on the ESRI website [2].

    [1] http://geographiclib.sourceforge.net/
    [2] http://www.esri.com/news/arcuser/0703/geoid1of3.html

    Example::
    
      >>> from faampy.mapping.utils import get_wgs84_offset
      >>> coord = [(50, 0), (51, 2), (54, 2)]
      >>> offset = get_wgs84_offset(coord)
      >>> print(offset
      [45.0389, 44.4422, 42.6927]

    """

    if not isinstance(coords, list):
        coords = [coords, ]

    lon, lat = zip(*coords)
    lon = list(lon)
    lat = list(lat)

    bad_ix = []
    for i in range(len(lon)):
        if abs(lon[i]) > 180.:
            lon[i] = 180.
            bad_ix.append(i)
        if abs(lat[i]) > 90.:
            lat[i] = 90.
            bad_ix.append(i)
    bad_ix = np.unique(bad_ix)

    lat_str = [dec_to_dms_(l, 'ns') for l in lat]
    lon_str = [dec_to_dms_(l, 'ew') for l in lon]
    coords_str =  zip(lat_str, lon_str)
    fd, fn =  tempfile.mkstemp()
    fd = open(fn, 'w')
    fd.writelines(['%s %s\n' % l for l in coords_str])
    fd.close()
    geoideval = subprocess.check_output(['which', 'GeoidEval']).strip()
    result = subprocess.check_output('%s --input-file %s' % (geoideval, fn),
                                     shell=True)
    result = [float(r) for r in result.split()]
    for i in bad_ix:
        result[i] = np.nan
    return result


def calc_distance_to_point(coords1, coords2):
    """Function calculates the distance between two points that are
    given as coordinate tuple. This function is more or less just
    a wrapper for the haversine package [1].
    
    :param tuple coords: (longitude, latitude)
    :param tuple origin: (longitude, latitude)
    :returns: distance between points in meters
    :rtype: float
    
    [1] https://pypi.python.org/pypi/haversine
    
    Example::
    
        In [1]: from faampy.mapping.utils import *
        
        In [2]: pt1 = (52.072222, -0.616667)  # Cranfield
        
        In [3]: pt2 = (52.831111, -1.327778)  # EMA
        
        In [4]: calc_distance_to_point(pt1, pt2)
        
        Out[2]: 97173.56497048707

    """
    from faampy._3rdparty.haversine import haversine
    
    distance = haversine(coords1, coords2)
    distance *= 1000.  # convert to meters
    return distance


def calc_distance_to_line(coords, line):
    """This works for coordinates in a cartesian coordinate system

    :param tuple coords: (x,y) coordindates of point in meters
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


def simplify(coords, error=None, distance=None, timestep=None):
    """uses the simplify option from gpsbabel

    """
    try:
        import gpsbabel
    except ImportError:
        sys.stdout.write('gpsbabel required for this function.\n Leaving ...')
        sys.exit(0)

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
    """Checks if a point is over land or over water. This is done using
    a shape file of world boundaries and looping over all its Polygons
    to see if the point is inside any of it (contained).

    This routine requires a shape file with the worlds countries borders [1].

    [1] http://thematicmapping.org/downloads/world_borders.php
    
    :param tuple coords: coordinates of the point of interest as tuple (lon, lat)
    :returns: True or False.
    :rtype: bool
    """

    try:
        import fiona
        from shapely.geometry import Point, shape
    except ImportError:
        sys.stdout.write('The libraries fiona and shapely are required for the function to work. Leaving ...\n')
        sys.exit(0)

    if not shape_file:
        shape_file='/home/data/mapdata/other/tm_world/TM_WORLD_BORDERS-0.3.shp'

    lon, lat = coords
    pt = Point(lon, lat)
    try:
        fc = fiona.open(shape_file)
    except:
        pass
    result=False
    for feature in fc:
        if shape(feature['geometry']).contains(pt):
          result=True
    fc.close()
    return result
