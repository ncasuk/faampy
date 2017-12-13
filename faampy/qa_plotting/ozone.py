#!/usr/bin/env python
'''

  -------------------------------------------
  |                                         |
  |      Time series of altitude            |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  |      Timeseries of O3_TECO              |
  |                                         |
  |                                         |
  |                                         |
  |                                         |
  |                                         |
  |                                         |
  |                                         |
  -------------------------------------------

'''


import matplotlib as mpl
if __name__ == '__main__': mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np


from general import QaQc_Figure, set_suptitle, get_data, add_takeoff, \
                    add_landing, zoom_to_flight_duration, add_time_buffer
from utils import *
from style import *


# List of variable names that need to be extracted from the data source
VARIABLE_NAMES = ['Time',         # Time of measurement (seconds since midnight on start date)
                  'O3_TECO',      # Static pressure from the aircraft RVSM (air data) system
                  'ALT_GIN',      # GPS Altitude
                  'WOW_IND']      # Weight on wheels indicator


def plot_alt_ts(ax, data):
    """
    Plots the lamp temperature

    """


    ax.set_ylabel('GPS alt (km)')
    ax.plot_date(data['mpl_timestamp'][:, 0].ravel(),
                 data['ALT_GIN'][:, 0].ravel()/1000.,
                 '-', lw=2)
    ax.text(0.05, 0.98,
            'Altitude',
            axes_title_style,
            transform=ax.transAxes)
    plt.setp(ax.get_xticklabels(), visible=False)
    return ax


def plot_o3_ts(ax, data):
    """
    Creates a timeseries plot for cabin temp, cabin pressure,
    and static pressure

    """
    hourloc = mpl.dates.HourLocator()
    xtickformat = mpl.dates.DateFormatter('%H:%M')

    x = data['mpl_timestamp'][:,0]
    y = data['O3_TECO'][:,0]

    x[data['WOW_IND'].ravel() != 0] = np.nan
    y[data['WOW_IND'].ravel() != 0] = np.nan

    ax.plot_date(x, y, '-', label='O3_TECO')
    ax.legend(loc='upper right')
    ax.xaxis.set_major_formatter(xtickformat)
    ax.xaxis.set_major_locator(hourloc)
    ax.set_ylabel('O3 (ppbV)')
    ax.set_xlabel('Time (utc)')
    return ax


def main(ds):
    """

    """

    gs = gridspec.GridSpec(2, 1, hspace=0.05, height_ratios=[1, 4])
    fig = QaQc_Figure(landscape=True).setup()

    fig.add_subplot(gs[1, :])
    fig.add_subplot(gs[0, :], sharex=fig.get_axes()[0])
    set_suptitle(fig, ds, 'QA-O3 TECO')

    data = get_data(ds, VARIABLE_NAMES)

    plot_o3_ts(fig.get_axes()[0], data)
    plot_alt_ts(fig.get_axes()[1], data)

    ax = fig.get_axes()[1]

    zoom_to_flight_duration(ax, data)
    add_time_buffer(ax)

    for ax in fig.get_axes():
        add_takeoff(ax, data)
        add_landing(ax, data)
    return fig
