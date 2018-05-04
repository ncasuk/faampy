# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 15:29:46 2016

@author: Poppy Townsend


Quality Assurance-Quality Check (QA-QC) plotting for the FAAM Core Rosemount Temperature sensors,
deiced and non-deiced models.


Layout (portrait):

  -------------   -------------  --------------
  |   Scatter  |  | Histogram |  |  Power     |
  |   plot     |  | of delta  |  |  Spectrum  |
  |   of IAT   |  |   IAT     |  |            |
  -------------   -------------  --------------
  ---------------------------------------------
  |           Deiced Heater status            |
  ---------------------------------------------
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

import numpy as np
import matplotlib as mpl
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from general import QaQc_Figure, \
                    set_suptitle, get_data, add_takeoff, add_landing, \
                    zoom_to_flight_duration, add_time_buffer
from utils import freeze_color_cycle
from style import rcParams, axes_title_style


#parameter names used in this script to plot temperature graphs
VARIABLE_NAMES = ['Time',        ## Time of measurement (seconds since midnight on start date)
                  'ITDI',        ## DEICED IND TEMP
                  'NDTI',        ## NONDEICED IND TEMP
                  'TAT_DI_R',    ## True air temperature from the Rosemount deiced temperature sensor
                  'TAT_ND_R',    ## True air temperature from the Rosemount non-deiced temperature sensor
                  'WOW_IND',     ## Weight on wheels indicator
                  'PRTAFT_deiced_temp_flag',
                  'LWC_JW_U']


def power_spectrum(data, *args):
    """
    calculates the power spectrum

    """
    if args:
        freq = args[0]
    else:
        freq = data.shape[1]

    ps = np.abs(np.fft.fft(data.ravel()))**2
    time_step = 1./freq
    freqs = np.fft.fftfreq(data.size, time_step)
    idx = np.argsort(freqs)
    return(freqs[idx], ps[idx])


def running_mean(x, N):
    return np.convolve(x, np.ones((N,))/N)[(N-1):]


def plot_power_spectrum(ax, data):
    """
    plots the power spectrum

    """
    #ixs = (np.min(np.where(data['WOW_IND'][:].filled() == 0)[0]),
    #       np.max(np.where(data['WOW_IND'][:].filled() == 0)[0]))
    ixs=[None, None]
    ixs[0] = np.where((data['WOW_IND'][:].ravel() == 0) &
                      (np.min(data['TAT_DI_R'], axis=1) > 0) &
                      (np.min(data['TAT_ND_R'], axis=1) > 0))[0][0]
    ixs[1] = np.where((data['WOW_IND'][:].ravel() == 0) &
                      (np.min(data['TAT_DI_R'], axis=1) > 0) &
                      (np.min(data['TAT_ND_R'], axis=1) > 0))[0][-1]

    freqs, ps_tat_di_r = power_spectrum(data['TAT_DI_R'][ixs[0]:ixs[1],:])
    freqs, ps_tat_nd_r = power_spectrum(data['TAT_ND_R'][ixs[0]:ixs[1],:])

    freqs = freqs[:-1]
    ps_tat_di_r = ps_tat_di_r[:-1]
    ps_tat_nd_r = ps_tat_nd_r[:-1]

    for ps in [ps_tat_di_r, ps_tat_nd_r]:
        ax.plot(freqs[freqs < 15.5], running_mean(ps, 200)[freqs < 15.5])

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_ylim(1, 10**3)
    ax.set_xlim(1, 16)
    xticks=[1,2,3,4,5,6,8,10,16]
    ax.set_xticks(np.array(xticks))
    ax.set_xticklabels([str(i) for i in xticks])
    ax.text(0.05, 0.98,
            'Power Spectrum',
            axes_title_style, transform=ax.transAxes)
    return ax


#plotting deiced vs non-deiced indicated air temp (scatter plot)
def plot_iat_scatter(ax, data):
    """
    plots scatter graph for deiced and non-deiced indicated air temp

    """
    ####due to the 32hz measuring frequency of rosemount we use '[:]' - this plots it with the 32hz mpl_timestamp size
    if 'NDTI' in data:
        ax.plot(data['NDTI'][:, 0].ravel(),
                data['ITDI'][:, 0].ravel(),
                '.', color='#9acd32')
    #plot 1-to-1 dashed line with same colour as the grid
    ax.plot(ax.get_xlim(),
            ax.get_ylim(),
            linestyle='--', color=rcParams['grid.color'])
    #axes title located top left of axes. follows the format as described in the style module under axes_title_style
    ax.text(0.05, 0.98, 'IAT_DI vs IAT_ND', axes_title_style, transform=ax.transAxes)
    ax.set_xlabel('Non-deiced (K)')
    ax.set_ylabel('Deiced (K)')

    ##sets every other tick label to be hidden
    for label in ax.get_xticklabels()[::2]:
        label.set_visible(False)
    for label in ax.get_yticklabels()[::2]:
        label.set_visible(False)
    return ax


