#!/usr/bin/env python
'''
Quality Assurance-Quality Check (QA-QC) plotting for the cabin pressure and
cabin temperature on the FAAM aircraft. Also includes static pressure from
the aircraft RVSM (air data) system for control.


Layout (landscape):

  -------------------------------------------
  |                                         |
  |      Timeseries of cabin pressure,      |
  |       cabin temperature and static      |
  |       pressure                          |
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
import numpy as np

from general import freeze_color_cycle, QaQc_Figure, adjust_ylim, \
                    set_suptitle, get_data, add_takeoff, add_landing, \
                    zoom_to_flight_duration, add_time_buffer
from utils import *
from style import *


#List of variable names that need to be extracted from the data source
VARIABLE_NAMES=['Time',             # Time of measurement (seconds since midnight on start date)
                'PS_RVSM',          # Static pressure from the aircraft RVSM (air data) system
                'CAB_PRES',         # Cabin pressure
                'CAB_TEMP',         # Cabin temperature at the core consoles
                'WOW_IND']          # Weight on wheels indicator


def plot_timeseries(ax, data):
    """
    Creates a timeseries plot for cabin temp, cabin pressure and static pressure

    """
    hourloc = mpl.dates.HourLocator()
    xtickformat = mpl.dates.DateFormatter('%H:%M')

    line1 = ax.plot_date(data['mpl_timestamp'][:,0], data['CAB_PRES'][:].ravel(), '-', label='Cabin pressure')
    line2 = ax.plot_date(data['mpl_timestamp'][:].ravel(), data['PS_RVSM'][:].ravel(),'-', label='Static pressure')
    ax.xaxis.set_major_formatter(xtickformat)
    ax.set_ylabel('Pressure (mb)')
    ax.set_xlabel('Time (utc)')

    cc = freeze_color_cycle(ax)
    ax_r = ax.twinx()
    ax_r.set_color_cycle(cc)

    line3 = ax_r.plot_date(data['mpl_timestamp'][:,0], data['CAB_TEMP'][:,0], '-', label='Cabin temperature')

    ax_r.set_ylabel('Cabin Temperature (C)')
    ax_r.grid(False)
    ax_r.xaxis.set_major_locator(hourloc)
    ax_r.xaxis.set_major_formatter(xtickformat)

    lines = line1+line2+line3
    labs = [l.get_label() for l in lines]
    ax.legend(lines, labs, loc='lower left')
    return ax


def main(ds):
    """
    Creates an overview plot for cabin pressure and cabin temperature.

    """

    fig = QaQc_Figure(landscape=True).setup()
    fig.add_subplot(111)
    for ax in fig.get_axes():
        ax.callbacks.connect('xlim_changed', adjust_ylim)

    set_suptitle(fig, ds, 'QA-Cabin Pressure/Temperature')

    data = get_data(ds, VARIABLE_NAMES)
    data['CAB_PRES'][(data['CAB_PRES'] > 1050) | (data['CAB_PRES'] < 700)] = np.nan
    data['PS_RVSM'][(data['PS_RVSM'] > 1080) | (data['PS_RVSM'] < 220)] = np.nan
    ax = fig.get_axes()[0]

    plot_timeseries(ax, data)

    zoom_to_flight_duration(ax, data)
    add_time_buffer(ax)

    add_takeoff(ax, data)
    add_landing(ax, data)
    return fig

#plt.close('all')
#ncfile = './data/core_faam_20160303_v004_r0_b947.nc'
#ds = netCDF4.Dataset(ncfile, 'r')
#ds=d
#fig = main(ds)