# -*- coding: utf-8 -*-
"""
This script goes through all the data files in a DATA_ROOT_PATH directory
and looks for defined instrument data files.

As output the script prints a list of instrument identifier and the last
flight id, that data are available.

"""

import os
import re
import sys

from datetime import datetime
from collections import OrderedDict


# Definition to what look for. A list of tuples where the first item in the tuple
# is the instrument id and the 2nd item is a list of regular expressions to 
# identify the data file
instrument_data = [('AIMMS',             ["metoffice-aimms_faam_\d{8}.*[bc]\d{3}.*.nc",]),
                   ('AQDNOX',            ["faam-aqd-nox_faam_\d{8}.*[bc]\d{3}.*.['na', 'txt']",]),
                   ('ARIES',             ["metoffice-aries_faam_\d{8}.*[bc]\d{3}.*['insb', 'mct'].nc",]),
                   ('AVAPS',             ["faam-dropsonde_faam_\d{14}.*[bBcC]\d{3}.*['proc', 'raw'].nc",]),
                   ('BUCK',              ["faam-cr2-hygro_faam_\d{8}.*[bc]\d{3}.*.na",]),
                   ('CCN',               ["faam-ccnrack_faam_\d{8}.*[bBcC]\d{3}.na",
                                          "faam-ccnrack_faam_\d{8}.*_v\d{3}_[bBcC]\d{3}.nc",]),
                   ('CFGC',              ["rhul-cf-gc-irms_faam_\d{8}.*[bBcC]\d{3}.*csv",]),
                   ('CIMS',              ["man-cims_faam_\d{8}.*[bBcC]\d{3}.na",]),
                   ('CIP100',            ["faam-cip100_faam_\d{8}.*",]),
                   ('CIP15',             ["faam-cip15_faam_\d{8}.*",]),
                   ('CORE',              ["core_faam_\d{8}.*[bBcC]\d{3}.nc",
                                          "core_faam_\d{8}.*[bBcC]\d{3}_1hz.nc",]),
                   ('CORE-CLOUD',        ["core-cloud-phy_faam_\d{8}.*[bBcC]\d{3}.nc",]),
                   ('CPC',               ["faam-3786cpc_faam_\d{8}.*[bBcC]\d{3}.na",]),
                   ('CVI',               ["metoffice-cvi_faam_\d{8}.*.*",]),
                   ('DCGC',              ["york-dc-gc-fid[123]_faam_\d{8}.*[bBcC]\d{3}.*",]),
                   ('DEIMOS',            ["metoffice-deimos_faam_\d{8}.*[bBcC]\d{3}.nc",]),
                   ('FAGE',              ["leeds-fage_faam_\d{8}.*na",]),
                   ('FGGA',              ["faam-fgga_faam_\d{8}.*[bBcC]\d{3}.na",]),
                   ('GCMS',              ["york-in-situ-gcms_faam_\d{8}.*[bBcC]\d{3}.na",
                                          "york-gcms_faam_\d{8}.*[bBcC]\d{3}.na", "fgam-gcms_faam_\d{8}.*['b', 'd']\d{3}.na"]),
                   ('GRIMM',             ["faam-grimm_faam_\d{8}.*[bBcC]\d{3}.*.na",]),
                   ('JNO2',              ["leic-fr-jno2_faam_\d{8}.*.na",]),
                   ('JO1D',              ["leic-fr-jo1d_faam_\d{8}.*.na",]),                   
                   ('LIDAR',             ["metoffice-lidar_faam_\d{8}.*[bBcC]\d{3}.*.nc",
                                          "metoffice-lidar-als450_faam_\d{8}.*[bBcC]\d{3}.*.nc",]),
                   ('LIF',               ["laquila-lif-['no2','noy'].*faam_\d{8}.*[bBcC]\d{3}.na",]),
                   ('MAN-CAS',           ["man-cas_faam_\d{8}.*[bBcC]\d{3}.*nc",]),
                   ('MAN-CPI',           ["man-cpi_faam_\d{8}.*[bBcC]\d{3}.*.['nc', 'png']",]),
                   ('MAN-AMS',           ["man-ams_faam_\d{8}.*[bBcC]\d{3}.na",]),
                   ('MAN-2DS',           ["man-2ds_faam_\d{8}.*[bBcC]\d{3}.*nc",]),
                   ('MAN-SMPS',          ["man-smps_faam_\d{8}.*['nc', 'na']",]),
                   ('MAN-SP2',           ["man-sp2_faam_\d{8}.*[bBcC]\d{3}.na",]),
                   ('MARSS',             ["metoffice-marss_faam_\d{8}.*[bBcC]\d{3}.nc",]),
                   ('PAN',               ["york-pan-gc_faam_\d{8}.*[bBcC]\d{3}.['na', 'ict']",
                                          "leeds-pan-gc_faam_\d{8}.*[bBcC]\d{3}.['na', 'ict']",]),
                   ('PERCA',             ["leic-perca_faam_\d{8}.*[bBcC]\d{3}.['na', 'ict']",]),
                   ('QCL',               ["man-qcl_faam_\d{8}.*[bBcC]\d{3}.na",]),
                   ('SHIMS',             ["metoffice-['l', 'u']sh_faam_\d{8}.*[bBcC]\d{3}.nc",]),
                   ('SWS',               ["metoffice-sws_faam_\d{8}.*[bBcC]\d{3}.nc",]),
                   ('UEA-GCMS',          ["uea-gc-ms_faam_\d{8}.*[bBcC]\d{3}.['na','ict']",]),
                   ('UEA-NICI',          ["uea-gc-nici-ms_faam_\d{8}.*[bBcC]\d{3}.*['halocarbons', 'nitrates'].na"]),
                   ('UEA-NOXY',          ["uea-noxy_faam_\d{8}.*['na', 'ict']",]),
                   ('UEA-PEROX',         ["uea-peroxides_faam_\d{8}.*[bBcC]\d{3}.*['na', 'ict']",]),
                   ('UEA-PTRMS',         ["uea-ptrms_faam_\d{8}.*[bBcC]\d{3}.*['na','ict']",]),
                   ('UEA-HCHO',          ["uea-hcho_faam_\d{8}.*[bBcC]\d{3}.*.['na','ict']",]),
                   ('VACC',              ["leeds-vacc_faam_\d{8}.*.nc",]),
                   ('VIDEO',             ["faam-video-.*_faam_\d{8}.*[bBcC]\d{3}.*.avi",]),
                   ('WAS',               ["york-gcms_faam_\d{8}.*[bBcCd]\d{3}_was-bottles.na",]),
                   ('WETNEPH',           ["metoffice-wetneph_faam_\d{8}.*[bBcC]\d{3}.*.['nc','zip']",]),
                   ('core-descrip',      ["core_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bBcC][0-9][0-9][0-9]_descrip.txt",]),
                   ('core-quality',      ["core_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bBcC][0-9][0-9][0-9]_quality.txt",]),
                   ('dropsonde-descrip', [".*dropsonde_faam_.*_r.*_[bBcC][0-9][0-9][0-9]_descrip.txt",]),
                   ('flight-cst',        ["flight-cst_faam_20[0-9][0-9][0-1][0-9][0-3][0-9]_r.*_[bBcC][0-9][0-9][0-9].txt",]),
                   ('flight-log',        ["flight-log_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bBcC][0-9][0-9][0-9].pdf",]),
                   ('flight-sum',        ["flight-sum_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bBcC][0-9][0-9][0-9].txt",]),
                   ('rawbuck',           ["core_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bB][0-9][0-9][0-9]_rawbuck.zip",]),
                   ('rawdrs',            ["core_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bB][0-9][0-9][0-9]_rawdrs.zip",]),
                   ('rawgin',            ["core_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bB][0-9][0-9][0-9]_rawgin.zip",]),
                   ('rawgps',            ["core_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bB][0-9][0-9][0-9]_rawgps.zip",]),
                   ('rawdlu',            ["core_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bBcC][0-9][0-9][0-9]_rawdlu.zip",])]


