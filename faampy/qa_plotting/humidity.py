# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 13:46:53 2016

@author: Poppy Townsend

Layout (portrait):

              ----------------
              |   Humidity   |
              |   Scatter    |
              |   plot       |
              |              |
              ----------------
  ---------------------------------------------
  |              Cloud status                 |
  ---------------------------------------------
  ---------------------------------------------
  |                                           |
  |        Timeseries of IAT; deiced,         |
  |           non-deiced, delta               |
  |                                           |
  ---------------------------------------------
  ---------------------------------------------
  |                                           |
  |         Timeseries of TAT  deiced,        |
  |           non-deiced, delta               |
  |                                           |
  ---------------------------------------------


"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

from humidity_formulae import dp2vp, vp2vmr

from utils import *
from general import add_time_buffer, QaQc_Figure, set_suptitle, get_data, \
                    add_takeoff, add_landing, zoom_to_flight_duration, \
                    adjust_ylim
from style import axes_title_style, rcParams

#parameter names used to create the humidity plots
VARIABLE_NAMES = ['ALT_GIN',           # Altitude from POS AV 510 GPS-aided Inertial Navigation unit
                  'WVSS2F_VMR',        # Water Vapour Measurement from Flush inlet WVSSII serial no. 4229 linearly interpolated to 1Hz
                  'WVSS2R_VMR',        # Water Vapour Measurement from Rosemount inlet WVSSII serial no. 0388 linearly interpolated to 1Hz'
                  'VMR_CR2',           # Water vapour volume mixing ratio measured by the Buck CR2
                  'TDEW_GE',           # Dew point from the General Eastern instrument
                  'PS_RVSM',           # Static pressure from the aircraft RVSM (air data) system
                  'TAT_ND_R',          # True air temperature from the Rosemount non-deiced temperature sensor
                  'WOW_IND',           # Weight on wheels indicator
                  'Time',              # Time of measurement (seconds since midnight on start date)
                  'LWC_JW_U',          # Liquid water from the Johnson Williams
                  'NV_LWC_C',          # Nevzorov liquid water calibrated
                  'NV_LWC_U',          # Nevzorov liquid water uncalibrated
                  'AERACK_buck_ppm']   # Raw data from the BUCK CR2


def conv_ge(tdew_ge, ps_rvsm):
    """
    convert tdew to vmr

    """
    vp_ge = dp2vp(tdew_ge)
    vmr_ge = vp2vmr(vp_ge, ps_rvsm)
    vmr_ge = vmr_ge*1E6
    return vmr_ge


def plot_humidity_scatter(ax, data):
    """
    plot for scatter graph WVSS2_R vs other 3 parameters

    """

    x = data['WVSS2R_VMR'][:, 0]
    y1 = data['WVSS2F_VMR'][:, 0]
    y2 = data['VMR_CR2'][:, 0]

    # use only inflight data using weight on wheels
    x[data['WOW_IND'].ravel() != 0] = np.nan
    y1[data['WOW_IND'].ravel() != 0] = np.nan
    y2[data['WOW_IND'].ravel() != 0] = np.nan

    ax.plot(x, y1, '.', label='WVSS2F_VMR')
    ax.plot(x, y2, '.', label='VMR_CR2')

    # converts dew point from GE to volume mixing ratio;
    # so that it matches the other humidity measurements
    tdew_ge = data['TDEW_GE'][:, 0].ravel()
    ps_rvsm = data['PS_RVSM'][:, 0].ravel()
    vmr_ge = conv_ge(tdew_ge, ps_rvsm)
    ax.plot(data['WVSS2R_VMR'][:].ravel(), vmr_ge, '.', label='GE')

    axis_range = (min([ax.get_xlim()[0], ax.get_ylim()[0]]),
                  max([ax.get_xlim()[1], ax.get_ylim()[1]]))
    ax.set_xlim(axis_range)
    ax.set_ylim(axis_range)
    # plot a 1:1 line
    ax.plot([0, 1], [0, 1],
            linestyle='--',
            color=rcParams['grid.color'],
            transform=ax.transAxes)
    ax.text(0.05, 0.98,
            'WVSS2R vs \n   WVSS2F\n   CR2\n   GE',
            axes_title_style, transform=ax.transAxes)

    ax.set_ylabel('VMR (ppb)')
    ax.set_xlabel('VMR (ppb)')
    ax.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    return ax


def plot_lwc(ax, data):
    """
    Plots liquid water content timeseries i.e. cloud status

    """
    plt.setp(ax.get_xticklabels(), visible=False)
    plt.setp(ax.get_yticklabels(), visible=False)
    ax.set_ylabel('lwc')
    ax.set_ylim(0, 1.1)

    if 'LWC_JW_U' in data.keys():
        lwc = data['LWC_JW_U'][:, 0]
    elif 'NV_LWC_C' in data.keys():
        lwc = data['NV_LWC_C'][:, 0]
    elif 'NV_LWC_U' in data.keys():
        lwc = data['NV_LWC_U'][:, 0]
    else:
        return
    lwc = np.clip(lwc, 0, 1)
    ax.plot_date(data['mpl_timestamp'][:, 0], lwc, '-')
    return ax


