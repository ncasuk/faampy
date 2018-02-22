# -*- coding: utf-8 -*-

"""
This scripts contains examples that work with an example spatialite DB, which
stores (almost) all FAAM flight tracks. An entry in this database can be
accompanied by a geometry (e.g. point, line, polygon, etc.) and it is possible
to make spatial queries, that a normal database is not able to perform. For
example distance measurements are possible.

The spatialite db is one single file, which is very convenient and does
not require the setup of an advanced database, which can come with a lots of
obstacles. In direct comparison spatialite is less powerful but has all the
features that we need. For more information see:

    https://www.gaia-gis.it/fossil/libspatialite/index

    http://www.gaia-gis.it/gaia-sins/spatialite-sql-4.4.0.html

    https://www.gaia-gis.it/gaia-sins/spatialite-tutorial-2.3.1.html

    http://postgis.net/docs/

"""

# === Start General ===========================================================
import json
import numpy as np
import os
import osgeo.ogr
import simplekml

import faampy
from faampy.core.faam_spatial import FAAM_Spatial_DB

DB_FILE = os.path.join(faampy.FAAMPY_DATA_PATH, 'db', 'faam_spatial_db.sqlite')

db = FAAM_Spatial_DB(DB_FILE)
# === End General =============================================================

# === Start Example 1 =========================================================
print('\n'*3)
print('=' * 40)
print('\n'*3)

print('Some DB info')

# Count how many records are in the DB
sql="""SELECT COUNT(*) FROM flight_tracks;"""
cur = db.conn.cursor()
cur.execute(sql)
cnt = cur.fetchone()[0]

print('Number of flights in the DB: %i' % (cnt,))
print('')

sql="""SELECT fid FROM flight_tracks ORDER BY fid;"""
cur = db.conn.cursor()
cur.execute(sql)
fids = sorted([i[0] for i in cur.fetchall()])
print('Latest fid in db: %s' % fids[-1])
all_fids = set(['b%0.3i' % i for i in range(1, 1000)] + \
               ['c%0.3i' % i for i in range(1, int(fids[-1][1:]))])
missing_fids = sorted(all_fids.difference(fids))

print('Number Missing flights: %i' % (len(missing_fids),))
print('Missing flights ids: %s' % (','.join(missing_fids),))


# === End Example 1 ===========================================================

# === Start Example 2 =========================================================
print('\n'*3)
print('=' * 40)
print('\n'*3)
print('TASK: Finding all flights that go over the North Sea')
print('\n')

# The shape (Polygon from the North Sea was downloaded from the web
# http://www.marineregions.org/gazetteer.php?p=details&id=2350

print('Reading in the shape file for the North Sea')
shp_file = os.path.join(faampy.FAAMPY_DATA_PATH, 'shp', 'north_sea.shp')
sf = osgeo.ogr.Open(shp_file)
layer = sf.GetLayer()
ns = layer.GetFeature(0)         # there is only one feature in the layer
geometry = ns.GetGeometryRef()
ns_wkt = geometry.ExportToWkt()  # Getting a Well-known text representation

print('Give me all flights where the track intersects the North Sea Polygon')

# Give me all flights where the track intersects the North Sea Polygon. Now that
# we have the Geometry in wkt format we can use it to create a sql query that we
# can send to the spatialite DB.

sql = "SELECT FT.fid FROM flight_tracks FT where "
sql += "ST_Intersects( GeomFromText('%s'), FT.the_geom) " % (ns_wkt,)
sql += "ORDER BY FT.fid;"
cur = db.conn.cursor()                       # connect
cur.execute(sql)                             # execute
fids = [i[0] for i in cur.fetchall()]        # flatten the result

print('')
print('Number of flights that intersect the North Sea: %i' % (len(fids),))
print('')
print('List flights that intersect the North Sea: %s\n' % (','.join(fids),))


# Now that we have all the fids that intersected the North Sea, we want
# to look at them using google-earth. Spatialite has the capability of
# formatting the geometries into a kml string (askml)

sql = "SELECT askml(Simplify(FT.the_geom, 0.01)) FROM flight_tracks FT WHERE"
sql += " FT.fid IN (%s)" % (str(','.join(["'%s'" % fid for fid in fids])))
cur.execute(sql)
flight_tracks_kml = cur.fetchall()


#Create a new kml file
kml=simplekml.Kml()
folder=kml.newfolder(name='Spatialite result')
lines=kml.kml().split('\n')
lines.insert(-4, '<Placemark>')
lines.insert(-4, '<name>North Sea</name>')
lines.insert(-4, geometry.ExportToKML())
lines.insert(-4, '</Placemark>')
for i, flight_track in enumerate(flight_tracks_kml):
    lines.insert(-4, '<Placemark>')
    lines.insert(-4, '<name>%s</name>' % (fids[i],))
    lines.insert(-4, flight_track[0])
    lines.insert(-4, '</Placemark>')


