# -*- coding: utf-8 -*-
"""

Quality Assurance-Quality Check (QA-QC) plotting for the FAAM Core Broadband
Radiometers (BBRs, pyranometers and pyrogeometers)


Layout (landscape):

  -------------------------------------------
  |            GPS Altitude                 |
  -------------------------------------------
  -------------------------------------------
  |            Sun position                 |
  -------------------------------------------
  |                                         |
  |   Time series of longwave radiation;    |
  |          from pyrgeometers              |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  |   Time series of shortwave radiation;   |
  |          from pyranometers              |
  -------------------------------------------

Created on Wed Apr 27 10:30:53 2016

@author: Poppy Townsend

"""

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import sys

from general import *
from utils import *
from style import *


VARIABLE_NAMES = ['Time',     ## Time of measurement (seconds since midnight on start date)
                  'WOW_IND',  ## Weight on wheels indicator
                  'ALT_GIN',  ## GPS altitude from the GIN
                  'IR_UP_C',  ## Corrected upward longwave irradiance (CGR4)
                  'IR_DN_C',  ## Corrected downward longwave irradiance (CGR4)
                  'BTHEIM_U']  ## Sun zenith angle in degrees



def plot_altitude(ax, data):
    """
    Time series plot of the GPS altitude

    :param ax: axes object
    :param data: data dictionary
    """
    alt = data['ALT_GIN'][:, 0].ravel()/1000.
    ax.plot_date(data['mpl_timestamp'][:, 0].ravel(), alt, '-', lw=2, label='GPS alt')
    ax.set_ylabel('alt (km)')
    ax.legend(loc='upper right')
    plt.setp(ax.get_xticklabels(), visible=False)
    return ax


def plot_clearsky_irradiance(ax, data):
    # see: http://pvlib-python.readthedocs.io/en/latest/index.html

    step = data['clearsky_irradiance_stepsize']
    _ylim = ax.get_ylim()
    timestamp = data['mpl_timestamp'][::step, 0].ravel()
    ghi = data['clearsky_irradiance_ghi']
    ax.plot_date(timestamp, ghi,
                 '-', color='0.3', lw=4, label='max irradiance', alpha=0.5)
    ax.set_ylim(_ylim)


def plot_pyrgeometers_ts(ax, data):
    """
    Time series plot for the fitted pyranometers (clear & red).

    :param ax: axes object
    :param data: data dictionary
    """
    pars = [('IR_DN_C',  'downward'),
            ('IR_UP_C', 'upward')]

    for p in pars:
        if p[0] in data.keys():
            ax.plot_date(data['mpl_timestamp'][:, 0].ravel(),
                         data[p[0]][:, 0].ravel(),
                         '-', label=p[1], lw=2)
    ax.legend(loc='upper right')
    ax.text(0.05, 0.98,
            'Pyrgeometers - corrected longwave irradiance',
            axes_title_style, transform=ax.transAxes)
    ax.set_ylabel('Irradiance (W m -2)')
    ax.set_xlabel('Time (utc)')
    yl = ax.get_ylim()
#    if yl[0] < -50:
#        ax.set_ylim(-50, yl[1])
#    if yl[1] > 1500:
#        ax.set_ylim(yl[0], 1500)
    hourloc = mpl.dates.HourLocator()
    xtickformat = mpl.dates.DateFormatter('%H:%M')
    ax.xaxis.set_major_locator(hourloc)
    ax.xaxis.set_major_formatter(xtickformat)
    return ax

def plot_heimann_ts(ax, data):
    emissivity = 0.9
    bt = data['BTHEIM_U'][:, 0].ravel()
    bt_watt = bt**4 * 5.670367 * 10**-8 * emissivity
    ax.plot_date(data['mpl_timestamp'][:, 0].ravel(), bt_watt, '-', lw=2, label='Heimann')
    ax.set_ylabel('?? (W m-2)')
    ax.legend(loc='upper right')
    plt.setp(ax.get_xticklabels(), visible=False)
    return ax



def main(ds):
    """
    Creates an overview plot for the BBR instruments; pyranometers and pyrogeometers.
    It calls all plotting functions and sets up axes layout.

    """

    data = get_data(ds, VARIABLE_NAMES)

    # Check if Pyrgeometer data are available
    pyrgeometers_fitted = False
    try:
        pyrgeometer_data = np.array(data['IR_DN_C'])
        pyrgeometer_data = pyrgeometer_data[(pyrgeometers_data > 100) & \
                                            (pyrgeometer_data < 400)]

        if pyrgeometer_data.size > 3600:
             pyrgeometers_fitted = True
        else:
            pyrgeometers_fitted = False
    except:
        pass

    pyrgeometers_fitted = True

    if pyrgeometers_fitted:
        gs = gridspec.GridSpec(3, 1, wspace=0.05, height_ratios=[1, 2, 3,])
        fig = QaQc_Figure(landscape=True).setup()

        fig.add_subplot(gs[2, :])
        fig.add_subplot(gs[1, :], sharex=fig.get_axes()[0], sharey=fig.get_axes()[0])
        fig.add_subplot(gs[0, :], sharex=fig.get_axes()[0])
        #plot_pyranometers_ts(fig.get_axes()[0], data)
        plot_pyrgeometers_ts(fig.get_axes()[0], data)
        #plot_sun_position(fig.get_axes()[2], data)
        plot_heimann_ts(fig.get_axes()[1], data)
        plot_altitude(fig.get_axes()[2], data)
    else:
        return

    # adjust ylim for GIN_ALT figure
    fig.get_axes()[-1].callbacks.connect('xlim_changed', adjust_ylim)

    set_suptitle(fig, ds, 'QA-Pyrgeometers')

    ax = fig.get_axes()[0]
    zoom_to_flight_duration(ax, data)
    add_time_buffer(ax)


    # adds grey bar showing takeoff/landing and only plots the flight
    for ax in fig.get_axes():
        add_takeoff(ax, data)
        add_landing(ax, data)
    fig.canvas.draw()
    return fig