def plot_alt(ax, data):
    """
    Plots altitude timeseries from the GIN instrument

    """
    ax.plot_date(data['mpl_timestamp'][:].ravel(),
                 data['ALT_GIN'][:].ravel(),
                 '-', label='ALT_GIN')
    plt.setp(ax.get_xticklabels(), visible=False)
    ax.text(0.05, 0.98, 'Altitude', axes_title_style, transform=ax.transAxes)
    ax.set_ylabel('Altitude (m)')
    labels = ax.get_yticklabels()
    labels[-1].set_visible(False)
    return ax


def plot_humidity(ax, data):
    """
    Plots timeseries of 4 instruments that measure humidity:
      WVSS2R
      WVSS2F
      VMR_CR2
      TDEW_GE

    """
    ax.plot_date(data['mpl_timestamp'][:, 0].ravel(),
                 data['WVSS2F_VMR'][:].ravel(),
                 '-', label='WVSS2-F')
    ax.plot_date(data['mpl_timestamp'][:, 0].ravel(),
                 data['WVSS2R_VMR'][:].ravel(),
                 '-', label='WVSS2-R')
    ax.plot_date(data['mpl_timestamp'][:, 0].ravel(),
                 data['VMR_CR2'][:].ravel(),
                 '-', label='VMR_CR2')

    # converts dew point from GE to volume mixing ratio,
    # so that it matches the other humidity measurements
    tdew_ge = data['TDEW_GE'][:, 0].ravel()
    ps_rvsm = data['PS_RVSM'][:, 0].ravel()
    vmr_ge = conv_ge(tdew_ge, ps_rvsm)

    ax.plot_date(data['mpl_timestamp'][:, 0].ravel(),
                 vmr_ge,
                 '-', label='GE')

    ax.text(0.05, 0.98,
            'Humidity timeseries',
            axes_title_style, transform=ax.transAxes)

    hourloc = mpl.dates.HourLocator()
    xtickformat = mpl.dates.DateFormatter('%H:%M')
    ax.xaxis.set_major_locator(hourloc)
    ax.xaxis.set_major_formatter(xtickformat)

    ax.set_xlabel('Time (utc)')
    ax.set_ylabel('Volume Mixing Ratio (ppb)')
    ax.legend(loc='lower right')

    labels = ax.get_yticklabels()
    labels[-1].set_visible(False)
    return ax


def main(ds):
    """
    Creates overview plot for humidity during a single flight

    """
    # Setup up axes layout: 4 axes in one column
    gs = gridspec.GridSpec(2, 1, height_ratios=[1, 4])
    top_cell = gs[0, 0]
    bottom_cell = gs[1, 0]

    gs1 = gridspec.GridSpecFromSubplotSpec(3, 1,
                                           bottom_cell,
                                           height_ratios=[2, 5, 10],
                                           hspace=0.05)

    fig = QaQc_Figure().setup()
    fig.add_subplot(gs1[2, :])
    fig.add_subplot(gs1[1, :], sharex=fig.get_axes()[0])
    fig.add_subplot(gs1[0, :], sharex=fig.get_axes()[0])
    set_suptitle(fig, ds, 'QA-Humidity')

    for ax in fig.get_axes():
        ax.callbacks.connect('xlim_changed', adjust_ylim)

    data = get_data(ds, VARIABLE_NAMES)
    data['VMR_CR2'][data['VMR_CR2'] < 0] = np.nan  # remove unreasonable data
    tdew_ge = data['TDEW_GE'][:, 0].ravel()
    ps_rvsm = data['PS_RVSM'][:, 0].ravel()

    vp_ge = dp2vp(tdew_ge)
    vmr_ge = vp2vmr(vp_ge, ps_rvsm)
    vmr_ge = vmr_ge*1E6

    # call the plotting methods below
    plot_humidity(fig.get_axes()[0], data)
    plot_alt(fig.get_axes()[1], data)
    plot_lwc(fig.get_axes()[2], data)

    # adds grey bar showing take-off/landing and only plots the flight
    ax = fig.get_axes()[0]
    zoom_to_flight_duration(ax, data)
    add_time_buffer(ax)

    for ax in fig.get_axes():
        add_takeoff(ax, data)
        add_landing(ax, data)

    gs2 = gridspec.GridSpecFromSubplotSpec(1, 1, top_cell)
    fig.add_subplot(gs2[0, :], aspect='equal')

    plot_humidity_scatter(fig.get_axes()[3], data)

    fig.canvas.draw()
    return fig
