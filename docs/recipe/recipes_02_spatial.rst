

Recipes - Spatial
=================

FAAM core data are stored as netCDF and come with *Time* dimension. However, since the FAAM aircraft is a moving plaform location is obviously also an important dimension and spatial queries of the FAAM data can add useful functionality. To provide this feature the FAAM flight tracks are inserted as *linestring* into a database with spatial capabilities. Such a database allows queries like:

  * Give me all the flights that have crossed Scotland
  * On which flights did we fly closer than 10nm miles pass the Queen's palace
  * What length was the flight track

  
DB description
--------------

The spatialite DB is stored in one single file, which is very convenient and does not require the setup of an advanced database, which can come with a lots of obstacles. In direct comparison spatialite is less powerful but has all the features that we need. For more information see:
    
  | https://www.gaia-gis.it/fossil/libspatialite/index    
  | http://www.gaia-gis.it/gaia-sins/spatialite-sql-4.4.0.html
  | https://www.gaia-gis.it/gaia-sins/spatialite-tutorial-2.3.1.html    
  | http://postgis.net/docs/

The example database has currently only one table and three colums:

  | fid      - Flight id
  | date     - Start date of flight
  | the_geom - Holds the linestring geometry
    

For the below examples python is our tool of choice, which has all the necessary modules ot interact with the db. The code is from the *faampy_spatial_examples.py* file.


Imports and DB connection
-------------------------

For the examples below to work we need to import some common modules.

.. code-block:: python

   import json
   import numpy as np
   import os
   import osgeo.ogr
   import simplekml
   
   try:
      from faampy.faam_spatial import FAAM_Spatial_DB
   except:
      import faam_spatial
   
   LATEST_FID = 'b991'
   
   DB_FILE = './faam_spatial_db.sqlite'
   
   # connecting to the database
   db = FAAM_Spatial_DB(DB_FILE)


Example: Get some db info
-------------------------

Just get some basic information from the database.

.. code-block:: python

   print 'Some DB info'
   
   # Count how many records are in the DB
   sql="""SELECT COUNT(*) FROM flight_tracks;"""
   cur = db.conn.cursor()
   cur.execute(sql)
   cnt = cur.fetchone()[0]
   
   print 'Number of flights in the DB: %i' % (cnt,)

   # Get all fids that are in the DB
   sql = """SELECT fid FROM flight_tracks ORDER BY fid;"""
   cur = db.conn.cursor()
   cur.execute(sql)
   fids = [i[0] for i in cur.fetchall()]
   # By today FAAM has flown a total of 991 missions
   all_fids = set(['b%0.3i' % i for i in range(int(LATEST_FID[1:]))])
   missing_fids = sorted(all_fids.difference(fids))
   
   print 'Number Missing flights: %i' % (len(missing_fids),) 
   print 'Missing flights ids: %s' % (','.join(missing_fids),)


Example: Find flights that go over the North Sea
------------------------------------------------

The goal is to find all FAAM flights that go over the North Sea. To do this we need
the boundaries for the North Sea. A shapefile with the Polygon can be downloaded from
the web: http://www.marineregions.org/gazetteer.php?p=details&id=2350

To read it in we use the osgeo module.

.. code-block:: python

   sf = osgeo.ogr.Open('north_sea.shp')
   layer = sf.GetLayer()
   ns = layer.GetFeature(0)             # there is only one feature in the layer
   geometry = ns.GetGeometryRef()
   ns_wkt = geometry.ExportToWkt()      # Getting Well-known text representation 

Give me all flights where the track intersects the North Sea Polygon. Now that
we have the Geometry in wkt format we can use it to create a sql query that we
can send to the spatialite DB

.. code-block:: python

   sql = "SELECT FT.fid FROM flight_tracks FT where "
   sql += "ST_Intersects( GeomFromText('%s'), FT.the_geom) " % (ns_wkt,)
   sql += "ORDER BY FT.fid;" 
   cur = db.conn.cursor()                       # connect
   cur.execute(sql)                             # execute
   fids = [i[0] for i in cur.fetchall()]        # flatten the result
   
   print 'Number of flights that intersect the North Sea: %i' % (len(fids),)
   print 'List flights that intersect the North Sea: %s\n' % (','.join(fids),)
      
Now that we have all the fids that intersected the North Sea, we want
to look at them using google-earth. Spatialite has the capability of
formatting the geometries into kml format (askml).

.. code-block:: python

   sql = "SELECT askml(Simplify(FT.the_geom, 0.01)) FROM flight_tracks FT WHERE"
   sql += " FT.fid IN (%s)" % (str(','.join(["'%s'" % fid for fid in fids])))
   cur.execute(sql)
   flight_tracks_kml = cur.fetchall()
      
   #Create a new kml file
   kml = simplekml.Kml()
   folder = kml.newfolder(name='Spatialite result')
   lines = kml.kml().split('\n')
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


Example: Get the length of a flight track
------------------------------------------

Get the length of a flight track. The database can do this for us
using the *GreatCircleLength* function.

.. code-block:: python

   fid = 'b659'
   sql = "SELECT GreatCircleLength(the_geom) from "
   sql += "flight_tracks where fid = '%s';" % (fid, )
   cur = db.conn.cursor()                       # connect
   cur.execute(sql)                             # execute
   length = cur.fetchone()[0]/1000.
   print 'Flight %s was %.2f km long.' % (fid, length)
   
   
Example: Get all flights when we climbed above a certain altitude
-----------------------------------------------------------------

We are trying to find all the flights where we climbed above a certain gps 
altitude. For this we loop over all individual flight tracks. The steps are:
1. Get flight track from DB in json format
2. Use the 'coordinates' key from the json and extract the z-coordinate
3. Check if the maximum z-value is greater than the MAX_HEIGHT and store
   the fid in the result list if that's the case
   
   
.. code-block:: python

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
   print 'List of flight ids: %s\n' % (','.join(fids),)
