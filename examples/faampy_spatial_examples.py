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


import json
import numpy as np
import os
import osgeo.ogr
import simplekml

from faam_spatial import FAAM_Spatial_DB

LATEST_FID='b991'

DB_FILE = './faam_spatial_db.sqlite'

db = FAAM_Spatial_DB(DB_FILE)

#=============================================================================

print '\n'*3
print '=' * 40
print '\n'*3

print 'Some DB info'

# Count how many records are in the DB
sql="""SELECT COUNT(*) FROM flight_tracks;"""
cur = db.conn.cursor()
cur.execute(sql)
cnt = cur.fetchone()[0]

print 'Number of flights in the DB: %i' % (cnt,)
print ''

sql="""SELECT fid FROM flight_tracks ORDER BY fid;"""
cur = db.conn.cursor()
cur.execute(sql)
fids = [i[0] for i in cur.fetchall()]
#By today FAAM has flown a total of 991 missions
all_fids = set(['b%0.3i' % i for i in range(int(LATEST_FID[1:]))])
missing_fids = sorted(all_fids.difference(fids))

print 'Number Missing flights: %i' % (len(missing_fids),) 
print 'Missing flights ids: %s' % (','.join(missing_fids),)


#=============================================================================


print '\n'*3
print '=' * 40
print '\n'*3
print 'TASK: Finding all flights that go over the North Sea'
print '\n'
# The shape (Polygon from the North Sea was downloaded from the web
# http://www.marineregions.org/gazetteer.php?p=details&id=2350
print 'Reading in the shape file for the North Sea'
sf = osgeo.ogr.Open('north_sea.shp')
layer = sf.GetLayer()
ns = layer.GetFeature(0)         # there is only one feature in the layer
geometry = ns.GetGeometryRef()
ns_wkt = geometry.ExportToWkt()  # Getting a Well-known text representation 

print 'Give me all flights where the track intersects the North Sea Polygon'

# Now that we have the Geometry in a wkt format we can use 
# that to create a sql query that we can send to the spatialite DB
sql = "SELECT FT.fid FROM flight_tracks FT where "
sql += "ST_Intersects( GeomFromText('%s'), FT.the_geom) " % (ns_wkt,)
sql += "ORDER BY FT.fid;" 
cur = db.conn.cursor()                       # connect
cur.execute(sql)                             # execute
fids = [i[0] for i in cur.fetchall()]        # flatten the result

print ''
print 'Number of flights that intersect the North Sea: %i' % (len(fids),)
print ''
print 'List flights that intersect the North Sea: %s\n' % (','.join(fids),)


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
print 'Writing North Sea Polygon and the flight track linestrings as kml'
print 'kml written to: %s' % (ofilename,)
ofile = open(ofilename, 'w')
ofile.write('\n'.join(lines))
ofile.close()


#=============================================================================


print '\n'*3
print '=' * 40
print '\n'*3
# Find the length of flight track for a specific flight
fid = 'b659'
print 'TASK: Give me the length of %s' % (fid,)
print '\n'
sql = "SELECT GreatCircleLength(the_geom) from "
sql += "flight_tracks where fid = '%s';" % (fid, )
cur = db.conn.cursor()                       # connect
cur.execute(sql)                             # execute
length = cur.fetchone()[0]/1000.
print 'Flight %s was %.2f km long.' % (fid, length)


#=============================================================================


print '\n'*3
print '=' * 40
print '\n'*3
# Print give me all flights when we climbed above 11000m
# There does not seem to be a way to do this directly in spatialite, so we
# do some simple data crunching in python
#
# To do this we need to get the xyz coordinates for each flight first and check
# those. I did not find a way to query the linestring directly
# Spatialite can return the geometry in json format which can then easily
# converted into a dictionary with 'coordinates' being one of the keys
MAX_HEIGHT = 11000
print 'TASK: Finding flights exceeding %i m altitude' % (int(MAX_HEIGHT,))
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
print 'N fids with gps height > %i: %i' % (int(MAX_HEIGHT), len(fids),)
print ''
print 'List of flight ids: %s\n' % (','.join(fids),)


#=============================================================================


