#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 21 09:26:50 2017

@author: axel
"""


#=== Step:Begin:Setup==========================================================

import datetime
import os
import numpy as np
import pandas as pd
import faampy
from faampy.core.faam_data import FAAM_Dataset

year, month, day = 2016, 10, 24
FID = 'b991'

core_file = os.path.join(faampy.FAAMPY_EXAMPLE_DATA_PATH,
                         'b991',
                         'core',
                         'core_faam_20161024_v004_r0_b991.nc')

fltsumm_file = os.path.join(faampy.FAAMPY_EXAMPLE_DATA_PATH,
                            'b991',
                            'core',
                            'flight-sum_faam_20161024_r0_b991.txt')

#=== Step:End:Setup============================================================


#=== Step:Begin:Reading in data ===============================================

# define the input data file
nox_file = os.path.join(faampy.FAAMPY_EXAMPLE_DATA_PATH,
                        'b991',
                        'chem_data',
                        'NOx_161024_090507')

# defining the function that calculates the timestamp
nox_dateparse = lambda x: pd.datetime(year, month, day) + \
      datetime.timedelta(seconds=int(float(float(x) % 1)*86400.))

df_nox = pd.read_csv(nox_file, parse_dates=[0], date_parser=nox_dateparse)
df_nox = df_nox.set_index('TheTime')  # Setting index
t = df_nox.index.values
df_nox['timestamp'] = t.astype('datetime64[s]')  # Converting index data type
df_nox = df_nox[['timestamp', 'no_conc', 'no2_conc', 'nox_conc']]
df_nox[df_nox < 0] = np.nan


# Now the FGGA data.

from faampy.data_io.chem import read_fgga
fgga_file = os.path.join(faampy.FAAMPY_EXAMPLE_DATA_PATH,
                         'b991',
                         'chem_data',
                         'FGGA_20161024_092223_B991.txt')

df_fgga = read_fgga(fgga_file)

# Using the valve states for flagging out calibration periods
df_fgga.loc[df_fgga['V1'] != 0, 'ch4_ppb'] = np.nan
df_fgga.loc[df_fgga['V2'] != 0, 'co2_ppm'] = np.nan
df_fgga.loc[df_fgga['V2'] != 0, 'ch4_ppb'] = np.nan


# Reading in the FAAM core data file using the FAAM_Dataset object from the
# faampy module

ds = FAAM_Dataset(core_file)

#=== Step:End:Reading in data =================================================


#=== Step:Start:Merging data ==================================================

# merge chemistry data with the core data set
# The delay keyword is used to set off the chemistry measurements. Due to fact
# that the air has to travel through tubings in the cabine those instruments
# are slower than e.g compared to the temperature measurements
ds.merge(df_nox.to_records(convert_datetime64=False), index='timestamp', delay=3)
ds.merge(df_fgga.to_records(convert_datetime64=False), index='timestamp', delay=4)

# define variable list, that we like to extract
var_list = ['Time', 'LAT_GIN', 'LON_GIN', 'ALT_GIN', 'HGT_RADR',
            'CO_AERO', 'U_C', 'V_C', 'W_C', 'U_NOTURB', 'V_NOTURB',
            'WOW_IND', 'TAT_DI_R', 'TDEW_GE', 'PS_RVSM', 'ch4_ppb', 'co2_ppm',
            'no_conc', 'no2_conc', 'nox_conc', 'TSC_BLUU', 'TSC_GRNU',
            'TSC_REDU', 'BSC_BLUU', 'BSC_GRNU', 'BSC_REDU', 'IAS_RVSM']

# write the netcdf out to you HOME directory
outfile = os.path.join(os.path.expanduser('~'), '%s_merged.nc' % (FID.lower()))
ds.write(outfile,
         clobber=True,
         v_name_list=var_list)

#=== Step:End:Merging data ====================================================


#=== Step:Begin:Create google-earth profiles ==================================

from faampy.mapping import ge_ncvar_to_kml

# We are now continuing to work with the merged data file, that was produced
# in the previous step

core_file2 = os.path.join(os.path.expanduser('~'), '%s_merged.nc' % (FID.lower()))

opath = os.path.expanduser('~')

ge_ncvar_to_kml.process(core_file2, 'CO_AERO', 0, -100, 500, opath)
ge_ncvar_to_kml.process(core_file2, 'co2_ppm', 0, -435, 1500, opath)
ge_ncvar_to_kml.process(core_file2, 'ch4_ppb', 0, -2115, 500, opath)

#=== Step:End:Create google-earth profiles ====================================


#=== Step:Begin:Quicklook Figures =============================================

from faampy.plotting import quicklooks

quicklooks._CATS = [[['TSC_BLUU', 'TSC_GRNU' , 'TSC_REDU'], ['BSC_BLUU', 'BSC_GRNU', 'BSC_REDU']],
                    [['CO_AERO'],],
                    [['ch4_ppb'], ['co2_ppm']],
                    [['no_conc'], ['no2_conc'], ['nox_conc']]]

# define the outpath, where all the figures should be saved to
quicklooks_outpath = os.path.join(os.path.expanduser('~'), 'b991_quicklooks')

quicklooks.process(fltsumm_file,
                   core_file2,
                   quicklooks_outpath)

#=== Step:End:Quicklook Figures ===============================================


#=== Step:Begin:Coloured Line  ================================================

import numpy as np
import datetime
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import os
from matplotlib.collections import LineCollection

from faampy.core.faam_data import FAAM_Dataset

cities = [('Liverpool', 53.410565, -2.992983),
         ('Manchester', 53.484538, -2.242493),
         ('Blackpool',  53.817770, -3.035729),
         ('Preston',    53.763530, -2.703519),
         ('Southport',  53.648671, -3.007051),
         ('Burnley',    53.789179, -2.238926),
         ('Blackburn',  53.748788, -2.488308)]

### SETTINGS ##################################################################

# Define map extent
ymin = 53.2
ymax = 54.0
xmin = -3.5
xmax = -2.0

FID = 'b991'
year, month, day = 2016, 10, 24


_RUNS = [('Run 2@100ft',  '121217', '122142'),
         ('Run 3@500ft',  '122257', '122937'),
         ('Run 4@1000ft', '123134', '124152'),
         ('Run 5@1000ft', '124305', '125133')]

_run = _RUNS[0]

VARIABLE_NAME = 'nox_conc'
# rng for chemical
rng = (0, 30000)

###############################################################################



#http://nbviewer.jupyter.org/github/dpsanders/matplotlib-examples/blob/master/colorline.ipynb
def colorline(x, y, z=None, cmap=plt.get_cmap('copper'),
              norm=plt.Normalize(0.0, 1.0), linewidth=3, alpha=1.0):
    """
    Plot a colored line with coordinates x and y
    Optionally specify colors in the array z
    Optionally specify a colormap, a norm function and a line width
    """

    # Default colors equally spaced on [0,1]:
    if z is None:
        z = np.linspace(0.0, 1.0, len(x))

    z = np.asarray(z)

    segments = make_segments(x, y)
    lc = LineCollection(segments, array=z, cmap=cmap, norm=norm, linewidth=linewidth, alpha=alpha)
    ax = plt.gca()
    ax.add_collection(lc)
    return lc


def make_segments(x, y):
    """
    Create list of line segments from x and y coordinates, in the correct
    format for LineCollection:
    an array of the form   numlines x (points per line) x 2 (x and y) array
    """
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    return segments


core_file2 = os.path.join(os.path.expanduser('~'), '%s_merged.nc' % (FID.lower()))

ds = FAAM_Dataset(core_file2)
df = ds.as_dataframe()

# define the map
wgs84 = ccrs.PlateCarree() #  we need
proj = ccrs.OSGB()  # this is the standard map projection for Great Britain
ax = plt.axes(projection=proj)
ax.set_extent([xmin, xmax, ymin, ymax])
ax.coastlines(resolution='10m', color='black', linewidth=1)

for city in cities:
    x, y = proj.transform_point(city[2], city[1], wgs84)
    ax.scatter(x, y, color='grey')
    ax.text(x, y, city[0], horizontalalignment='right')


coords = proj.transform_points(wgs84,
                               df['LON_GIN'].values,
                               df['LAT_GIN'].values)
x = coords[:,0]
y = coords[:,1]

z = df[VARIABLE_NAME].values


start_time = datetime.datetime(year, month, day, int(_run[1][0:2]), int(_run[1][2:4]), int(_run[1][4:6]))
end_time = datetime.datetime(year, month, day, int(_run[2][0:2]), int(_run[2][2:4]), int(_run[2][4:6]))

ixs = [np.where(df.index == start_time)[0][0],
       np.where(df.index == end_time)[0][0]]

x = x[ixs[0]:ixs[1]]
y = y[ixs[0]:ixs[1]]
z = z[ixs[0]:ixs[1]]

#http://matplotlib.org/examples/pylab_examples/multicolored_line.html
lc = colorline(x, y, z=z,
               cmap=plt.get_cmap('gnuplot2'),
               norm=plt.Normalize(rng[0], rng[1]),
               linewidth=5)

df_30s = df[ixs[0]:ixs[1]].resample('30s').mean()

coords = proj.transform_points(wgs84,
                               df_30s['LON_GIN'].values,
                               df_30s['LAT_GIN'].values)
x = coords[:,0]
y = coords[:,1]

u, v = (df_30s['U_C'].values, df_30s['V_C'].values)
plt.barbs(x, y, u, v,
          length=7,
          barbcolor='k',
          flagcolor='k',
          linewidth=0.5,
          zorder=2)

#cbar_ax=plt.gca()
#cb = colorbar(lc, label="NOx (ppt)", cax=cbar_ax)

#=== Step:End:Coloured Line ===================================================


#=== Step:Begin:Transect Figure ===============================================

#=== Step:End:Transect Figure =================================================
