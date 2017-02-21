core_filename = '/home/axel/Dropbox/campaigns/vanaheim2016/b988-oct-20/core_faam_20161020_v004_r0_b988.nc'
aimms_filename = '/home/axel/Dropbox/campaigns/vanaheim2016/b988-oct-20/metoffice-aimms_faam_20161020_v003_r0_b988.nc'

core_filename = '/home/axel/Dropbox/campaigns/wintex2017/b994-feb-03/core_faam_20170203_v004_r0_b994.nc'
aimms_filename = '/mnt/faamarchive/scanner/aimms/metoffice-aimms_faam_20170203_v003_r0_b994.nc'


import sys
sys.path.insert(0, '/home/axel/git-repos/faampy/')


import netCDF4
import pandas as pd
import numpy as np

import matplotlib.gridspec as gridspec

from faampy.core.utils import get_mpl_time
from matplotlib.dates import num2date, date2num
from matplotlib import dates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

plt.style.use('seaborn-deep')


# plot time series of the u,v,w and delta; add top figure with altitude and liquid water content
# plot time series of t and rh and delta
# plot spectra for u,v,w,tas
# plot scatter plots matrix for u,v,w,tas

def plot_wind_vector_components():
    pass


core_ds = netCDF4.Dataset(core_filename, 'r')
aimms_ds = netCDF4.Dataset(aimms_filename, 'r')


#def get_data(var, core_ds, aimms_ds):
varnames = [['U_C', 'U'],
            ['V_C', 'V'],
            ['W_C', 'W'],
            ['TAS', 'TAS']]

cols_c, cols_a = zip(*varnames)
t_c = np.array(num2date(get_mpl_time(core_ds, 32)))
t_a = netCDF4.num2date(aimms_ds.variables['TIME'][:], aimms_ds.variables['TIME'].units)


df_colnames = ['core_%s' % s.lower() for s in cols_a]
df_c = pd.DataFrame(index=t_c.ravel(), columns=df_colnames)
for i,j in zip(df_colnames, cols_c):
    df_c[i] = core_ds.variables[j][:].data.ravel()
df_colnames = ['aimms_%s' % s.lower() for s in cols_a]
df_a = pd.DataFrame(index=t_a, columns=df_colnames)
df_a = df_a.tz_localize('UTC')
for i,j in zip(df_colnames, cols_a):
    df_a[i] = aimms_ds.variables[j][:].data.ravel()

# filter data frame; only use data points when the aircraft was in the air
wow = core_ds.variables['WOW_IND'][:].data
wow_ix = (np.min(np.where(wow == 0)[0]),
          np.max(np.where(wow == 0)[0]))
t_ix = (t_c[wow_ix[0],0], t_c[wow_ix[1],0])
df_c = df_c[(df_c.index >= t_ix[0]) & (df_c.index < t_ix[1])]
df_a = df_a[(df_a.index >= t_ix[0]) & (df_a.index < t_ix[1])]

#a = aimms_data.variables[varnames[1]][:]
#wow = core_data.variables['WOW'][:]


# time series plots
fig = plt.figure()
gs = gridspec.GridSpec(4, 1, left=0.1, hspace=0.05)

_ax = {}
_ax['ax_u'] = fig.add_subplot(gs[3])                                #  axes u wind component
_ax['ax_v'] = fig.add_subplot(gs[2], sharex=fig.get_axes()[0])      #  axes v wind component
_ax['ax_w'] = fig.add_subplot(gs[1], sharex=fig.get_axes()[0])      #  axes w wind component
_ax['ax_tas'] = fig.add_subplot(gs[0], sharex=fig.get_axes()[0])    #  axes tas wind component


