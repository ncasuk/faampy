# -*- coding: utf-8 -*-

import datetime
import matplotlib as mpl
import netCDF4
import numpy as np
import pandas as pd
import sys

from utils import get_mpl_time

try:
    from ppodd.core import *
except:
    sys.stdout.write('decades-pp not installed ...\n')
    pass

VERTICAL_INDICATOR_WIDTH = 4
VERTICAL_INDICATOR_COLOR = '0.7'


def rotate_coord(x, y, angle):
    """coordinate system rotation

    """
    x_rot = x * np.cos(np.deg2rad(angle)) + y * np.sin(np.deg2rad(angle))
    y_rot = -x * np.sin(np.deg2rad(angle)) + y * np.cos(np.deg2rad(angle))
    return(x_rot, y_rot)


class QaQc_Figure(object):
    """Main Quality Assurance/Quality Control Figure. This class defines some
common figure features that should be applied to all figures."""

    def __init__(self, landscape=False):

        self.fig = mpl.pyplot.figure()
        self.fig.orientation='portrait'
        #set default size to DIN-A4 portrait
        self.fig.set_size_inches(8.27, 11.69, forward=True)
        #add FAAM logo to top left corner of figure
        font_logo = mpl.font_manager.FontProperties(family='sans-serif', style='italic', size='xx-large', weight='bold')
        self.fig.logo_text = self.fig.text(0.05, 0.98, 'FAAM',
                                       horizontalalignment='left',
                                       verticalalignment='top',
                                       transform=self.fig.transFigure,
                                       color='#004ACC')
        self.fig.logo_text.set_font_properties(font_logo)

        self.fig.timestamp = self.fig.text(0.98, 0.02, 'created: %s' %(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                                           horizontalalignment='right',
                                           verticalalignment='bottom',
                                           transform=self.fig.transFigure,
                                           fontsize='smaller')
        #decrease margins between subplots
        self.fig.subplots_adjust(hspace=0.15)

        HEADER_POSITION=(0.5, 0.96)

        #self.fig.header=self.fig.suptitle('')
        if not landscape:
            self.fig.header=self.fig.text(HEADER_POSITION[0], HEADER_POSITION[1], '',
                                      horizontalalignment='center',
                                      verticalalignment='top',
                                      transform=self.fig.transFigure)

        if landscape:
            self.fig.orientation='landscape'
            #get original width and height
            width, height=tuple(self.fig.get_size_inches())
            self.fig.set_size_inches(height, width, forward=True)

            x, y=self.fig.logo_text.get_position()
            x_new, y_new=rotate_coord(x*width, y*height, 270)
            self.fig.logo_text.set_rotation(270)
            self.fig.logo_text.set_position((-x_new/height, 1.0-(y_new/width)))
            self.fig.logo_text.set_horizontalalignment('right')
            self.fig.timestamp.set_verticalalignment('top')

            x, y=self.fig.timestamp.get_position()
            x_new, y_new=rotate_coord(x*width, y*height, 270)
            self.fig.timestamp.set_rotation(270)
            self.fig.timestamp.set_position((-x_new/height, 1.0-(y_new/width)))
            self.fig.timestamp.set_horizontalalignment('left')
            self.fig.timestamp.set_verticalalignment('bottom')

            x_new, y_new=rotate_coord(HEADER_POSITION[0]*width, HEADER_POSITION[1]*height, 270)
            #self.fig.header.set_rotation(270)
            #self.fig.header.set_position((-x_new/height, 1.0-(y_new/width)))
            #self.fig.header.set_verticalalignment('center')
            #self.fig.header.set_horizontalalignment('right')
            #print(x_new, y_new)
            #self.fig.header=self.fig.text(-x_new/height, 1.0-(y_new/width), 'rotated\nwith newlines',
            self.fig.header=self.fig.text(-x_new/height, 0.5, '',
                                          horizontalalignment='center',
                                          verticalalignment='center',
                                          rotation=270,
                                          transform=self.fig.transFigure)

    def setup(self):
        return self.fig


def get_data(ds, var_names):
    """
    Funtion to get the data from the specified netCDF dataset
    ds = netCDF dataset
    var_names = variable names (i.e. VARIABLE_NAMES) as specified at the top of each qa-qc module

    """
    result={}

    if isinstance(ds, netCDF4.Dataset):
        #Read all necessary data from netCDF dataset and convert to 1Hz
        result['mpl_timestamp'] = get_mpl_time(ds, freq=32)
        for var in var_names:
            if var not in ds.variables.keys():
                continue
            else:
                result[var] = ds.variables[var][:]
    elif isinstance(ds, decades_dataset):
        #result['mpl_timestamp'] = get_mpl_time(ds, 32)
        for var in var_names:
            if (var not in ds.keys()) and (var[:-5] not in ds.keys()) :
                continue
            if var != 'Time':
                #check if df exists
                if not 'df' in locals():
                    if var.endswith('_FLAG'):
                        df=pd.Series(list(np.array(ds[var[:-5]][:].flag())), index=ds[var[:-5]].times[:], dtype=np.dtype("object"), name=var)
                    else:
                        df=pd.Series(list(np.array(ds[var][:])), index=ds[var].times[:], dtype=np.dtype("object"), name=var)
                else:
                    if var.endswith('_FLAG'):
                        ndf=pd.Series(list(np.array(ds[var[:-5]][:].flag)), index=ds[var[:-5]].times[:], dtype=np.dtype("object"), name=var)
                        df=pd.concat([df, ndf], axis=1, join='outer')
                    else:
                        ndf=pd.Series(list(np.array(ds[var][:])), index=ds[var].times[:], dtype=np.dtype("object"), name=var)
                        df=pd.concat([df, ndf], axis=1, join='outer')

        df=df.dropna()

        new_result={}
        new_result['Time']=np.array(df.index, dtype=np.uint32)
        bs=datetime.datetime(ds['DATE'][2], ds['DATE'][1], ds['DATE'][0], 0, 0, 0)

        mpl_timestamp=get_mpl_time(new_result, freq=32, basetime=bs)
        new_result['mpl_timestamp']=mpl_timestamp

        for k in list(df):
            if k.endswith('_FLAG'):
                _k=k[:-5]
            else:
                _k=k
            if ds[_k].frequency > 1:
                new_result[k]=np.array([list(row) for row in df[k].values])
            else:
                #we have to make it two dimensional
                new_result[k]=np.array(list(df[k]), ndmin=2).T
        result=new_result
    return result



def get_data_old(ds, var_names):
    """
    Funtion to get the data from old netCDF datasets
    ds = netCDF dataset
    var_names = variable names (i.e. VARIABLE_NAMES) as specified at the top of each qa-qc module
    """
    result = {}
    df = None
    if isinstance(ds, netCDF4.Dataset):
        #Read all necessary data from netCDF dataset and convert to 1Hz
        result['mpl_timestamp'] = get_mpl_time(ds, 32)
        for var in var_names:
            result[var] = ds.variables[var][:]
    elif isinstance(ds, decades_dataset):
        #result['mpl_timestamp'] = get_mpl_time(ds, 32)
        for var in var_names:
            if var != 'Time':
                #result[var] = ds[var][:]
                if not df:
                    #create dataframe
                    df=pd.Series(np.array(d[var]))
                else:
                    #add to datafrome
                    pass
    return result


def get_wow_min_max(wow_ind):
    """
    This functions finds the weight on wheels minimum and maximum values.
    These can then be used in other functions to plot the take-off/landing.

    """
    #wow_min = np.where(wow_ind.filled() == 0)[0].min()
    #wow_max = np.where(wow_ind.filled() == 0)[0].max()
    if hasattr(wow_ind, 'filled'):
        wow_ind=wow_ind.filled()
    wow_min = np.where(wow_ind == 0)[0].min()
    wow_max = np.where(wow_ind == 0)[0].max()
    return wow_min, wow_max


def add_takeoff(ax, data):
    """oplots time of take-off as vertical line.

    """
    wow_min, wow_max = get_wow_min_max(data['WOW_IND'][:])
    ax.axvline(data['mpl_timestamp'][wow_min,0], lw=VERTICAL_INDICATOR_WIDTH, color=VERTICAL_INDICATOR_COLOR, zorder=1)


def add_landing(ax, data):
    """oplots time of landing as vertical line.

    """
    wow_min, wow_max=get_wow_min_max(data['WOW_IND'])
    ax.axvline(data['mpl_timestamp'][wow_max,0], lw=VERTICAL_INDICATOR_WIDTH, color=VERTICAL_INDICATOR_COLOR, zorder=1)


def set_suptitle(fig, ds, qa_title):
    """
    This function adds all relevant information to the figure title. i.e. flight number and date.

    """
    if hasattr(ds, 'title'):
        fig.header.set_text('%s\n%s - %s' % (qa_title, ds.title.split()[2], ds.title.split()[4]))
    elif hasattr(ds, 'Title'):
        fig.header.set_text('%s\n%s - %s' % (qa_title, ds.Title.split()[2], ds.Title.split()[4]))
    else:
        fig.header.set_text('%s\n%s - %s' % (qa_title, ds['FLIGHT'].data, datetime.datetime.strptime('%0.2i-%0.2i-%0.4i' % tuple(ds['DATE']), '%d-%m-%Y').strftime('%d-%b-%Y')))
    return


def add_time_buffer(ax, time_buffer=3):
    """
    Adding time buffer to the axis, which should be . time_buffer is in percent default: 3

    """
    current_xrange=ax.get_xlim()[1]-ax.get_xlim()[0]
    new_xlim=(ax.get_xlim()[0]-(current_xrange/100.)*time_buffer,
              ax.get_xlim()[1]+(current_xrange/100.)*time_buffer)
    ax.set_xlim(new_xlim)


def adjust_ylim(ax):
    # http://stackoverflow.com/questions/4098131/how-to-update-a-plot-in-matplotlib
    xlim = ax.get_xlim()
    for a in ax.figure.axes:
        # shortcuts: last avoids n**2 behavior when each axis fires event
        #if a is ax or len(a.lines) == 0 or getattr(a, 'xlim', None) == xlim:
        #    continue

        ylim = np.inf, -np.inf
        for l in a.lines:
            x, y = l.get_data()
            # faster, but assumes that x is sorted
            start, stop = np.searchsorted(x, xlim)
            yc = y[max(start-1,0):(stop+1)]
            ylim = min(ylim[0], np.nanmin(yc)), max(ylim[1], np.nanmax(yc))

        # TODO: update limits from Patches, Texts, Collections, ...

        # x axis: emit=False avoids infinite loop
        a.set_xlim(xlim, emit=False)

        # y axis: set dataLim, make sure that autoscale in 'y' is on
        corners = (xlim[0], ylim[0]), (xlim[1], ylim[1])
        a.dataLim.update_from_data_xy(corners, ignore=True, updatex=False)
        a.autoscale(enable=True, axis='y')
        # cache xlim to mark 'a' as treated
        a.xlim = xlim


def zoom_to_flight_duration(ax, data):
    """
    This function makes sure only the flight data is plotted by looking at when the
    weight on wheels indicator shows takeoff/landing. Therefore ignoring pre and post flight data.

    """
    wow_min, wow_max=get_wow_min_max(data['WOW_IND'])
    new_xlim=(data['mpl_timestamp'][wow_min, 0],
              data['mpl_timestamp'][wow_max, 0])
    ax.set_xlim(new_xlim)
    #adjust_ylim(ax)
