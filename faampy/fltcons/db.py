'''
Created on 14 Dec 2010

@author: axel
'''

import sys

import os

import sqlite3 as dbapi
import re
import time

import faampy
import faampy.fltcons

from faampy.fltcons.Parser import Parser

from faampy.utils import *


#faampy.fltcons.DB_NAME = os.path.join(faampy.__path__[0], '..', 'files', 'db', 'faam_fltcons.sqlite')
FLTCONS_DB_NAME = os.path.join(faampy.FAAMPY_DATA_PATH, 'db', 'faam_fltcons_db.sqlite')

class DB(object):

    def __init__(self):
        pass

    def connect(self):
        self.con = dbapi.connect(FLTCONS_DB_NAME)

    def disconnect(self):
        self.con.close()

    def setup(self):
        """Create the fltcons table"""
        if not hasattr(self, 'con'):
            self.connect()
        sql = """CREATE TABLE fltcons (par VARCHAR(20), fid INTEGER, rev VARCHAR(4), rdate DATE, line TEXT, fname TEXT);"""
        cur = self.con.cursor()
        cur.execute(sql)
        self.con.commit()

    def insert(self, par, fid, rev, rdate, line, fname, commit=True):
        template="""INSERT INTO fltcons VALUES ('%s', '%s', '%s', '%s', '%s', '%s');"""
        if 'list' in str(type(par)):
            for i in range(len(par)):
                sql = template % (par[i], fid[i], rev[i], rdate[i], line[i], fname[i])
                cur = self.con.cursor()
                cur.execute(sql)
        else:
            sql = template % (par, fid, rev, rdate, line, fname)
            cur = self.con.cursor()
            cur.execute(sql)
        # Only commit if commit keyword is set, which is the default
        # Otherwise the sql statement is returned
        if commit:
            self.con.commit()
        return sql

    def clean(self):
        sql = "DELETE from fltcons;"
        cur = self.con.cursor()
        cur.execute(sql)

    def query(self, par):
        pass