ofilename = os.path.join(os.environ['HOME'], 'fids_crossing_ns.kml')
print('Writing North Sea Polygon and the flight track linestrings as kml')
print('kml written to: %s' % (ofilename,))
ofile = open(os.path.join(os.path.expanduser('~'), ofilename), 'w')
ofile.write('\n'.join(lines))
ofile.close()

# === End Example 2 ===========================================================

# === Start Example 3 =========================================================

print('\n'*3)
print('=' * 40)
print('\n'*3)
# Find the length of flight track for a specific flight
fid = 'b659'
print('TASK: Give me the length of %s' % (fid,))
print('\n')
sql = "SELECT GreatCircleLength(the_geom) from "
sql += "flight_tracks where fid = '%s';" % (fid, )
cur = db.conn.cursor()                       # connect
cur.execute(sql)                             # execute
length = cur.fetchone()[0]/1000.
print('Flight %s was %.2f km long.' % (fid, length))

# === End Example 3 ===========================================================

# === Start Example 4 =========================================================

print('\n'*3)
print('=' * 40)
print('\n'*3)
# Print give me all flights when we climbed above 11000m
# There does not seem to be a way to do this directly in spatialite, so we
# do some simple data crunching in python
#
# To do this we need to get the xyz coordinates for each flight first and check
# those. I did not find a way to query the linestring directly
# Spatialite can return the geometry in json format which can then easily
# converted into a dictionary with 'coordinates' being one of the keys
MAX_HEIGHT = 11000
print('TASK: Finding flights exceeding %i m altitude' % (int(MAX_HEIGHT,)))
sql = """SELECT fid, AsGeoJSON(the_geom) from flight_tracks;"""
cur = db.conn.cursor()                       # connect
cur.execute(sql)                             # execute
result = cur.fetchall()
fid_max_alt_list = []
for r in result:
    fid = r[0]
    # get the coordinates from the geojson
    coords = np.array(json.loads(r[1])['coordinates'])
    # the alt coordinate is the 3rd column
    alt_max = np.nanmax(coords[:,2])
    fid_max_alt_list.append((fid, alt_max))

fids = sorted([i[0] for i in fid_max_alt_list if i[1] > MAX_HEIGHT])
print('N fids with gps height > %i: %i' % (int(MAX_HEIGHT), len(fids),))
print('')
print('List of flight ids: %s\n' % (','.join(fids),))
# === End Example 4 ===========================================================

# === Start Example 5 =========================================================
# http://stackoverflow.com/questions/19412462/getting-distance-between-two-points-based-on-latitude-longitude-python
def calc_distance(lat1, lon1, lat2, lon2):
    from math import sin, cos, sqrt, atan2, radians
    # approximate radius of earth in m
    R = 6373000.0
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

print('TASK: Finding flights that took off in Cranfield in every year')
Cranfield_Coords = (52.072222, -0.616667)    # Cranfield Airport coordinates
# in m; the distance is rather large to cover flights
# when the GIN didn't work straight away
MAX_DISTANCE = 15000
sql = """SELECT fid, date, AsGeoJSON(the_geom) from flight_tracks order by date;"""
cur = db.conn.cursor()                       # connect
cur.execute(sql)                             # execute
result = cur.fetchall()
# get a list of all years for which we do the analysis
years = list(set([r[1].split('-')[0] for r in result]))
dist_dict = {}
for y in years:
    dist_dict[y] = []

for r in result:
    fid = r[0]
    # get the coordinates from the geojson
    coords = np.array(json.loads(r[2])['coordinates'])
    # extract year string from sql result
    year = r[1].split('-')[0]
    lat1, lon1 = Cranfield_Coords
    # pull coordinates form the very first array
    lon2 = coords[0, 0]
    lat2 = coords[0, 1]
    dist = calc_distance(lat1, lon1, lat2, lon2)
    if dist < MAX_DISTANCE:
        dist_dict[year].append((fid, dist))

# print summary
total = 0
# print the number for every year
for year in sorted(dist_dict.keys()):
    n = len(dist_dict[year])
    total += n
    print('%7s: %3s' % (year, n))
print('%7s: %3s' % ('total', total))
# === End Example 5 ===========================================================

# === Start Example 6-1 =======================================================
print('\n'*3)
print('=' * 40)
print('\n'*3)
print('TASK: Finding all profiles that go below a defined threshold above the North Sea')
print('\n')

profile_threshold = 2000.  # in meters

# The shape (Polygon from the North Sea was downloaded from the web
# http://www.marineregions.org/gazetteer.php?p=details&id=2350

print('Reading in the shape file for the North Sea')
shp_file = os.path.join(faampy.FAAMPY_DATA_PATH, 'shp', 'north_sea.shp')
sf = osgeo.ogr.Open(shp_file)
layer = sf.GetLayer()
ns = layer.GetFeature(0)         # there is only one feature in the layer
geometry = ns.GetGeometryRef()
ns_wkt = geometry.ExportToWkt()  # Getting a Well-known text representation

print('Give me all flights where the track intersects the North Sea Polygon')

# Give me all events when the linestring in contained inside the
# North Sea Polygon

