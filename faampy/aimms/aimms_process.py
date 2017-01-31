# -*- coding: utf-8 -*-
"""
The script wraps the several steps for processing the AIMMS data.
The script requires wine and idl

The script is called as:

   python aimms_process.py FID


Created on Mon Jan 30 08:50:47 2017

@author: axel
"""

import os
import re
import shutil
import sys
import tempfile

from faampy.utils.file_info import *
from faampy.utils.file_list import *



AIMMS_ROOT_PATH = '/mnt/faamarchive/Data/cloudphysics'
CORE_ROOT_PATH = '/mnt/faamarchive/badcMirror/'

AIMMS_ROOT_PATH = '/home/tardis/FAAMarchive/Data/cloudphysics'
CORE_ROOT_PATH = '/home/tardis/FAAMarchive/badcMirror/'

TEMPPATH = tempfile.mkdtemp()
OUTPATH = '/home/tardis/'
CALFILE = 'AIMMScalB884.dat'

_VERSION_ = 'v003'
revstring = 'r0'
 


 
def get_aimms_raw_files(AIMMS_ROOT_PATH, fid):
    """The AIMMS probe produces severl raw data files for
    a single flight. Those files needs to be sticked together.
    """    
    pattern = '.*%s.*odms.*\d{8}.*r\d{2}' % (fid,)
    file_list = []    
    for root, subFolders, files in os.walk(AIMMS_ROOT_PATH):
        for f in files:
            filename = os.path.join(root, f)
            if re.match(pattern, filename.lower()):
                file_list.append(filename)
    return file_list


def get_core_file(CORE_ROOT_PATH, fid):
    fl = File_List(CORE_ROOT_PATH)
    fl.filter_by_data_type('core-lowres')
    fl.filter_latest_revision()
    for f in fl:
        if f.fid == fid:
            return os.path.join(os.path.join(f.path, f.filename))


dir_path = os.path.dirname(os.path.realpath(__file__))

# get the flight number
fid = sys.argv[1]

aimms_raw_files=get_aimms_raw_files(AIMMS_ROOT_PATH, fid)
core_file = get_core_file(CORE_ROOT_PATH, fid)


print(aimms_raw_files)
print(core_file)
print(TEMPPATH)

date_string = os.path.basename(core_file).split('_')[2]


for f in aimms_raw_files:
    shutil.copy(f, os.path.join(TEMPPATH, os.path.basename(f)))

shutil.copy(core_file, os.path.join(TEMPPATH, os.path.basename(core_file)))


# all the files that are needed for the processing will be copied to the TEMPPATH to
# keep things simple
for f in ['asmbl.exe',
          'canextr4.exe',
          'ekf556.exe',
          'convert_aimms_netcdf.pro',
          'findcorefile.pro',
          'cal_files/'+CALFILE]:
    shutil.copy(os.path.join(dir_path, f), os.path.join(TEMPPATH, f))

# move into the temporary directory
os.chdir(TEMPPATH)

idents = list(set([os.path.splitext(os.path.basename(f))[0] for f in aimms_raw_files]))

for i in idents:
    cmd = "wine asmbl.exe %s 1" % (i,)
    os.system(cmd)
    #cmd = "wine canextr4.exe %s.raw"    
    aimms_out_file = '%s_%s_aimms.out' % (fid, date_string)
    cmd = "wine ekf556.exe %s %s.raw -c on -o %s" % (CALFILE, i, aimms_out_file)
    os.system(cmd)    
    
    aimms_ncfile = os.path.join(OUTPATH, 'metoffice-aimms_faam_%s_%s_%s_%s.nc' % (date_string, _VERSION_, revstring, fid))
    # call the idl script from the command line
    cmd = """idl -e "convert_aimms_netcdf, '%s/', '%s', '%s', '%s'"  """ % (os.path.join(TEMPPATH), os.path.join(TEMPPATH, os.path.basename(core_file)), aimms_ncfile, fid)
    # print(cmd)
    os.system(cmd)

# Tidy up again
shutil.rmtree(TEMPPATH)    
