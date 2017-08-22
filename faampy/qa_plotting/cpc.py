#!/usr/bin/env python
'''
Created on 15 Mar 2012

@author: axel

Quality Assurance-Quality Check (QA-QC) plotting for the FAAM Core Nephelometer.



'''

import matplotlib as mpl
from matplotlib import gridspec
import matplotlib.pyplot as plt
import netCDF4
import numpy as np
import scipy.ndimage

from general import *
from utils import *
from style import *

#List of variable names that need to be extracted from the data source
VARIABLE_NAMES = ['CPC378_counts',
                  'CPC378_saturator_temp',
                  'CPC378_growth_tube_temp',
                  'CPC378_optics_temp',
                  'CPC378_pressure',
                  'CPC378_sample_flow',
                  'CPC378_sheath_flow',
                  'CPC378_total_flow',
                  'Time',
                  'WOW_IND']



def plot_flows(ax, data):
    """
    Creates timeseries for nephelometer temperature and pressure
    
    """
    
    
    line_total_flow = ax.plot_date(data['mpl_timestamp'][:].ravel(), data['CPC378_total_flow'][:].ravel(),'-', label='total')
    ax.set_ylim(500,650)
    cc=freeze_color_cycle(ax)
    ax_2=ax.twinx()
    ax_2.set_color_cycle(cc) 
    
    line_sample_flow = ax_2.plot_date(data['mpl_timestamp'][:].ravel(), data['CPC378_sample_flow'][:].ravel(),'-', label='sample')
    line_sheath_flow = ax_2.plot_date(data['mpl_timestamp'][:].ravel(), data['CPC378_sheath_flow'][:].ravel(),'-', label='sheath')
    plt.setp(ax.get_xticklabels(), visible=False)
    plt.setp(ax.get_xticklabels(), visible=False)
    lines = line_total_flow + line_sample_flow + line_sheath_flow
    labs = [l.get_label() for l in lines]
    ax_2.grid(False)
    ax_2.legend(lines, labs)
    ax_2.set_ylim(250,350)
    ax.text(0.05, 0.98, 'CPC Flows', axes_title_style, transform=ax.transAxes)
    return ax
 



def plot_temperatures(ax, data):
    """
    Plots total scatter for blue, green and red wavelengths for the nephelometer (timeseries)
    
    """
    
    line_growth_tube = ax.plot_date(data['mpl_timestamp'][:].ravel(), data['CPC378_growth_tube_temp'][:].ravel(),'-', label='growth_tube')
    line_optics = ax.plot_date(data['mpl_timestamp'][:].ravel(), data['CPC378_optics_temp'][:].ravel(),'-', label='optics')
    cc=freeze_color_cycle(ax)
    ax_2=ax.twinx()
    ax_2.set_color_cycle(cc)     
    line_saturator = ax_2.plot_date(data['mpl_timestamp'][:].ravel(), data['CPC378_saturator_temp'][:].ravel(),'-', label='saturator')    
    ax_2.grid(False)
    plt.setp(ax.get_xticklabels(), visible=False)
    lines = line_growth_tube + line_optics + line_saturator
    labs = [l.get_label() for l in lines]
    ax_2.legend(lines,labs)
    ax.text(0.05, 0.98, 'CPC Temperatures', axes_title_style, transform=ax.transAxes)
    return ax


def plot_counts(ax, data):
    """

    
    """
    hourloc=mpl.dates.HourLocator()
    xtickformat=mpl.dates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(xtickformat)
    ax.xaxis.set_major_locator(hourloc)
    
    cnts=data['CPC378_counts'][:]
    ix=np.where(data['WOW_IND'][:].ravel() == 1)[0]    
    cnts[ix,:]=np.nan
    ax.plot_date(data['mpl_timestamp'][:].ravel(), cnts.ravel(), '-')
    ax.set_ylim((0, np.nanmax(cnts)))
    ax.set_ylabel('#')
    ax.set_xlabel('Time (utc)')
    ax.text(0.05, 0.98, 'CPC', axes_title_style, transform=ax.transAxes)
    return ax

    
def main(ds):
    """
    Creates an overview plot for nephelometer for a single flight.

    """
   
    fig=QaQc_Figure().setup()
    gs=gridspec.GridSpec(10,1)
    fig.add_subplot(gs[6:10,0])
    fig.add_subplot(gs[3:6,0], sharex=fig.get_axes()[0])
    fig.add_subplot(gs[0:3,0], sharex=fig.get_axes()[0])
    
    set_suptitle(fig, ds, 'CPC3781')
    
    data=get_data(ds, VARIABLE_NAMES)
    data['CPC378_counts'][data['CPC_counts'] > 1000000] = np.nan
    #the CPC data are 10Hz; we need to resize and interpolate the mpl_timestamp for plotting
    data['mpl_timestamp'] = scipy.ndimage.interpolation.zoom(input=data['mpl_timestamp'], zoom=[1, (10./32.)], order=1)
    
    for ax in fig.get_axes():
        add_takeoff(ax, data)
        add_landing(ax, data)    
    
    plot_counts(fig.get_axes()[0], data)
    plot_temperatures(fig.get_axes()[1], data)
    plot_flows(fig.get_axes()[2], data)
        
    ax=fig.get_axes()[0]    
    zoom_to_flight_duration(ax, data)
    add_time_buffer(ax)
    
    
    return fig


#plt.close('all')
#ncfile = './data/core_faam_20160303_v004_r0_b947.nc'
#ds = netCDF4.Dataset(ncfile, 'r')
#ds=d
#fig = main(ds)