sql = "SELECT FE.id, FE.desc, FE.start_datetime, FE.end_datetime, "
sql += "AsGeoJSON(FE.the_geom) FROM fltsumm_event FE where "
sql += "ST_Contains(GeomFromText('%s'), FE.the_geom) " % (ns_wkt,)
sql += "ORDER BY FE.id;"
cur = db.conn.cursor()                       # connect
cur.execute(sql)                             # execute
fevents = [i for i in cur.fetchall()]        # flatten the result

# Now we filter the flight summary events to look for those that wer are
# interested in
fevents_filtered = []
for fevent in fevents:
    # only consider events that start with 'prof'
    if fevent[1].lower().startswith('prof'):
        # extract the altitude values from the linestring coordincates
        if not fevent[4]:
            continue
        alt_rng = sorted([json.loads(fevent[4])['coordinates'][0][2],
                          json.loads(fevent[4])['coordinates'][1][2]])
        if min(alt_rng) < profile_threshold:
            fevents_filtered.append(fevent)
fevents = fevents_filtered

# Now print a summary
print('\n')
print('A total of %i events fit the criteria.' % (len(fevents)))
print('\n')

# Create a summary table
# The columns are: fid, start_time, end_time, start_altitude, end_altitude
output = []
for fevent in fevents:
    alt_rng = sorted([json.loads(fevent[4])['coordinates'][0][2],
                      json.loads(fevent[4])['coordinates'][1][2]])
    output.append('%6s %s %s %5i %5i' % (fevent[0].split('_')[0],
                                         fevent[2].split('T')[1],
                                         fevent[3].split('T')[1],
                                         int(alt_rng[0]),
                                         int(alt_rng[1])))

# Print only the last 20 events
for line in output[-20:]:
    print(line)
# === End Example 6-1 =========================================================

# === Start Example 6-2 =======================================================
print('\n'*3)
print('=' * 40)
print('\n'*3)
print('TASK: Extract the data for all the profiles from the FAAM core netCDF')
print('\n')

from faampy.utils.file_list import File_List

BADC_MIRROR_PATH = '/home/data/faam/badcMirror'

# get all FAAM core files and filter the latest revision
core_file_list = File_List(BADC_MIRROR_PATH)
core_file_list.filter_by_data_type('core-lowres')
core_file_list.filter_latest_revision()

# get list of unique fids from the fevents list created in the previous example
ufids = np.unique([o.split()[0] for o in output])

from faampy.core.faam_data import FAAM_Dataset

df_list = []
for fid in ufids:
    # check if the core file for this specific flight is available
    if fid not in [f.fid for f in core_file_list]:
        continue
    for c in core_file_list:
        if fid == c.fid:
            core_file_name = os.path.join(c.path, c.filename)
            ds = FAAM_Dataset(core_file_name)
            df = ds.as_dataframe(varnames=['TAT_DI_R', 'TAT_ND_R',
                                           'PS_RVSM', 'ALT_GIN'])
            df['fid'] = fid
            df_list.append(df.copy())

import pandas as pd

# Create one large dataframe by concatenating those from the df_list
df = pd.concat(df_list)

# Create a new column
df['of_interest'] = 0
for fevent in fevents:
    start_time = fevent[2].replace('T', ' ')
    end_time = fevent[3].replace('T', ' ')
    df['of_interest'][start_time:end_time] = 1

# Delete all rows that are of *no* interest
df.drop(df[df['of_interest'] == 1].index, inplace=True)
# Now that we don't need that column any more we delete it
del df['of_interest']

df.drop(df[df['ALT_GIN'] > 2000.].index, inplace=True)

# Calculate the potential temperature
# https://en.wikipedia.org/wiki/Potential_temperature
df['pot_temp'] = df['TAT_DI_R']*(1000./df['PS_RVSM'])**0.286

# Some data cleaning
df.drop(df[df['pot_temp'] > 305.].index, inplace=True)
df.drop(df[df['pot_temp'] < 265.].index, inplace=True)
# Analyse the four seasons: DJF, MAM, JJA, SON
df['month'] = df.index.month
# Create categories for the season and altitude (slices of 500m)
df['cat_season'] = pd.cut(df['month'], 4, labels=['DJF', 'MAM', 'JJA', 'SON'])
df['cat_alt'] = pd.cut(df['ALT_GIN'],
                       bins=np.arange(0, 2000, 100),
                       labels=np.arange(50, 1950, 100))

grouped = df.groupby('cat_season')

import matplotlib.pyplot as plt

f, axs = plt.subplots(1, 4, sharey=True, sharex=True)
i = 0
for season, group in grouped:
    ax = axs[i]
    group.boxplot(ax=ax, column=['pot_temp'], by=['cat_alt'], vert=False, showfliers=False)
    if i == 0:
        ax.set_ylabel('gps alt (m)')
    ax.set_title(season)
    ax.set_xlabel('pot temp (K)')
    plt.suptitle('Potential Temperature Profiles above the North Sea')
    i += 1

axs[0].set_xlim(270, 305)
# === End Example 6-2 =========================================================
