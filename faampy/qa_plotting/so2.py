#!/usr/bin/env python
'''
Created on 21 Jan 2015

@author: axel


  -------------------------------------------
  |                                         |
  |      Timeseries of SO2,                 |
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
import netCDF4
import numpy as np


from general import *
from utils import *
from style import *


#List of variable names that need to be extracted from the data source
VARIABLE_NAMES=['Time',             ## Time of measurement (seconds since midnight on start date)
                'SO2_TECO',         ## Static pressure from the aircraft RVSM (air data) system 
                'WOW_IND']          ## Weight on wheels indicator


def plot_timeseries(ax, data):
    """
    Creates a timeseries plot for cabin temp, cabin pressure and static pressure
    
    """
    hourloc = mpl.dates.HourLocator()
    xtickformat = mpl.dates.DateFormatter('%H:%M')

    x=data['mpl_timestamp'][:,0]
    y=data['SO2_TECO'][:,0]

    x[data['WOW_IND'].ravel() != 0]=np.nan
    y[data['WOW_IND'].ravel() != 0]=np.nan
    #ax.plot_date(data['mpl_timestamp'][:,0], data['SO2_TECO'][:].ravel(), '-')
    ax.plot_date(x, y, '-', label='SO2_TECO')
    ax.legend()
    ax.xaxis.set_major_formatter(xtickformat)
    ax.xaxis.set_major_locator(hourloc)
    ax.set_ylabel('SO2 (ppmV)')
    ax.set_xlabel('Time (utc)')
    autoscale_y(ax)
    return ax


def main(ds):
    """

    """
    
    fig=QaQc_Figure(landscape=True).setup()
    fig.add_subplot(111)

    set_suptitle(fig, ds, 'QA-SO2 TECO')
    
    data=get_data(ds, VARIABLE_NAMES)
    
    ax=fig.get_axes()[0]

    plot_timeseries(ax, data)

    zoom_to_flight_duration(ax, data)
    add_time_buffer(ax)

    add_takeoff(ax, data)
    add_landing(ax, data)

    return fig    
    
#plt.close('all')
#ncfile = './data/core_faam_20160303_v004_r0_b947.nc'
#ds = netCDF4.Dataset(ncfile, 'r')
#fig = main(ds)
    
#ds=d
#fig=main(ds)    
#import glob2
#file_list=glob2.glob('/home/axel/MONSOON2016/*/core_faam_*b9??.nc', 'r')
#file_list=sorted(file_list)
#for f in file_list:
#    print(f[0])
#    ds=netCDF4.Dataset(f[0], 'r')
#    fig = main(ds)
#    fig.savefig('/home/axel/%s_qa-so2.png' % (ds.FLIGHT))
#    ds.close()
