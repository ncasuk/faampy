#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon May 22 18:32:02 2017

@author: axel
"""

import datetime
import numpy as np
import pandas as pd
import os
import pvlib

import matplotlib.pyplot as plt

from bbr_correction import BBR_roll_pitch_correction


plt.ion()

# Input data file
p = os.path.dirname(os.path.realpath(__file__))
ifile = os.path.join(p, 'Oct_1_2011.xls')


year, month, day = 2011, 10, 1

# reading in data
df = pd.read_excel(ifile)
ts = [datetime.datetime(year, month, day, x.hour, x.minute, x.second) for x in df['TIME(GMT)']]

# create a new dataframe from scratch
df2 = pd.DataFrame()
df2['timestamp'] = ts

# Variable translator, so that Padma's variable names match those that the
# correction code expects
VarTranslator = {' Alt (m)': 'ALT_GIN',
                 'LAT':      'LAT_GIN',
                 'LON':      'LON_GIN',
                 'HDG':      'HDG_GIN',
                 'PITCH':    'PTCH_GIN',
                 'ROLL':     'ROLL_GIN',
                 'RSRT':     'UP1S'}

# add columns to dataframe using FAAM vartiable names as column names
for k, v in VarTranslator.iteritems():
    df2[v] = df[k]

df2 = df2.set_index('timestamp')

# lets do some tidying up; duff data at the beginning
df2[df2.LON_GIN <= 0] = np.nan
df2[df2.PTCH_GIN == 0] = np.nan

coords = zip(df2['LAT_GIN'].values, df2['LON_GIN'].values, df2['ALT_GIN'].values)
locs = [pvlib.location.Location(lat, lon, altitude=alt) for lat, lon, alt in coords]

# calculate the solar position
solarpos = pvlib.solarposition.ephemeris(df2.index, df2['LAT_GIN'], df2['LON_GIN'])

# add Solar parameters
df2['SOL_AZIM'] = solarpos['elevation']
df2['SOL_ZEN'] = solarpos['zenith']
# derive pressure from altitude; altitude is needed for the pvlib clearsky model
df2['PS_RVSM'] = pvlib.atmosphere.alt2pres(df2['ALT_GIN'])*0.01
df2['UP1Z'] = 0


# Skip the first 4000 data rows
df2 = df2[4000:]

bbr_corr = BBR_roll_pitch_correction(df2)
# make a first rought guess
#bbr_corr.guess_factors(dp_range=(-2, 2, 0.2), dr_range=(-2, 2, 0.2))
# using sliders to fit the two angles
#bbr_corr.interactive_fitting()
bbr_corr.dp = 2.0
bbr_corr.drp = 2.0
bbr_corr.recalculate()
bbr_corr.to_csv('test.csv')

#odf = bbr_corr.df.copy()
#odf.merge(bbr_corr.flux_raw)
#odf.merge(bbr_corr.flux_cor)
#odf.merge(bbr_corr.k)
#for k in sorted(bbr_corr.clearsky_irradiance.keys()):
#    odf.merge(bbr_corr.calc_irradiance[k])
#odf.to_csv('/home/axel/test.csv')



#plt.draw()
# Needs the below otherwise program will close without a chance to look at the
# figures
#iput = raw_input('\nPress <RETURN> to exit')
