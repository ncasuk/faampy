# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 11:00:50 2016

@author: axel
"""

import os
import pyspatialite.dbapi2 as db
import sys

class FAAM_Spatial_DB(object):

    def __init__(self, db_file): 
        self.db_file = db_file
        self.conn = db.connect(db_file)    
        if not os.path.exists(db_file):            
            self.setup()
            return 'DB created ... \n'

    def info(self):
        # Test that the spatialite extension has been loaded:
        cur = self.conn.execute('SELECT sqlite_version(), spatialite_version()')
        info = cur.fetchall()
        sys.stdout.write('%s %s\n' % (info[0][0], info[1][0]))

    def setup(self):
        cur=self.conn.cursor()
        # creating a LINESTRING table
        sql = 'CREATE TABLE flight_tracks ('
        sql += 'fid TEXT NOT NULL PRIMARY KEY,'
        sql += 'date DATE);'
        cur.execute(sql)
        sql = 'SELECT InitSpatialMetadata(1);'
        #http://stackoverflow.com/questions/24047634/performance-problems-using-sqlite-function-initspatialmetadata-to-create-a-spa
        sql = 'SELECT InitSpatialMetadata(1);'
        cur.execute(sql)
        sql = "SELECT AddGeometryColumn('flight_tracks', 'the_geom', 4326, 'LINESTRINGZ', 'XYZ');"        
        cur.execute(sql)
        self.conn.commit()
        return

    def insert(self, fid, dt, wkt, overwrite=False):
        cur = self.conn.cursor()
        if overwrite:
            sql = """SELECT * from flight_tracks where fid=%s;""" % (fid,)
            cur.execute(sql)
            res = cur.fetchone()
            if res:
                cur.execute("DELETE FROM flight_tracks where fid=%s;" % (fid,))        
                
        geom = "GeomFromText('" + wkt + "', 4326)"
        sql = "INSERT INTO flight_tracks (fid, date, the_geom) "
        sql += "VALUES ('%s', '%s', %s);" % (fid, dt.strftime('%Y-%m-%d'), geom)    
        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()
        return

    def clean(self):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM flight_tracks;")
        self.conn.commit()
        return

    def check_exists(self, fid):
        sql = 'SELECT fid FROM flight_tracks;'
        cur = self.conn.cursor()
        cur.execute(sql)
        if fid in [i[0] for i in cur.fetchall()]:
            return True
        else:
            return False
    
    def close(self):
        self.conn.close()




