# -*- coding: utf-8 -*-
"""

Quality Assurance-Quality Check (QA-QC) plotting for the FAAM Core Broad Band (pyranometers
and pyrogeometers) Radiometers (BBR)


Layout (landscape):

  -------------------------------------------
  |            GPS Altitude                 |
  -------------------------------------------
  -------------------------------------------
  |            Sun position                 |
  -------------------------------------------
  |                                         |
  |   Timeseries of longwave radiation;     |
  |          from pyrgeometers              |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  |   Timeseries of shortwave radiation;    |
  |          from pyranometers              |
  -------------------------------------------

Created on Wed Apr 27 10:30:53 2016

@author: Poppy Townsend

"""

import netCDF4
import numpy as np
import pandas as pd
from matplotlib.dates import num2date
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pytz

from general import *
from utils import *
from style import *


VARIABLE_NAMES=['Time',             # Time of measurement (seconds since midnight on start date)
                'WOW_IND',          # Weight on wheels indicator
                'ALT_GIN',          # GPS altitude from the GIN
                'LON_GIN',          # GPS longitude from the GIN
                'LAT_GIN',          # GPS latitude from the GIN
                'PS_RVSM',          # static pressure
                'SW_DN_C',          # Corrected downward short wave irradiance, clear dome
                'RED_DN_C',         # Corrected downward short wave irradiance, red dome
                'SW_UP_C',          # Corrected upward short wave irradiance, clear dome
                'RED_UP_C',         # Corrected upward short wave irradiance, red dome
                'IR_UP_C',          # Corrected upward longwave irradiance (CGR4)
                'IR_DN_C',          # Corrected downward longwave irradiance (CGR4)
                'HDG_GIN',          # Aircraft Heading from the GIN
                'SOL_AZIM',         # Sun azimuth angle in degrees
                'SOL_ZEN']          # Sun zenith angle in degrees


def calc_sun_position(data):
    """
    Creates time series plot for the sun position.
      0: sun on the nose
     90: sun starboard
    180: sun on the tail
    270: sun on port side

    :param ax: axes object
    :param data: data dictionary

    """
    # sun position in reference to the aircraft heading
    # 0: sun on the nose; 90: sun starboard; 180: sun from behind; 270: sun on port side
    sp=data['SOL_AZIM'][:].ravel()-data['HDG_GIN'][:,0].ravel()
    sp[sp < 0]+=360.0
    data['sun_position'] = sp
    return data


def plot_sun_position(ax, data):
    """
    Creates time series plot for the sun position.
      0: sun on the nose
     90: sun starboard
    180: sun on the tail
    270: sun on port side

    :param ax: axes object
    :param data: data dictionary

    """
    # sun position in reference to the aircraft heading
    # 0: sun on the nose; 90: sun starboard; 180: sun from behind; 270: sun on port side

    ax.plot_date(data['mpl_timestamp'][:,0].ravel(), data['sun_position'], '-', lw=2, label='Sun position')
    ax.set_ylim(0, 360)
    ax.yaxis.set_ticks(np.arange(0.0, 361.0, 90.0))
    ax.legend(loc='upper right')
    plt.setp(ax.get_xticklabels(), visible=False)
    return ax


def calc_clearsky_irradiance(data, step=30):
    # see: http://pvlib-python.readthedocs.io/en/latest/index.html


    try:
        import pvlib
        PVLIB_MODULE = True
    except:
        PVLIB_MODULE = False
        print('module pvlib not available ...')
        return data

    times = mpl.dates.num2date(data['mpl_timestamp'][:,0].ravel())
    # pvlib needs a pandas DatetimeINdex
    times = pd.DatetimeIndex(times)

    # TODO: See if we should read in masked arrays
    #idata = zip(data['LAT_GIN'][::step, 0].filled(),
    #            data['LON_GIN'][::step, 0].filled(),
    #            data['ALT_GIN'][::step, 0].filled(),
    #            data['PS_RVSM'][::step, 0].filled()*100.,  # convert to Pascal
    #            times[::step])

    idata = zip(data['LAT_GIN'][::step, 0],
                data['LON_GIN'][::step, 0],
                data['ALT_GIN'][::step, 0],
                data['PS_RVSM'][::step, 0]*100.,  # convert to Pascal
                times[::step])

    n = len(idata)
    # TODO: Need to find sensible values for those two parameters
    aod700 = [0.02]*n
    precipitable_water = [0.5]*n

    apparent_elevation = [float(pvlib.solarposition.get_solarposition(t, lat, lon, altitude=alt)['apparent_elevation']) for lat, lon, alt, press, t in idata]
    lat, lon, alt, press, times = zip(*idata)
    dayofyear = [t.dayofyear for t in times]
    dni_extra = [pvlib.irradiance.extraradiation(d) for d in dayofyear]

    iput = zip(apparent_elevation, aod700, precipitable_water, press, dni_extra)

    solis = [pvlib.clearsky.simplified_solis(i[0], i[1], i[2], i[3], i[4]) for i in iput]
    # see https://firstgreenconsulting.wordpress.com/2012/04/26/differentiate-between-the-dni-dhi-and-ghi/
    ghi = [s['ghi'] for s in solis]  # global horizontal irradiance
    dni = [s['dni'] for s in solis]  # direct normal irradiance
    dhi = [s['dhi'] for s in solis]  # diffuse horizontal irradiance
    data['clearsky_irradiance_ghi'] = ghi
    data['clearsky_irradiance_dni'] = dni
    data['clearsky_irradiance_dhi'] = dhi
    data['clearsky_irradiance_stepsize'] = step
    return data


