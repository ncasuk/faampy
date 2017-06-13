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
        if os.path.exists(db_file):
            exists = True
        else:
            exists = False
        self.conn = db.connect(db_file)
        if not exists:
            self.setup()
            sys.stdout.write('DB created ... \n')

    def info(self):
        # Test that the spatialite extension has been loaded:
        cur = self.conn.execute('SELECT sqlite_version(), spatialite_version()')
        info = cur.fetchall()
        sys.stdout.write('%s %s\n' % (info[0][0], info[1][0]))

    def setup(self):
        cur = self.conn.cursor()
        # creating a LINESTRING table
        sql = 'CREATE TABLE flight_tracks ('
        sql += 'fid TEXT NOT NULL PRIMARY KEY,'
        sql += 'date DATE);'
        cur.execute(sql)

        sql = 'CREATE TABLE fltsumm_event ('
        sql += 'id TEXT NOT NULL PRIMARY KEY,'
        sql += 'fid TEXT NOT NULL,'
        sql += 'desc TEXT,'
        sql += 'start_datetime DATETIME,'
        sql += 'end_datetime DATETIME);'
        cur.execute(sql)
        # http://stackoverflow.com/questions/24047634/performance-problems-using-sqlite-function-initspatialmetadata-to-create-a-spa
        sql = 'SELECT InitSpatialMetadata(1);'
        cur.execute(sql)
        sql = "SELECT AddGeometryColumn('flight_tracks', 'the_geom', 4326, 'LINESTRINGZ', 'XYZ');"
        cur.execute(sql)
        sql = "SELECT AddGeometryColumn('fltsumm_event', 'the_geom', 4326, 'LINESTRINGZ', 'XYZ');"
        cur.execute(sql)
        self.conn.commit()
        return

    def insert_flight_track(self, fid, dt, wkt, overwrite=False):
        cur = self.conn.cursor()
        if overwrite:
            sql = """SELECT * from flight_tracks where fid=='%s';""" % (fid,)
            cur.execute(sql)
            res = cur.fetchone()
            if res:
                cur.execute("DELETE FROM flight_tracks where fid=='%s';" % (fid,))

        geom = "GeomFromText('" + wkt + "', 4326)"
        sql = "INSERT INTO flight_tracks (fid, date, the_geom) "
        sql += "VALUES ('%s', '%s', %s);" % (fid, dt.strftime('%Y-%m-%d'), geom)
        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()
        return

    def insert_fltsumm_event(self, fid, desc, sdt, edt, wkt, overwrite=False):
        """
        :param fid: flight id
        :param sdt: start time
        :param edt: end time
        :param wkt: well known text representation
        """
        cur = self.conn.cursor()
        # creating an unique id using fid and start time
        _id = '%s_%s' % (fid, sdt.strftime('%Y%m%dT%H%M%S'))

        if overwrite:
            sql = """SELECT * from fltsumm_event where id=='%s';""" % (_id,)
            cur.execute(sql)
            res = cur.fetchone()
            if res:
                cur.execute("DELETE FROM fltsumm_event where id=='%s';" % (_id,))

        geom = "GeomFromText('" + wkt + "', 4326)"
        sql = "INSERT INTO fltsumm_event(id, fid, desc, start_datetime, end_datetime, the_geom) "
        sql += "VALUES ('%s', '%s', '%s', '%s', '%s', %s);" % (_id,
                                                               fid,
                                                               desc,
                                                               sdt.strftime('%Y-%m-%dT%H:%M:%S'),
                                                               edt.strftime('%Y-%m-%dT%H:%M:%S'),
                                                               geom)
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
