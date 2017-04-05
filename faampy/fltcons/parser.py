'''
Created on 31 Oct 2011

@author: axel
'''

import netCDF4
import os
import sys
import datetime

import faampy
import faampy.fltcons
from faampy.utils.file_info import get_revision_from_filename, \
                                   get_fid_from_filename


class Parser(object):

    def __init__(self):
        pass

    def parse(self, ifile):
        """Parsing"""
        result = {}

        if os.path.splitext(ifile)[1] == '.nc':
            ds = netCDF4.Dataset(ifile, 'r')
            txt = ds.Flight_Constants
            lines = txt.split('\n')
            ds.close()
        elif os.path.splitext(ifile)[1] == '.txt':
            f = open(ifile, 'r')
            lines = f.readlines()
            f.close()
        else:
            sys.stdout.write('Can not handle %s ...\n' % ifile)
            return
        fltcs_list = faampy.fltcons.PARAMETERS

        rev = get_revision_from_filename(ifile)
        fid = get_fid_from_filename(ifile)

        rev_date = None
        tmplines = lines[:]
        while not rev_date and tmplines:
            line = tmplines.pop()
            try:
                rev_date = datetime.datetime.strptime(line.split('-')[1].strip(), '%d %b %Y')
            except:
                pass
            try:
                rev_date = datetime.datetime.strptime(line.split('-')[1].strip(), '%d %B %Y')
            except:
                pass
        rev_date = rev_date.strftime('%Y-%m-%d')
        if not rev_date:
            rev_date = '2099-01-01'

        for line in lines:
            if line.split(' ')[0] in fltcs_list:
                par = line.split(' ')[0]
                result[par] = (fid, rev, rev_date, line.strip('\n'))
        return result

#p = Parser()
#x=p.parse(os.path.join(fl[-1].path, fl[-1].filename))#
#print(x)
#f = '/mnt/faamarchive/badcMirror/data/2014/b847-feb-18/core_raw/flight-cst_faam_20140218_r0_b847.txt'
#P = Parser()
#d = P.parse(f)
#print(d)
