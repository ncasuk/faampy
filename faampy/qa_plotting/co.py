"""
Decades processing routine for processing the data stream from the AERO AL5002 instrument.

Variables available are:

 AL52CO_cal_status
 AL52CO_calpress
 AL52CO_cellpress
 AL52CO_conc
 AL52CO_counts
 AL52CO_err
 AL52CO_flight_num
 AL52CO_lampflow
 AL52CO_lamptemp
 AL52CO_monoflow
 AL52CO_monopress
 AL52CO_monotemp
 AL52CO_packet_length
 AL52CO_ptp_sync
 AL52CO_sens
 AL52CO_temppmt
 AL52CO_ue9LJ_temp
 AL52CO_utc_time
 AL52CO_zero


Carbon Monoxide concentrations are calculated by linearly interpolation of the
zero and sens values inbetween calibrations.

The concentration of the calibration gas might be revised after a campaign and
therefore the CO concentration needs to be scaled. This is taken care off by a
scaling factor which is the fourth number in the CALCOMX flight constant. If
the scaling factor is not available it is assumed to be 1.0.

Data are flagged as "3" if either the AL52CO_cal_status flag is "1" or if the
pressure in the calibration chamber (AL52CO_calpress) exceeds as defined
threshold (3.4).

Layout (landscape):

  -------------------------------------------
  |                                         |
  |      Time series lamp temperature       |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  |      Timeseries of CO raw,              |
  |      CO interpolated, CO delta          |
  |      and Calibration                    |
  |                                         |
  |                                         |
  |                                         |
  -------------------------------------------

"""


import datetime

import time
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.dates import date2num, num2date, DateFormatter, HourLocator
import numpy as np

from general import *
from utils import *
from style import *


VARIABLE_NAMES = ['CO_AERO',              # Mole fraction of Carbon Monoxide in air from the AERO AL5002 instrument
                  'AL52CO_conc',          # Reading in signed decimal for CO Signal (ppb)
                  'AL52CO_sens',          # Detector sensitivity (Hz/ppb)
                  'AL52CO_zero',          # Detector background (Hz)
                  'AL52CO_calpress',      # CO/air calibrant gas pressure (bar); Honeywell Press Transducer model SA
                  'AL52CO_lamptemp',      # UV Lamp temperature
                  'WOW_IND',              # Weight on wheels indicator
                  'Time']                 # Time of measurement (seconds since midnight on start date)


def plot_lamptemp_ts(ax, data):
    """
    Plots the lamp temperature

    """
    plt.setp(ax.get_xticklabels(), visible=False)

    ax.set_ylabel('temp (degC)')
    ax.set_ylim(34, 38)
    ax.plot_date(data['mpl_timestamp'][:, 0].ravel(),
                 data['AL52CO_lamptemp'][:].ravel(),
                 '-', color='#ff4d4d')
    ax.text(0.05, 0.98, 'Lamp Temp', axes_title_style, transform=ax.transAxes)
    return ax


