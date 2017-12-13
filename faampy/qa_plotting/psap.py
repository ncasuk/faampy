# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 13:46:53 2016

@author: Poppy Townsend

Quality Assurance-Quality Check (QA-QC) plotting for the FAAM CORE Particle Soot Absorption Photometer (Radiance Research)

Layout (landscape):

  -------------------------------------------
  |                                         |
  | Timeseries of PSAP LIN_FLAG             |
  |                                         |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  | Timeseries of PSAP flow                 |
  |                                         |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  | Timeseries of psap-lin & psap-log       |
  |                                         |
  -------------------------------------------



"""

import netCDF4
import numpy as np
import datetime
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from general import *
from utils import *
from style import *

#parameter names used to create the PSAP plots
VARIABLE_NAMES=['PSAP_FLO',         ## PSAP Flow
                'PSAP_LOG',         ## Uncorrected absorption coefficient at 565nm, log, from PSAP
                'PSAP_LIN',         ## Uncorrected absorption coefficient at 565nm, linear, from PSAP
                'Time',             ## Time of measurement (seconds since midnight on start date)
                'PSAP_FLO_FLAG',    ## Flag for PSAP Flow
                'PSAP_LOG_FLAG',    ## Flag for Uncorrected absorption coefficient at 565nm, log, from PSAP
                'PSAP_LIN_FLAG',    ## Flag for Uncorrected absorption coefficient at 565nm, linear, from PSAP
                'WOW_IND']          ## Weight on wheels indicator


def plot_psap_lin_flag(ax,data):
    """
    Plots PSAP_LIN_FLAG timeseries

    """
    ##due to the measuring frequency we use '[:,0]' for the timestamp so that it matches the 1hz frequency from psap
    ax.plot_date(data['mpl_timestamp'][:,0].ravel(), data['PSAP_LIN_FLAG'][:].ravel(), '-', color='#9acd32', label = 'psap_lin_flag')

    plt.setp(ax.get_xticklabels(),visible=False)

    ax.set_ylabel('flag (-)')
    ax.set_ylim(-0.2,3.2)
    ax.legend(loc='upper right')
    ax.text(0.05, 0.98,'psap-lin flag', axes_title_style, transform=ax.transAxes)
    return ax


def plot_psap_flo(ax,data):
    """
    Plots timeseries of PSAP_FLO

    """
    ax.plot_date(data['mpl_timestamp'][:,0].ravel(), data['PSAP_FLO'][:].ravel(), '-', color='#ff4d4d', label = 'psap_flo')

    plt.setp(ax.get_xticklabels(),visible=False)
    ax.set_ylabel('flow (l m-1)')
    ax.set_ylim(-0.2,4)
    ax.legend(loc='upper right')
    ax.text(0.05, 0.98,'psap flow', axes_title_style, transform=ax.transAxes)
    return ax


def plot_psap(ax,data):
    """
    Plots time series for PSAP_LIN and PSAP_LOG

    """
    line1, = ax.plot_date(data['mpl_timestamp'][:,0].ravel(),
                          data['PSAP_LIN'][:].ravel()*10E5,
                          '-', label='psap_lin')

    hourloc = mpl.dates.HourLocator()
    xtickformat = mpl.dates.DateFormatter('%H:%M')
    ax.xaxis.set_major_locator(hourloc)
    ax.xaxis.set_major_formatter(xtickformat)

    ax.set_ylabel('psap_lin/10E5 (m-1)')
    ax.set_xlabel('Time (utc)')

    cc=freeze_color_cycle(ax)
    ax_a=ax.twinx()
    ax_a.set_color_cycle(cc)

    ax_a.grid(False)
    line2, = ax_a.plot_date(data['mpl_timestamp'][:,0].ravel(),
                            data['PSAP_LOG'][:].ravel()*10E5,
                            '-', label='psap_log')
    ax_a.set_ylabel('psap_log/10E5 (-) ')

    lines = [line1, line2]       #have to set the legend like this due to the shared x-axis; normal legend will only show one parameter
    labs = [l.get_label() for l in lines]
    ax_a.legend(lines, labs, loc='upper right')
    ax.text(0.05, 0.98,
            'psap-lin & psap-log',
            axes_title_style,
            transform=ax.transAxes)
    return ax


def main(ds):
    """
    Creates overview plot for PSAP for a single flight

    """
    # Setup up axes layout: 3 axes in one column
    gs = gridspec.GridSpec(3, 1, wspace=0.1, height_ratios=[1,1,2])
    fig=QaQc_Figure(landscape=True).setup()

    fig.add_subplot(gs[2,:])
    fig.add_subplot(gs[1,:], sharex=fig.get_axes()[0])
    fig.add_subplot(gs[0,:], sharex=fig.get_axes()[0])

    ax = fig.get_axes()[2]
    ax.callbacks.connect('xlim_changed', adjust_ylim)

    set_suptitle(fig, ds, 'QA-PSAP')   #sets main plot title    ##TO DO: make this bigger/bolder?

    data=get_data(ds, VARIABLE_NAMES)

    #Call the plotting methods below:
    plot_psap(fig.get_axes()[0],data)
    plot_psap_flo(fig.get_axes()[1],data)
    plot_psap_lin_flag(fig.get_axes()[2],data)

    #adds grey bar showing takeoff/landing and only plots the flight
    ax=fig.get_axes()[0]
    zoom_to_flight_duration(ax, data)
    add_time_buffer(ax)

    for ax in fig.get_axes():
        add_takeoff(ax, data)
        add_landing(ax, data)

    fig.canvas.draw()
    return fig