def plot_altitude(ax, data):
    """
    Time series plot of the GPS altitude

    :param ax: axes object
    :param data: data dictionary
    """
    alt = data['ALT_GIN'][:,0].ravel()/1000.
    ax.plot_date(data['mpl_timestamp'][:,0].ravel(), alt, '-', lw=2, label='GPS alt')
    ax.set_ylabel('alt (km)')
    ax.legend(loc='upper right')
    plt.setp(ax.get_xticklabels(), visible=False)
    return ax


def plot_clearsky_irradiance(ax, data):
    # see: http://pvlib-python.readthedocs.io/en/latest/index.html

    step = data['clearsky_irradiance_stepsize']
    _ylim=ax.get_ylim()
    timestamp = data['mpl_timestamp'][::step,0].ravel()
    ghi = data['clearsky_irradiance_ghi']
    ax.plot_date(timestamp, ghi, '-', color='0.3', lw=4, label='max irradiance', alpha=0.5)
    ax.set_ylim(_ylim)


def plot_pyranometers_ts(ax, data):
    """
    Time series plot for the fitted pyranometers (clear & red).

    :param ax: axes object
    :param data: data dictionary
    """
    pars = [('SW_DN_C',  'downward, clear dome'),
            ('RED_DN_C', 'downward, red dome'),
            ('SW_UP_C',  'upward, clear dome'),
            ('RED_UP_C', 'upward, red dome')]

    for p in pars:
        if p[0] in data.keys():
            ax.plot_date(data['mpl_timestamp'][:,0].ravel(), data[p[0]][:,0].ravel(), '-', label=p[1])
    ax.legend(loc='upper right')
    ax.text(0.05, 0.98, 'Pyranometers - corrected shortwave irradiance', axes_title_style, transform=ax.transAxes)
    ax.set_ylabel('Irradiance (W m -2)')
    ax.set_xlabel('Time (utc)')
    ylim = ax.get_ylim()
    if ylim[0] < -50:
        ax.set_ylim(-50, ylim[1])
    ylim = ax.get_ylim()
    if ylim[1] > 1500:
        ax.set_ylim(ylim[0], 1500)
    hourloc = mpl.dates.HourLocator()
    xtickformat = mpl.dates.DateFormatter('%H:%M')
    ax.xaxis.set_major_locator(hourloc)
    ax.xaxis.set_major_formatter(xtickformat)
    return ax


def plot_pyrgeometers_ts(ax,data):
    """
    Creates timeseries plot for the pyrgeometers

    """
    # these are yet to be fitted; will update to include when ready.
    plt.setp(ax.get_xticklabels(),visible=False)
    ax.text(0.05, 0.98,
            'Pyrgeometers - corrected longwave irradiance',
            axes_title_style,
            transform=ax.transAxes)
    ax.set_ylabel('Irradiance (W m -2)')
    ax.legend()
    return ax


def main(ds):
    """
    Creates an overview plot for the BBR instruments; pyranometers and pyrogeometers.
    It calls all plotting functions and sets up axes layout.

    """

    data = get_data(ds, VARIABLE_NAMES)
    data = calc_sun_position(data)
    data = calc_clearsky_irradiance(data)

    # Check if Pyrgeometer data are available
    pyrgeometers_fitted = False
    try:
        pyrgeometer_data = np.array(data['IR_DN_C'])
        pyrgeometer_data = pyrgeometer_data[(pyrgeometers_data > 0) & \
                                            (pyrgeometer_data < 200)]

        if pyrgeometer_data.size > 3600:
             pyrgeometers_fitted = True
        else:
            pyrgeometers_fitted = False
    except:
        pass

    if pyrgeometers_fitted:
        gs = gridspec.GridSpec(4, 1, wspace=0.05, height_ratios=[1, 1, 4, 4])
        fig = QaQc_Figure(landscape=True).setup()

        fig.add_subplot(gs[3,:])
        fig.add_subplot(gs[2,:], sharex = fig.get_axes()[0])
        fig.add_subplot(gs[1,:], sharex = fig.get_axes()[0])
        fig.add_subplot(gs[0,:], sharex = fig.get_axes()[0])
        plot_pyranometers_ts(fig.get_axes()[0], data)
        if 'clearsky_irradiance_ghi' in data.keys():
            plot_clearsky_irradiance(fig.get_axes()[0], data)
        plot_pyrgeometers_ts(fig.get_axes()[1], data)
        plot_sun_position(fig.get_axes()[2], data)
        plot_altitude(fig.get_axes()[3], data)
    else:
        gs = gridspec.GridSpec(3, 1, wspace=0.1, height_ratios=[1, 1, 6])
        fig = QaQc_Figure(landscape=True).setup()

        fig.add_subplot(gs[2,:])
        fig.add_subplot(gs[1,:])
        fig.add_subplot(gs[0,:], sharex=fig.get_axes()[0])
        plot_pyranometers_ts(fig.get_axes()[0], data)
        if 'clearsky_irradiance_ghi' in data.keys():
            plot_clearsky_irradiance(fig.get_axes()[0], data)
        plot_sun_position(fig.get_axes()[1], data)
        plot_altitude(fig.get_axes()[2], data)

    for ax in fig.get_axes():
        ax.callbacks.connect('xlim_changed', adjust_ylim)

    set_suptitle(fig, ds, 'QA-Broadband Radiometers')

    ax = fig.get_axes()[0]
    zoom_to_flight_duration(ax, data)
    add_time_buffer(ax)

    # adds grey bar showing takeoff/landing and only plots the flight
    for ax in fig.get_axes():
        add_takeoff(ax, data)
        add_landing(ax, data)

    return fig
