#!/usr/bin/env python
'''
Created on 15 Mar 2012

@author: axel

Quality Assurance-Quality Check (QA-QC) plotting for the FAAM Core
Nephelometer.


Layout (portrait):

  -------------------------------------------
  |                                         |
  | Timeseries of Neph temp and pressure    |
  |                                         |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  | Timeseries of Neph backscatter          |
  |                                         |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  | Timeseries of Neph total scatter        |
  |                                         |
  -------------------------------------------


'''

import matplotlib as mpl
from matplotlib import gridspec
import numpy as np

from general import *
from utils import *
from style import *

#List of variable names that need to be extracted from the data source
VARIABLE_NAMES = ['NEPH_T',        ## Internal sample temperature of the Nephelometer
                  'NEPH_RH',       ## Internal relative humidity of the Nephelometer
                  'TSC_BLUU',      ## Uncorrected blue total scattering coefficient from TSI 3563 Nephelometer
                  'TSC_GRNU',      ## Uncorrected green total scattering coefficient from TSI 3563 Nephelometer
                  'TSC_REDU',      ## Uncorrected red total scattering coefficient from TSI 3563 Nephelometer
                  'BSC_BLUU',      ## Uncorrected blue back scattering coefficient from TSI 3563 Nephelometer
                  'BSC_GRNU',      ## Uncorrected green back scattering coefficient from TSI 3563 Nephelometer
                  'BSC_REDU',      ## Uncorrected red back scattering coefficient from TSI 3563 Nephelometer
                  'WOW_IND']       ## Weight on wheels indicator


def plot_housekeeping(ax, data):
    """
    Creates timeseries for nephelometer temperature and pressure

    """
    label_text = 'Neph temperature'
    line_neph_t = ax.plot_date(data['mpl_timestamp'][:, 0],
                               data['NEPH_T'][:].ravel(),
                               '-', label='Temp')

    ax.set_ylabel('Temperature (K)')
    ax.tick_params(labelbottom='off')
    lines = line_neph_t

    cc = freeze_color_cycle(ax)
    ax_2 = ax.twinx()
    ax_2.set_color_cycle(cc)

    #ax_2=ax.twinx()
    if data.has_key('NEPH_RH'):
        ax_2.grid(False)
        line_neph_pr = ax_2.plot_date(data['mpl_timestamp'][:, 0],
                                      data['NEPH_RH'][:].ravel(),
                                      '-', label='Rel. Hum')
        ax_2.set_ylabel(r'RH (%)')
        _ylim = list(ax_2.get_ylim())
        _ylim[0] = -5
        ax_2.set_ylim(_ylim)
        label_text = 'Neph temperature and humidity'
        lines = line_neph_t + line_neph_pr

    labs = [l.get_label() for l in lines]
    ax_2.legend(lines, labs, loc='lower right')

    ax_2.text(0.05, 0.98,
              label_text,
              axes_title_style, transform=ax.transAxes)
    return ax


def plot_total_scatter(ax, data):
    """
    Plots total scatter for blue, green and red wavelengths for the nephelometer (timeseries)

    """
    hourloc=mpl.dates.HourLocator()
    xtickformat=mpl.dates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(xtickformat)
    ax.xaxis.set_major_locator(hourloc)

    scale_factor=10000
    ax.plot_date(data['mpl_timestamp'][:,0],
                 data['TSC_BLUU'][:]*scale_factor,
                 '-', label= 'Blue')
    ax.plot_date(data['mpl_timestamp'][:,0],
                 data['TSC_GRNU'][:]*scale_factor,
                 '-', color='#9acd32', label= 'Green')
    ax.plot_date(data['mpl_timestamp'][:,0],
                 data['TSC_REDU'][:]*scale_factor,
                 '-', color='#ff4d4d', label= 'Red')
    ax.set_ylabel('m-1 / %i' % (scale_factor,))
    ax.set_xlabel('Time (utc)')
    ax.text(0.05, 0.98, 'Total Scatter',
            axes_title_style, transform=ax.transAxes)
    ax.legend(loc='upper right')
    return ax


def plot_back_scatter(ax, data):
    """
    Plots back scatter for blue, green and red wavelengths for the nephelometer (timeseries)

    """

    scale_factor = 10000
    ax.plot_date(data['mpl_timestamp'][:,0],
                 data['BSC_BLUU'][:]*scale_factor,
                 '-', label= 'Blue')
    ax.plot_date(data['mpl_timestamp'][:,0],
                 data['BSC_GRNU'][:]*scale_factor,
                 '-', color='#9acd32', label= 'Green')
    ax.plot_date(data['mpl_timestamp'][:,0],
                 data['BSC_REDU'][:]*scale_factor,
                 '-', color='#ff4d4d', label= 'Red')
    ax.set_ylabel('m-1 / %i' % (scale_factor,))
    ax.text(0.05, 0.98, 'Back Scatter',
            axes_title_style, transform=ax.transAxes)
    ax.legend(loc='upper right')
    #plt.setp(ax.get_xticklabels(), visible=False)
    ax.tick_params(labelbottom='off')
    return ax


def main(ds):
    """
    Creates an overview plot for nephelometer for a single flight.

    """

    fig = QaQc_Figure().setup()
    gs = gridspec.GridSpec(10,1)
    fig.add_subplot(gs[6:10,0])
    fig.add_subplot(gs[2:6,0], sharex=fig.get_axes()[0])
    fig.add_subplot(gs[0:2,0], sharex=fig.get_axes()[0])
    #for ax in fig.get_axes():
    #    ax.callbacks.connect('xlim_changed', adjust_ylim)

    set_suptitle(fig, ds, 'QA-Nephelometer')

    data = get_data(ds, VARIABLE_NAMES)
    data['NEPH_T'][data['NEPH_T'] < 250]=np.nan
    data['NEPH_T'][data['NEPH_T'] > 350]=np.nan
    for p in data.keys():
        if p.split('_')[0] in ['BSC', 'TSC']:
            data[p][(data[p] > 0.0001) | (data[p] < -1)] = np.nan

    for ax in fig.get_axes():
        add_takeoff(ax, data)
        add_landing(ax, data)

    plot_total_scatter(fig.get_axes()[0], data)
    plot_back_scatter(fig.get_axes()[1], data)
    plot_housekeeping(fig.get_axes()[2], data)

    ax = fig.get_axes()[0]
    zoom_to_flight_duration(ax, data)
    add_time_buffer(ax)
    fig.canvas.draw()
    return fig
