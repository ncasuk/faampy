#!/usr/bin/env python
'''

'''


import matplotlib as mpl
if __name__ == '__main__': mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import netCDF4
import numpy as np

import scipy
import scipy.stats

from general import *
from style import *


VARIABLE_NAMES=['WOW_IND',
                'Time',
                'PS_RVSM',
                'P9_STAT']


def linear_fit(data):
    ix=np.where(data['WOW_IND'] == 0)[0]
    p9_stat=data['P9_STAT'][ix,:].ravel()
    ps_rvsm=data['PS_RVSM'][ix,:].ravel()
    #ix = np.where(np.abs(x-y) < 50)

    slope, intercept, r_value, p_value, slope_std_error = scipy.stats.linregress(p9_stat, ps_rvsm)
    #create formula string
    if intercept > 0:
        result = 'y=%.2f*x+%.2f r^2=%.2f' % (slope, intercept, r_value**2)
    else:
        result = 'y=%.2f*x%.2f r^2=%.2f' % (slope, intercept, r_value**2)
    return result


def plot_hist(ax, data):
    """
    Plot the histogram of differences between PS_RVSM and P9_STAT
    """
    ix=np.where(data['WOW_IND'] == 0)[0]
    p9_stat=data['P9_STAT'][ix,:]
    ps_rvsm=data['PS_RVSM'][ix,:]
    delta=(p9_stat-ps_rvsm).ravel()
    _range=(-10.0, 10.0)
    _step_size=0.2
    _bins= np.arange(_range[0], _range[1], _step_size)
    freq, bin_edges = np.histogram(delta, bins=_bins, range=_range)
    freq=freq.astype(np.float32)/delta.size*100.
    ax.bar((_bins[0:-1]+_bins[1:])/2.0,
           freq,
           width=_step_size,
           alpha=0.80, color='tomato')

    ax.grid(b='on')
    ax.set_xlabel('P9_STAT-PS_RVSM (mb)')
    ax.set_ylabel('percentage (%)')

    ax.text(0.1, 0.15, 'n=%i' % (delta.size), transform=ax.transAxes)

    rect = [0.2, 0.6, 0.25, 0.25]
    ax2 = plt.gcf().add_axes(rect, aspect='equal')

    ax2.plot(p9_stat.ravel(), ps_rvsm.ravel(), '.')
    ax2.set_xlabel('PS_RVSM (mb)')
    ax2.set_ylabel('P9_STAT (mb)')
    lim0, lim1 = 250, 1050
    ax2.set_xlim((lim0, lim1))
    ax2.set_ylim((lim0, lim1))
    ax2.grid(b='on')
    lfit=linear_fit(data)
    ax2.set_title(lfit)
    # oplot 1:1 line
    plt.plot(plt.gca().get_xlim(), plt.gca().get_ylim(), linestyle='--', color='grey')
    ax2.yaxis.set_major_locator(MaxNLocator(4))
    ax2.xaxis.set_major_locator(MaxNLocator(4))
    return ax


def main(ds):
    fig=QaQc_Figure(landscape=True).setup()
    fig.add_subplot(111)
    set_suptitle(fig, ds, 'QA-Static Pressure')
    data=get_data(ds, VARIABLE_NAMES)
    ax=plt.gca()
    plot_hist(ax, data)
    add_time_buffer(ax)
    return fig


