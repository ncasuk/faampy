#!/usr/bin/env python

'''
Quality Assurance-Quality Check (QA-QC) plotting for the two dew point mirror
instruments (General Eastern (GE) and the BUCK CR2) on the FAAM aircraft.


Layout (portrait):

  -------------------------------------------
  |                                         |
  | Timeseries of GPS ALTITUDE              |
  |                                         |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  | Timeseries of BUCK Volume Mixing Ratio  |
  |                                         |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  | Timeseries of dewpoints GE and BUCK     |
  |                                         |
  -------------------------------------------



'''


import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
if __name__ == '__main__': mpl.use('Agg')
import netCDF4
import numpy as np

from general import *
from utils import *
from style import *

ALPHA=0.7

#List of variable names that needs to be extract from the data source
VARIABLE_NAMES=['VMR_CR2',       ## Water vapour volume mixing ratio measured by the Buck CR2
                'VMR_C_U',       ## Uncertainty estimate for water vapour volume mixing ratio measured by the Buck CR2
                'TDEW_CR2',      ## Mirror Temperature measured by the Buck CR2 Hygrometer
                'TDEW_C_U',      ## Uncertainty estimate for Buck CR2 Mirror Temperature
                'TDEW_GE',       ## Dew point from the General Eastern instrument
                'ALT_GIN',       ## Altitude from POS AV 510 GPS-aided Inertial Navigation unit
                'WOW_IND',       ## Weight on wheels indicator
                'HGT_RADR']      ## Radar height from the aircraft radar altimeter.


def plot_dewpoint(ax, data):
    """
    plotting mirror dew point temperatures for GE and BUCK

    """

    hourloc=mpl.dates.HourLocator()
    xtickformat=mpl.dates.DateFormatter('%H:%M')

    tdew_cr2=data['TDEW_CR2'][:,0]
    tdew_cr2[tdew_cr2 < 0]=np.nan
    ax.plot_date(data['mpl_timestamp'][:,0], tdew_cr2,
                 '-', alpha=ALPHA, label='BUCK')

    ax.plot_date(data['mpl_timestamp'][:,0],
                 data['TDEW_GE'][:,0],
                 '-', alpha=ALPHA, label='GE')
    ax.xaxis.set_major_formatter(xtickformat)
    ax.xaxis.set_major_locator(hourloc)
    ax.legend(loc='upper right')
    ax.set_ylabel('tdew (K)')
    ax.set_xlabel('Time (utc)')
    ax.text(0.05, 0.98,'Dewpoint timeseries', axes_title_style, transform=ax.transAxes)
    return ax


def plot_altitude(ax, data):
    """
    plot altitude timeseries

    """
    ax.plot_date(data['mpl_timestamp'][:,0].ravel(), data['ALT_GIN'][:,0].ravel(), '-', label='ALT_GIN')
    plt.setp(ax.get_xticklabels(), visible=False)
    ax.set_ylabel('Altitude (m)')
    ax.text(0.05, 0.98,'Altitude', axes_title_style, transform=ax.transAxes)
    ax.legend(loc='upper right')
    return ax


def plot_vmr(ax, data):
    """
    plotting the buck data and the calculated uncertainty (timeseries)

    """
    #data['VMR_CR2'].mask[data['TDEW_CR2'] < 0] = True
    #data['VMR_CR2'].fill_value = np.nan
    #plot the uncertainty as a grey shadow below the line

    vmr=np.copy(data['VMR_CR2'])
    vmr_unc=np.copy(data['VMR_C_U'])

    vmr[vmr <= 0]=np.nan
    vmr_unc[vmr <= 0]=np.nan
    vmr_unc[vmr_unc <= 0]=np.nan
    ax.fill_between(data['mpl_timestamp'][:,0],
                    vmr[:,0],
                    vmr[:,0] - vmr_unc[:,0],
                    color='0.4',
                    label= 'uncertainty')
    ax.fill_between(data['mpl_timestamp'][:,0],
                    vmr[:,0],
                    vmr[:,0] + vmr_unc[:,0],
                    color='0.4')
    ax.plot_date(data['mpl_timestamp'][:,0], vmr[:,0], '-', label= 'BUCK')
    plt.setp(ax.get_xticklabels(), visible=False)
    ax.set_ylabel('VMR (ppm)')
    ax.text(0.05, 0.98,'Buck mixing ratio timeseries', axes_title_style, transform=ax.transAxes)
    ax.legend(loc='upper right')
    if ax.get_ylim()[0] < 0:
        ax.set_ylim(0, ax.get_ylim()[1])
    return ax


def main(ds):
    """
    Creates an overview plot for the two dew point mirror instruments
    (i) General Eastern (GE) and the (2) BUCK CR2.

    """

    #Setup up axes layout: 3 axes in one column
    gs=gridspec.GridSpec(3, 1, height_ratios=[1,1,2], hspace=0.05)
    fig=QaQc_Figure().setup()
    fig.add_subplot(gs[0])
    fig.add_subplot(gs[1], sharex=fig.get_axes()[0])
    fig.add_subplot(gs[2], sharex=fig.get_axes()[0])
    for ax in fig.get_axes():
        ax.callbacks.connect('xlim_changed', adjust_ylim)

    set_suptitle(fig, ds, 'QA-BUCK')

    data=get_data(ds, VARIABLE_NAMES)

    #Call the three plotting methods
    plot_altitude(fig.get_axes()[0], data)
    plot_vmr(fig.get_axes()[1], data)
    plot_dewpoint(fig.get_axes()[2], data)

    ax=fig.get_axes()[2]
    zoom_to_flight_duration(ax, data)
    add_time_buffer(ax)

    for ax in fig.get_axes():
        add_takeoff(ax, data)
        add_landing(ax, data)

    return fig
