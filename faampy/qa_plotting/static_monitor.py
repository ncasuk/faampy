#!/usr/bin/env python

'''

  -------------------------------------------
  |                                         |
  |      Timeseries of EXX_JCI              |
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
import numpy as np

from general import add_time_buffer, QaQc_Figure, set_suptitle, get_data, \
                    add_takeoff, add_landing, zoom_to_flight_duration, \
                    adjust_ylim
import style

mpl.rcParams = style.rcParams

#List of variable names that need to be extracted from the data source
VARIABLE_NAMES = ['Time',      # Time of measurement (seconds since midnight on start date)
                  'EXX_JCI',   # Raw counts
                  'WOW_IND']   # Weight on wheels indicator


def plot_timeseries(ax, data):
    """
    Creates a time series plot from the core static field sensor.

    """
    hourloc = mpl.dates.HourLocator()
    xtickformat = mpl.dates.DateFormatter('%H:%M')

    x = data['mpl_timestamp'][:, 0].ravel()
    y = data['EXX_JCI'][:].ravel().astype(np.float32)

    x[data['WOW_IND'].ravel() != 0] = np.nan
    y[data['WOW_IND'].ravel() != 0] = np.nan
    ax.plot_date(x, y, '-', label='EXX_JCI')
    ax.legend(loc='upper right')
    ax.xaxis.set_major_formatter(xtickformat)
    ax.xaxis.set_major_locator(hourloc)
    ax.set_ylabel('EXX JCI (adc counts)')
    ax.set_xlabel('Time (utc)')
    adjust_ylim(ax)
    return ax


def main(ds):
    """

    """

    fig = QaQc_Figure(landscape=True).setup()
    fig.add_subplot(111)

    set_suptitle(fig, ds, 'QA-Static Monitor')

    data = get_data(ds, VARIABLE_NAMES)

    ax = fig.get_axes()[0]

    plot_timeseries(ax, data)
    zoom_to_flight_duration(ax, data)
    add_time_buffer(ax)
    add_takeoff(ax, data)
    add_landing(ax, data)

    fig.canvas.draw()
    return fig
