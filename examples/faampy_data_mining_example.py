#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script finds all FAAM core data files and filters for the latest revision.
The FAAM_Dataset object from the faampy module is used, which makes processing
easier, by synchronizing variables names and adding an artificial WOW FLag for
old flights.

"""

# === Step:Start:Data Mining Extraction ==========================

import os
import netCDF4
import numpy as np

from faampy.core.faam_data import FAAM_Dataset
from faampy.utils.file_list import File_List

# ================================================================

ROOT_DATA_PATH = '/mnt/faamarchive/badcMirror/data/'
OUTFILENAME = os.path.join(os.path.expanduser('~'), 'chemistry_spatial.csv')

# ================================================================

# Get all hires FAAM core data that are in the ROOT_DATA_PATH directory
fl = File_List(ROOT_DATA_PATH)
fl.filter_by_data_type('core-hires')
fl.filter_latest_revision()


def extract(core_netcdf):
    """
    Extracts CO and O3 data from a FAAM core netCDF.

    :param str core_netcdf: FAAM core netCDF file name
    """

    ncfilename = os.path.join(core_netcdf.path, core_netcdf.filename)
    ds = FAAM_Dataset(ncfilename)
    _ds_index = ds.index.ravel()
    units = 'seconds since %s 00:00:00 +0000' % str(_ds_index[0])[:10]
    # create timestamp
    timestamp = netCDF4.num2date(ds.variables['Time'][:].ravel(), units)
    n = timestamp.size

    if 'CO_AERO' in list(ds.variables.keys()):
        co_aero = ds.variables['CO_AERO'][:]
        co_aero_flag = ds.variables['CO_AERO_FLAG'][:]
        co_aero[co_aero_flag != 0] = -9999.0
    else:
        co_aero = np.zeros(n)-9999.0

    if 'O3_TECO' in list(ds.variables.keys()):
        o3_teco = ds.variables['O3_TECO'][:]
        o3_teco_flag = ds.variables['O3_TECO_FLAG'][:]
        o3_teco[o3_teco_flag != 0] = -9999.0
    else:
        o3_teco = np.zeros(n)-9999.0

    # Old FAAM files did not have the GIN instrument fitted
    # if no GIN data are available we use the GPS instrument
    if 'LAT_GIN' in list(ds.variables.keys()):
        lon_var_name = 'LON_GIN'
        lat_var_name = 'LAT_GIN'
        alt_var_name = 'ALT_GIN'
    elif 'LAT_GPS' in list(ds.variables.keys()):
        lon_var_name = 'LON_GPS'
        lat_var_name = 'LAT_GPS'
        alt_var_name = 'GPS_ALT'

    if len(ds.variables[lon_var_name][:].shape) > 1:
        x = ds.variables[lon_var_name][:, 0].ravel()
        y = ds.variables[lat_var_name][:, 0].ravel()
        z = ds.variables[alt_var_name][:, 0].ravel()
    else:
        x = ds.variables[lon_var_name][:].ravel()
        y = ds.variables[lat_var_name][:].ravel()
        z = ds.variables[alt_var_name][:].ravel()

    wow = ds.variables['WOW_IND'][:].ravel()

    timestamp_string = [t.strftime('%Y-%m-%dT%H:%M:%S') for t in timestamp]
    fid = [core_netcdf.fid, ]*n
    result = zip(list(np.array(timestamp_string)[wow == 0]),
                 list(np.array(fid)[wow == 0]),
                 list(x[wow == 0]),
                 list(y[wow == 0]),
                 list(z[wow == 0]),
                 list(co_aero[wow == 0]),
                 list(o3_teco[wow == 0]))
    return result


# open the output file and write the column labels out
ofile = open(OUTFILENAME, 'w')
# write the column names
ofile.write('timestamp,fid,lon,lat,alt,co,o3\n')

# loop over all core files
for core_netcdf in fl:
    print('Working on ... %s' % core_netcdf.fid)
    try:
        data = extract(core_netcdf)
    except:
        print('  Issue with %s ...' % core_netcdf.fid)
        continue

    out_txt = ['%s,%s,%f,%f,%f,%f,%f\n' % l for l in data]
    out_txt = ''.join(out_txt)
    ofile.write(out_txt)
    ofile.flush()

ofile.close()
# === Step:End:Data Mining Extraction ====================================

# === Step:Start:Analysis Violin Plot ====================================
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn

ifile = os.path.join(os.path.join(os.path.expanduser('~'),
                     'faam_chemistry_data_mining.csv')

# read in the csv file that was created in the previous step

df = pd.read_csv(ifile, na_values=[-9999.0,], parse_dates=True, index_col=0)
# Need to do some tidying up; list of all flights that have errorenous
# Ozone data and which have not been flagged properly. This list has been 
# created manually, by looking at the time series of all flights.
faulty_fids = ['b028', 'b069', 'b070', 'b098', 'b105', 'b115', 'b116',
               'b127', 'b138', 'b139', 'b140', 'b141', 'b142', 'b152',
               'b163', 'b166', 'b182', 'b191', 'b258', 'b259', 'b260',
               'b261', 'b262', 'b268', 'b276', 'b284', 'b298', 'b304',
               'b328', 'b332', 'b347', 'b352', 'b353', 'b376', 'b382',
               'b384', 'b386', 'b425', 'b429', 'b475', 'b511', 'b543',
               'b597', 'b645', 'b646', 'b649', 'b665', 'b674', 'b686',
               'b790', 'b791', 'b792', 'b823', 'b829', 'b833', 'b835',
               'b836', 'b886', 'b909', 'b992']

# remove the data from the faulty Flight IDs
for ffid in faulty_fids:
    df = df[df['fid'] != ffid]

# A bit more data cleaning is needed
df = df[(df['alt'] > 0) & (df['alt'] < 12500)]  # remove errorenous alt
df['alt'] = df['alt'].values.clip(0, 11500)     # clipping altitude data
df = df[(df['o3'] > 5) & (df['o3'] < 500)]
df = df[np.isfinite(df['o3'])]

# We are only interested in data points North of 62 deg
df = df[(df['lat'] > 62.) & (df['lat'] < 90.)]

# Binning the altitude data in 100m categories
df['cat_alt'] = pd.cut(df.alt,
                       bins=np.arange(0, 11500, 500),
                       labels=np.arange(250, 11250, 500))

# Create the labels fore the yticks
labels = ['%i' % i for i in np.arange(250, 11250, 500)]

# Extract the data
cat_subsets = []
for x in np.unique(df['cat_alt'].values):
    if np.isfinite(x):
        cat_subsets.append(df[df['cat_alt'] == x]['o3'].values)

fig = plt.figure()
ax = plt.gca()
violins = ax.violinplot(cat_subsets, vert=False,
                        showmedians=True, showmeans=True, showextrema=False)

# Change the layout of some elements of the plot
# https://stackoverflow.com/questions/26291479/changing-the-color-of-matplotlibs-violin-plots
for pc in violins['bodies']:
    pc.set_facecolor('cornflowerblue')
    pc.set_alpha(0.7)
violins['cmeans'].set_color('black')
violins['cmedians'].set_color('0.55')

ax.set_ylim((0, float(len(labels))+0.5))
ax.set_yticks(np.arange(1, len(labels)+1))
ax.set_yticklabels(labels)
ax.set_title('Summary O3 profiles, lat > 62N')
ax.set_xlabel('O3 concentration')
ax.set_ylabel('GPS alt (m)')

# Add the total number of measurements per category to the right hand side
cnt_labels = ['n = %.1fk' % (float(len(s))/1000.) for s in cat_subsets]
axis_to_data = ax.transAxes + ax.transData.inverted()
xpos = axis_to_data.transform((0.95, 0))[0]
for i,cnt_l in enumerate(cnt_labels):
    ax.text(xpos, i+1, cnt_labels[i], va='center', ha='right', fontsize='small')

ax.legend([violins['cmeans'], violins['cmedians']],
          ['mean', 'median'],
          loc=(0.3, 0.01))
plt.tight_layout()
# === Step:Stop:Analysis Violin Plot ====================================
