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

bbr_corr = BBR_roll_pitch_correction(df)
bbr_corr.instr = 'UP2'
# make a first rought guess
#bbr_corr.guess_factors(dp_range=(-2, 2, 0.2), dr_range=(-2, 2, 0.2))
# using sliders to fit the two angles
bbr_corr.interactive_fitting()


# Needs the below otherwise program will close without a chance to look at the
# figures
#iput = raw_input('\nPress <RETURN> to exit')
#sys.exit(1)