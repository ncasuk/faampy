#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 07:42:21 2017

@author: axel
"""

import datetime
import pickle
import numpy as np
import os
import sys

from bbr_correction import BBR_roll_pitch_correction


# read in the data
path = os.path.dirname(os.path.realpath(__file__))
data_file = os.path.join(path, 'b978_bbr_correction_data.pickle')
df = pickle.load(open(data_file, "rb"))


# filter data using only the high level box pattern
# remove data during turn
ROLL_THRESHOLD = 0.8
_start =df.index.searchsorted(datetime.datetime(2016, 9, 19, 12, 44, 05))
_end = df.index.searchsorted(datetime.datetime(2016, 9, 19, 13, 4, 00))







df = df.ix[_start:_end]
df = df[np.abs(df.ROLL_GIN) < ROLL_THRESHOLD]


## UP1: Clear dome pyranometer
## UP2: Red dome pyranometer
for var in ['UP1', 'UP2']:
    bbr_cor = BBR_roll_pitch_correction(df)
    bbr_cor.instr = var
    bbr_cor.recalculate()
    bbr_cor.calc_irradiance()
    if var == 'UP1':
        bbr_cor.guess_factors(dp_range=np.arange(2.5, 3.5, 0.05),
                              dr_range=np.arange(-2.0, -0.0, 0.05))
        clear_flux = bbr_cor.flux_cor[:]
    elif var == 'UP2':
        bbr_cor.guess_factors(dp_range=np.arange(2.0, 3.0, 0.05),
                              dr_range=np.arange(-7.0, -6.0, 0.05))
        red_flux = bbr_cor.flux_cor[:]
    else:
        pass
    f = bbr_cor.plot_overview()
    f.show()

# Needs the below otherwise program will close without a chance to look at the
# figures
iput = raw_input('\nPress <RETURN> to exit')
sys.exit(1)