def plot_co_ts(ax, data):
    """Creates an overview plot, that shows the CO timeseries before and after
    the interpolation of the calibration coefficients.

    On the second y-axis the CO delta is plotted. Calibration periods are
    indicated by black dots.

    """

    ts=data['mpl_timestamp'][:,0].ravel()
    co_orig=data['AL52CO_conc']
    co_interp=data['CO_AERO']

    #cal_status=np.zeros(co_orig.shape)
    #cal_status[data['AL52CO_calpress'] > 2.0]=1
    # add time buffer to cal_status
    calpress=data['AL52CO_calpress'][:].ravel()
    cal_status=np.zeros(data['AL52CO_calpress'].shape)

    cal_status_ix=np.where((calpress > 3.4))[0]
    # add time buffer to cal_status
    cal_status_buffer=8
    for i in range(cal_status_buffer*-1, cal_status_buffer+1):
        cal_status_ix=list(set(list(np.concatenate((np.array(cal_status_ix), np.array(cal_status_ix)+i)))))
    cal_status_ix=np.array(cal_status_ix)
    cal_status_ix=cal_status_ix[cal_status_ix < len(cal_status)]
    cal_status_ix=list(cal_status_ix)
    cal_status[cal_status_ix]=1
    cal_status=cal_status.reshape((cal_status.size, 1))

    perc = np.percentile(co_orig, [2, 98])
    co_orig_clean = co_orig[:]
    co_orig_clean[(co_orig_clean > perc[1]) |
                  (co_orig_clean < 0) |
                  (cal_status == 1)] = np.nan

    ax.plot_date(ts, co_orig_clean, '-')
    yl = ax.get_ylim()
    plt.cla()
    line1 = ax.plot_date(ts, co_orig, '-', label='CO raw')
    co_interp[cal_status == 1] = np.nan
    line2 = ax.plot_date(ts, co_interp, '-', label='CO interp')

    ax.set_ylim(yl)
    ax.set_xlabel('Time (utc)')
    ax.set_ylabel('CO mixing ratio (ppbV)')
    ax.xaxis.set_major_locator(HourLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    ax.xaxis.grid(True)

    cc = freeze_color_cycle(ax)
    ax_r = ax.twinx()
    ax_r.set_color_cycle(cc)

    line3 = ax_r.plot_date(ts, co_orig-co_interp, '-', label=r'CO $\Delta$')
    ax_r.set_ylim(-10, 10)
    ax_r.set_ylabel(r'CO $\Delta$')
    ax_r.grid(False)

    # overplot time periods when instrument is calibrating
    cal_status_ix=np.where(cal_status == 1)[0]
    if len(cal_status_ix > 0):
        line4 = plt.plot_date(ts[cal_status_ix],
                              ts[cal_status_ix]*0.0,
                              'o', markersize=8, color='black', label='Cal')

    if 'line4' in locals():
        lines = line1+line2+line3+line4
    else:
        lines = line1+line2+line3
    labs = [l.get_label() for l in lines]
    ax_r.legend(lines,labs)
    return ax


def get_cal_coefficients(data):
    """The calibration coefficients for the AL5002 instrument drift
    inbetween calibrations. It is assumed that the drifting is linear
    and too take account of this new coefficients are calculated for
    each data point, which are then used to recalculate the CO concentrations.

    """

    sens = data['AL52CO_sens'].ravel()
    zero = data['AL52CO_zero'].ravel()
    utc_time = [time.mktime(num2date(i).timetuple()) for \
                i in data['mpl_timestamp'][:,0]]
    # create copies of sens and zero calibration coefficients
    sens_new, zero_new = sens[:], zero[:]
    # get calibration periods
    ix=np.where(sens[1:]-sens[:-1] != 0)[0]
    # remove nan values
    ix=ix[~np.isnan((sens[1:]-sens[:-1])[ix])]
    # ignore the first 100 data points
    ix=ix[ix>100]
    # the +2 is a dodgy way to make sure that the values have changed.
    # Apparently the zero and sens parameters do not change at
    # exactly the same time in the data stream
    ix=[10]+list(ix+2)+[sens.size-2]
    # loop over all calibration periods
    table=[]
    for i in range(len(ix)-1):
        ix1=ix[i]
        ix2=ix[i+1]
        sens_new[ix1:ix2]=np.interp(utc_time[ix1:ix2], np.float32([utc_time[ix1], utc_time[ix2]]), [sens[ix1], sens[ix2]])
        zero_new[ix1:ix2]=np.interp(utc_time[ix1:ix2], np.float32([utc_time[ix1], utc_time[ix2]]), [zero[ix1], zero[ix2]])
        # write calibration information to stdout
        timestamp_start=datetime.datetime.utcfromtimestamp(utc_time[ix1]).strftime('%Y-%m-%d %H:%M:%S')
        timestamp_end=datetime.datetime.utcfromtimestamp(utc_time[ix2]).strftime('%Y-%m-%d %H:%M:%S')
        if np.isnan(sens[ix1]):
            sens_string='   nan'
        else:
            sens_string='%6.2f' % (sens[ix1],)
        if np.isnan(zero[ix1]):
            zero_string='   nan'
        else:
	    zero_string='%6i' % (zero[ix1],)
        table.append([timestamp_start, timestamp_end, sens_string, zero_string])

    return table


def add_cal_coefficients_to_axes(ax, table):
    """
    Plots calibration coefficients on the CO plot.

    """
    _xlim=ax.get_xlim()
    _ylim=ax.get_ylim()
    for line in table:
        #print(line)
        if ((date2num(datetime.datetime.strptime(line[0], '%Y-%m-%d %H:%M:%S')) > _xlim[0]) &
           (date2num(datetime.datetime.strptime(line[1], '%Y-%m-%d %H:%M:%S')) < _xlim[1])):
               x=(date2num(datetime.datetime.strptime(line[0], '%Y-%m-%d %H:%M:%S')) + \
                 date2num(datetime.datetime.strptime(line[1], '%Y-%m-%d %H:%M:%S')))/2.0
               y=0.8*_ylim[1]
               #http://stackoverflow.com/questions/17086847/box-around-text-in-matplotlib
               ax.text(x, y, '\n'.join([i.strip() for i in line[2:]]), horizontalalignment='center', verticalalignment='top',
                       fontsize='small', color='black', bbox=dict(facecolor='wheat', edgecolor='black', boxstyle='round,pad=0.6'))


def main(ds):
    """
    Creates overview plot for CO during a single flight

    """
    gs = gridspec.GridSpec(2, 1, hspace=0.05, height_ratios=[1,4])
    fig = QaQc_Figure(landscape=True).setup()

    fig.add_subplot(gs[1,:])
    fig.add_subplot(gs[0,:], sharex=fig.get_axes()[0])

    set_suptitle(fig, ds, 'QA-Carbon Monoxide')

    data = get_data(ds, VARIABLE_NAMES)
    table = get_cal_coefficients(data)

    plot_co_ts(fig.get_axes()[0], data)

    zoom_to_flight_duration(fig.get_axes()[0], data)
    add_time_buffer(fig.get_axes()[0])
    add_cal_coefficients_to_axes(fig.get_axes()[0], table)

    plot_lamptemp_ts(fig.get_axes()[1], data)

    for ax in fig.get_axes():
        add_takeoff(ax, data)
        add_landing(ax, data)
    fig.canvas.draw()
    return fig

#plt.close('all')
#ds=d
#ds=netCDF4.Dataset('./data/co_extract_20160317_b952.nc', 'r')
#fig=main(ds)


#plt.close('all')


#FID='c007'
#DATE='20170302'
#SEARCH_PATH='/home/axel/Dropbox/campaigns/moya2017/'
#NC_REVISION='0'
#WRITE_NC=True
#OUTPATH='/home/axel/Dropbox/campaigns/moya2017/c007-mar-02/'

##################################################################################



#def find_file(pattern):
#    matches = []
#    for root, dirnames, filenames in os.walk(SEARCH_PATH):
#        for filename in fnmatch.filter(filenames, pattern):
#            matches.append(os.path.join(root, filename))
#    matches.sort(key=os.path.basename)
#    return matches[-1]


#rawdlu_file=find_file('core_faam_%s*%s_rawdlu.zip' % (DATE, FID))
#fltcst_file=find_file('flight-cst_faam_%s*%s.txt' % (DATE, FID))


#d=decades_dataset()
#d.add_file(rawdlu_file)
#d.add_file(fltcst_file)
#d.process()
#f = main(d)