def plot_iat_histogram(ax, data):
    """
    plotting delta IAT (histogram)

    """
    if 'NDTI' not in list(data.keys()):
        return
    delta_iat = data['ITDI'][:].ravel() - data['NDTI'][:].ravel()

    _range=(-4.0, 4.0)
    _step_size=0.1
    _bins= np.arange(_range[0], _range[1], _step_size)
    freq, bin_edges = np.histogram(delta_iat, bins=_bins, range=_range)
    #freq=float(freq)/delta_iat.size
    freq=freq.astype(np.float32)/delta_iat.size*100.
    ax.bar((_bins[0:-1]+_bins[1:])/2.0, freq, width=_step_size, alpha=0.8, color='#ff4d4d')
    ax.set_xlim((_range[0], _range[1]))
    ax.text(0.05, 0.98,r'$\Delta$ IAT', axes_title_style, transform=ax.transAxes)
    ax.set_ylabel('percentage (%)')
    ax.set_xlabel(r'$\Delta$ IAT')
    return ax


def plot_iat(ax, data):
    """
    plot timeseries of indicated air temp; deiced, non-deiced and delta

    """
    if 'NDTI' not in data.keys():
        labels = ax.get_yticklabels()
        labels[-1].set_visible(False)
        return
    line1 = ax.plot_date(data['mpl_timestamp'][:, 0].ravel(),
                         data['ITDI'][:, 0].ravel(),
                         '-', label='deiced')
    line2 = ax.plot_date(data['mpl_timestamp'][:,0].ravel(),
                         data['NDTI'][:,0].ravel(),
                         '-', label='non-deiced')

    cc = freeze_color_cycle(ax)
    ax_a=ax.twinx()
    ax_a.set_color_cycle(cc)

    delta_iat = data['ITDI'][:].ravel()-data['NDTI'][:].ravel()
    ax_a.grid(False)
    ax_a.set_ylabel(r'$\Delta$ IAT (K)')
    line3 = ax_a.plot_date(data['mpl_timestamp'][:].ravel(), delta_iat, '-', label=r'$\Delta$')

    ax_a.text(0.05, 0.98,'Indicated air temperature', axes_title_style, transform=ax.transAxes)
    ax.set_ylabel('IAT (K)')
    plt.setp(ax.get_xticklabels(),visible=False)

    lines = line1+line2+line3
    labs = [l.get_label() for l in lines]
    ax_a.legend(lines,labs, loc='lower right')
    labels=ax.get_yticklabels()
    labels[-1].set_visible(False)
    return ax


def plot_tat(ax,data):
    """
    plot timeseries of true air temp; deiced, non-deiced and delta

    """
    line1, = ax.plot_date(data['mpl_timestamp'][:,0].ravel(), data['TAT_DI_R'][:,0].ravel(), '-', label='deiced')
    line2, = ax.plot_date(data['mpl_timestamp'][:,0].ravel(), data['TAT_ND_R'][:,0].ravel(), '-', label='non-deiced')

    cc=freeze_color_cycle(ax)
    ax_a=ax.twinx()
    ax_a.set_color_cycle(cc)

    delta_tat = data['TAT_DI_R'][:,0].ravel()-data['TAT_ND_R'][:,0].ravel()
    line3, = ax_a.plot_date(data['mpl_timestamp'][:,0].ravel(), delta_tat, '-', label='$\Delta$')

    ax_a.grid(False)
    ax_a.text(0.05, 0.98,'True air temperature', axes_title_style, transform=ax.transAxes)
    ax_a.set_ylabel(r'$\Delta$ TAT (K)')
    ax.set_ylabel('TAT (K)')
    ax.set_xlabel('Time (utc)')

    hourloc = mpl.dates.HourLocator()
    xtickformat = mpl.dates.DateFormatter('%H:%M')
    ax.xaxis.set_major_locator(hourloc)
    ax.xaxis.set_major_formatter(xtickformat)
    labels=ax.get_yticklabels()
    labels[-1].set_visible(False)

    lines = [line1,line2,line3]
    labs = [l.get_label() for l in lines]
    ax_a.legend(lines,labs, loc='lower right')
    return ax