### SETTINGS ###############################################################

# list of file names that should be ignored
NON_DATA_FILES = ['.ftpaccess', '.ftpaccess.org', '.checksums', '.listing', '.summary', '00README', 'ARIES_readme.txt']

DATA_ROOT_PATH = '/home/data/faam/badc'
DATA_ROOT_PATH = '/mnt/faamarchive/badcMirror/data'
DATA_ROOT_PATH = '/home/data/faam/badcMirror'

# if True will print of files that haven't been assorted to an instrument
PRINT_RESIDUALS = False

###########################################################################

result = OrderedDict()
FULL_FILE_LIST = []


# http://stackoverflow.com/questions/1157106/remove-all-occurrences-of-a-value-from-a-python-list
def remove_values_from_list(the_list, val):
   return [value for value in the_list if value != val]


# set up an empty dictionary
keys, v = zip(*instrument_data)
for k in keys:
    result[k] = []

# create a list of all data files in the ROOT_PATH
for root, subFolders, files in os.walk(DATA_ROOT_PATH):
    for f in files:
        FULL_FILE_LIST.append(f)

# remove non relevant files from the NON_DATA_FILES list
for non_data_file in NON_DATA_FILES:
    FULL_FILE_LIST = remove_values_from_list(FULL_FILE_LIST, non_data_file)
    FULL_FILE_LIST = remove_values_from_list(FULL_FILE_LIST, non_data_file + '~')


# loop over all files and append the files to the list with the instrument key
for f in FULL_FILE_LIST:
    for instr, pattern in instrument_data:
        instr_file_list = []
        for p in pattern:
            if re.match(p, os.path.basename(f).lower()):
                # if the filename is a match append it to the list in the dictionary                
                result[instr].append(f)
                # remove the file from the FULL _FILE_LIST
                FULL_FILE_LIST = remove_values_from_list(FULL_FILE_LIST, f)


for k,v in result.items():
    if v:
        fids = [re.findall('[bc]\d{3}', i.lower())[0] for i in v]
        datestring = []
        for i in v:
            if re.findall('_\d{8,}_', i.lower()):
                datestring.append(datetime.strptime(re.findall('_\d{8,}_', i.lower())[0][1:9], '%Y%m%d').strftime('%Y-%m-%d'))
        sys.stdout.write('%20s  %-15s\n' % (k, max(fids)+ 3*' '+max(datestring)))
    else:
        sys.stdout.write('%20s  %-15s\n' % (k, 'EMPTY'))

# Because all matched files were removed from the FULL_FILE_LIST in now only
# contains the residuals. Files that had no match from the regular
# regular expressions
if PRINT_RESIDUALS:
    for f in FULL_FILE_LIST:
        if ((not f.startswith('.')) and (not f.startswith('0')) and (not f.startswith('1'))):
            print(f)