for wv in ['u', 'v', 'w', 'tas']:
    #df_c['core_'+wv].plot(ax=_ax['ax_'+wv], label='core-'+wv, ylabe)
    #df_a['aimms_'+wv].plot(ax=_ax['ax_'+wv], label='aimms-'+wv))
    ax = _ax['ax_'+wv]
    l1 = ax.plot_date(date2num(df_c.index.to_pydatetime()), df_c['core_'+wv].values, '-', label='core')
    l2 = ax.plot_date(date2num(df_a.index.to_pydatetime()), df_a['aimms_'+wv].values, '-', label='aimms')
    #ax.legend()
    ax.grid(True)
    ax.text(0.02, 0.95, wv, verticalalignment='top', transform=ax.transAxes)
    ax.set_ylabel(r'%s $(ms^{-1})$' % wv)
    # the delta is plotted for 1Hz averaged data to keep it simple
    #delta = df_c['core_'+wv].resample('S').mean()-df_a['aimms_'+wv].resample('S').mean()
    delta = df_c['core_'+wv].resample('S')-df_a['aimms_'+wv].resample('S')
    ax2 = _ax['ax_'+wv].twinx()
    l3 = ax2.plot_date(date2num(delta.index.to_pydatetime()), delta.values, '-', color='firebrick', label=r'$\Delta$')
    ax2.set_ylabel(r'$\Delta \quad (ms^{-1})$')
    if wv != 'u':
        for label in ax.get_xticklabels()[:]:
            label.set_visible(False)        
    else:
        hfmt = dates.DateFormatter('%H:%M')
        ax.xaxis.set_major_locator(dates.MinuteLocator(byminute=range(0, 60, 30)))
        ax.xaxis.set_major_formatter(hfmt)
        ax.set_xlabel('time (utc)')

    if wv == 'tas':
        lines = l1+l2+l3
        labs = [l.get_label() for l in lines]
        ax.legend(lines,labs, loc='upper right')




# scatter plots
fig = plt.figure()
gs = gridspec.GridSpec(2, 2)

_ax = {}
_ax['ax_u'] = fig.add_subplot(gs[3], aspect='equal')      #  axes u wind component
_ax['ax_v'] = fig.add_subplot(gs[2], aspect='equal')      #  axes v wind component
_ax['ax_w'] = fig.add_subplot(gs[1], aspect='equal')      #  axes w wind component
_ax['ax_tas'] = fig.add_subplot(gs[0], aspect='equal')    #  axes tas wind component

for wv in ['u', 'v', 'w', 'tas']:
    ax = _ax['ax_'+wv]
    x = np.array(df_c['core_'+wv].resample('S'))
    y = np.array(df_a['aimms_'+wv].resample('S'))
    ax.plot(x, y, '.')
    ax.grid(True)
    _lim=(np.min([ax.axes.get_xlim()[0], ax.axes.get_ylim()[0]]),
          np.max([ax.axes.get_xlim()[1], ax.axes.get_ylim()[1]]))
    ax.set_xlim(_lim)
    ax.set_ylim(_lim)
    l = Line2D([0,1],[0,1], color='0.3', transform=ax.transAxes)
    ax.add_line(l)
    ax.text(0.05, 0.95, wv, verticalalignment='top', transform=ax.transAxes)



def running_mean(x, N):
    return np.convolve(x, np.ones((N,))/N)[(N-1):]


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


# spectra plots

fig = plt.figure()
gs = gridspec.GridSpec(2, 2)

_ax = {}
_ax['ax_u'] = fig.add_subplot(gs[3])      #  axes u wind component
_ax['ax_v'] = fig.add_subplot(gs[2])      #  axes v wind component
_ax['ax_w'] = fig.add_subplot(gs[1])      #  axes w wind component
_ax['ax_tas'] = fig.add_subplot(gs[0])    #  axes tas wind component

for wv in ['u', 'v', 'w', 'tas']:
    ax = _ax['ax_'+wv]
    c_freqs, c_ps = power_spectrum(np.array(df_c['core_'+wv]), 32)
    a_freqs, a_ps = power_spectrum(np.array(df_a['aimms_'+wv]), 20)

    c_freqs = c_freqs[:-1]
    a_freqs = a_freqs[:-1]
    c_ps = c_ps[:-1]
    a_ps = a_ps[:-1]

    ax.plot(c_freqs[c_freqs < 15.5], running_mean(c_ps, 200)[c_freqs < 15.5])
    ax.plot(a_freqs[a_freqs < 9.5], running_mean(a_ps, 200)[a_freqs < 9.5])

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_ylim(1, 10**8)
    ax.set_xlim(0.1, 16)
    xticks = [1, 2, 3, 4, 5, 6, 8, 10, 16]
    ax.set_xticks(np.array(xticks))
    ax.set_xticklabels([str(i) for i in xticks])
    ax.text(0.05, 0.95, wv, verticalalignment='top', transform=ax.transAxes)
