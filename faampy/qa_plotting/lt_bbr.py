# -*- coding: utf-8 -*-
"""

Quality Assurance-Quality Check (QA-QC) plotting for the FAAM Core Broad Band (pyranometers
and pyrogeometers) Radiometers (BBR)


Layout (landscape):

  -------------------------------------------
  |            Aircraft Heading             |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  | Timeseries of longwave radiation;       |
  |        from pyrgeometers                |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  | Timeseries of shortwave radiation;      |
  |        from pyranometers                |
  -------------------------------------------

Created on Wed Apr 27 10:30:53 2016

@author: Poppy Townsend

"""

import netCDF4
import numpy as np
from matplotlib.dates import num2date
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os


import radiation
from general import get_data
from utils import *
from style import *


VARIABLE_NAMES=['Time',             ## Time of measurement (seconds since midnight on start date)
                'WOW_IND',          ## Weight on wheels indicator
                'IAS_RVSM',
                'SW_DN_C',          ## Corrected downward short wave irradiance, clear dome
                'RED_DN_C',         ## Corrected downward short wave irradiance, red dome
                'SW_UP_C',          ## Corrected upward short wave irradiance, clear dome
                'RED_UP_C',         ## Corrected upward short wave irradiance, red dome
                'IR_UP_C',
                'IR_DN_C',
                'HDG_GIN',          ## Aircraft Heading from the GIN
                'SOL_AZIM',         ## Sun azimuth angle in degrees
                'SOL_ZEN']          ## Sun zenith angle in degrees




from faampy.utils.file_list import File_List
sys.path.insert(0, '/home/axel/git-repos/')


fl = File_List('/mnt/faamarchive/badcMirror/data/')
fl.filter_by_data_type('core-hires')
fl.filter_latest_revision()

from collections import OrderedDict

result = OrderedDict()

import scipy.stats

import qa_plotting.bbr

for f in fl:
    try:
        ds = netCDF4.Dataset(os.path.join(f.path, f.filename))
        data = get_data(ds, VARIABLE_NAMES)
        threshold = 200
        sw_dn = data['SW_DN_C']
        sw_dn[sw_dn < threshold] = np.nan
        red_dn = data['RED_DN_C']
        red_dn[red_dn < 0] = np.nan
        r = red_dn/sw_dn
        r.fill_value = np.nan
        r = r[data['IAS_RVSM'][:,0] > 60]
        r = r.data
        #result[f.fid] = scipy.stats.describe(r, nan_policy='omit')
        #result[f.fid] = np.nanmedian(r)
        result[f.fid] = r
        close('all')
        fig = qa_plotting.bbr.main(ds)
        fig.savefig('/home/axel/qa-bbr_figs/%s_qa-bbr.png' % (ds.FLIGHT))
    except:
        pass
    data = None


boxplot_data = []
for k in result.keys():
    x = result[k].ravel()
    x = x[np.isfinite(x)]
    boxplot_data.append(x)


labels = result.keys()
fig = figure()
ax = fig.add_subplot(111)
bp = ax.boxplot(boxplot_data, patch_artist=True)
ax.set_xticklabels(labels)
ax.set_ylim(0,1)

for median in bp['medians']:
    median.set(color='firebrick', linewidth=3)

for box in bp['boxes']:
    # change outline color
    box.set(color='0.3', linewidth=2)
    # change fill color
    box.set(facecolor='0.65')

for whisker in bp['whiskers']:
    whisker.set(linewidth=2)