def plot_lwc(ax, data):
    """
    plots liquid water content timeseries i.e. cloud status

    """
    if 'LWC_JW_U' in list(data.keys()):
        lwc = data['LWC_JW_U'][:, 0]
        lwc = np.clip(lwc, 0, 1)
    else:
        n = len(data['mpl_timestamp'][:,0])
        lwc = np.zeros(n)*np.nan
    plt.setp(ax.get_xticklabels(), visible=False)
    plt.setp(ax.get_yticklabels(), visible=False)
    ax.plot_date(data['mpl_timestamp'][:, 0], lwc, '-')
    ax.set_ylabel('lwc')
    ax.set_ylim(0, 1.1)
    return ax


def plot_heater(ax, data):
    """
    plots deiced heater status i.e. ON/OFF

    """
    if not 'PRTAFT_deiced_temp_flag' in data:
        return
    ax.text(0.05, 0.98,'Heater', axes_title_style, transform=ax.transAxes)
    ax.grid(False)
    ax.set_ylim(0,1)
    ax.yaxis.set_major_locator(plt.NullLocator())
    plt.setp(ax.get_xticklabels(), visible=False)
    heater_status = np.array(data['PRTAFT_deiced_temp_flag'], dtype=np.int8)
    heater_status[data['WOW_IND'] == 1] = 0
    toggle = np.diff(heater_status.ravel())
    time_periods=zip(list(np.where(toggle == 1)[0]),
                     list(np.where(toggle == -1)[0]))
    for t in time_periods:
        #plt.barh(0, data['mpl_timestamp'][0,1], left=data['mpl_timestamp'][0,0])
        width=data['mpl_timestamp'][t[1],0]-data['mpl_timestamp'][t[0],0]
        ax.add_patch(patches.Rectangle((data['mpl_timestamp'][t[0],0], 0), width, 1, alpha=0.8, color='#ffaf4d'))
    return ax


def main(ds):
    """
    Creates an overview plot for the Rosemount temperature sensors; deiced and non-deiced sensors.
    It calls all plotting functions and sets up axes layout.

    """
    # Setup up axes layout: 3 axes in one column
    gs = gridspec.GridSpec(2, 1, height_ratios=[1,4])
    top_cell = gs[0,0]
    bottom_cell = gs[1,0]

    gs1 = gridspec.GridSpecFromSubplotSpec(4, 1, bottom_cell,
                                           height_ratios=[1, 1, 10, 10],
                                           hspace=0.05)

    fig = QaQc_Figure().setup()
    ax_tat_ts = fig.add_subplot(gs1[3])                                # axes for true air temperature time series
    ax_iat_ts = fig.add_subplot(gs1[2], sharex=fig.get_axes()[0])      # axes for indicated air temperature time series
    ax_lwc_ts = fig.add_subplot(gs1[1], sharex=fig.get_axes()[0])      # axes for cloud indicator
    ax_heater_ts = fig.add_subplot(gs1[0], sharex=fig.get_axes()[0])   # axes for heater indicator

    gs2=gridspec.GridSpecFromSubplotSpec(1,3, top_cell, hspace=0.15)
    ax_scatter = fig.add_subplot(gs2[0], aspect='equal')               # axes for scatter plot
    ax_hist = fig.add_subplot(gs2[1])                                  # axes for histogram
    ax_ps = fig.add_subplot(gs2[2])                                    # axes for power spectrum

    set_suptitle(fig, ds, 'QA-Temperature')

    data = get_data(ds, VARIABLE_NAMES)
    for var in ['ITDI', 'NDTI', 'TAT_DI_R', 'TAT_ND_R']:
        data[var][data[var] <= 0] = np.nan

    # call all plotting methods
    plot_tat(ax_tat_ts, data)
    plot_iat(ax_iat_ts, data)
    plot_lwc(ax_lwc_ts, data)
    plot_heater(ax_heater_ts, data)
    plot_iat_scatter(ax_scatter, data)
    plot_iat_histogram(ax_hist, data)
    plot_power_spectrum(ax_ps, data)

    for ax in fig.get_axes()[0:4]:
        add_takeoff(ax, data)
        add_landing(ax, data)

    ax=fig.get_axes()[0]
    zoom_to_flight_duration(ax, data)
    add_time_buffer(ax)
    return fig

#ds = netCDF4.Dataset('D:\\netcdf-test-files\\temperature_qa_extract_20160215_b943.nc', 'r')
#plt.close('all')
#ds = netCDF4.Dataset('./data/temperature_qa_extract_20160215_b943.nc', 'r')
#ds=d
#fig = main(ds)
#data=get_data(ds, VARIABLE_NAMES)
#close('all')
#fig=figure()
#ax=gca()
#plot_power_spectrum(ax, data)
#fig.savefig('/home/axel/test.png')