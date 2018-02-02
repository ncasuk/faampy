'''
Created on 16 Mar 2012

@author: axel
'''

import datetime
import netCDF4
import numpy as np
import os
import re
import sys
import shutil

from matplotlib.dates import date2num

import matplotlib as mpl
import matplotlib.pyplot as plt

def sub_nans(ncfilename):
    """
    This function substitutes any NaN values with -9999

    """
    dst=os.path.splitext(ncfilename)[0]+'_edited'+os.path.splitext(ncfilename)[1]
    shutil.copy(ncfilename, dst)
    ds=netCDF4.Dataset(dst, 'a')
    for k in ds.variables.keys():
        if not k.endswith('_FLAG'):
            dat=ds.variables[k][:]
            if hasattr(dat, 'mask'):
                dat[dat.mask]=-9999
                dat[np.isnan(dat)]=-9999
                ds.variables[k][:]=dat
    ds.close()


def data_filter(ds, var_filter, verbose=None):
    """
    filter(ds, [('Time', (20000 , 22000)), ('GIN_ALT', (0, 40000))]

    """
    ix=np.empty(0)
    n=len(ds.variables['Time'])
    for item in var_filter:
        key=item[0]
        val=item[1]
        tmp_var=ds.variables[key][:].ravel()
        ix_tmp=np.where((tmp_var < val[0]) | (tmp_var > val[1]))[0]
        if verbose:
            sys.stdout.write('Filtering %s ... %.2f %% removed' % (key, float(ix_tmp.size)/float(tmp_var.size)*100.0))
        ix=np.concatenate((ix, ix_tmp))
    bad_index=set(np.unique(ix))
    full_index=set(range(n))
    good_index=list(full_index.difference(bad_index))
    if verbose:
        sys.stdout.write('Remaining points: %i (%5.2f percent)\n' % (len(good_index), float(len(good_index))/float(len(n))*100.0))
    return good_index


def conv_secs_to_time(secs, no_colons=None):
    """
    converts seconds past midnight to time string HH:MM:SS

    """
    hh=secs/3600
    mm=(secs % 3600)/60
    ss=(secs % 3600)%60
    if no_colons:
        result='%.2i%.2i%.2i' % (hh, mm, ss)
    else:
        result='%.2i:%.2i:%.2i' % (hh, mm, ss)
    return result


def conv_time_to_secs(hhmmss):
    """
    converts time string as it used e.g. in the flight summary
    to seconds past midnight.

    >>> conv_time_to_secs('122312')
    Out[1]: 44592
    >>>

    """
    hhmmss=hhmmss.strip()
    l_hhmmss=list(hhmmss)
    while ':' in l_hhmmss:
        l_hhmmss.remove(':')
    hhmmss=''.join(l_hhmmss)
    hhmmss=hhmmss[-6:]
    result=int(hhmmss[0:2])*3600+int(hhmmss[2:4])*60+int(hhmmss[4:6])
    return result


def get_fid(ds):
    """Get the flight ID (bnnn) from netCDF4.Dataset

    >>> ncfile = '/home/data/faam/badc/2013/b768-apr-03/core_processed/core_faam_20130403_v004_r0_b768.nc'
    >>> ds = netCDF4.Dataset(ncfile, 'r')
    >>> print(get_fid(ds))
    b768

    """
    #parse the title global attribute of the netcdf
    if hasattr(ds, 'title'):
        result=str(re.findall('[bBcCpP]\d{3}', ds.title)[0])
        result=result.lower()
    elif hasattr(ds, 'Title'):
        result=str(re.findall('[bBcCpP]\d{3}', ds.Title)[0])
        result=result.lower()
    else:
        result=""

    return result


def get_base_time(ds):
    """
    This function looks for the different parameter names used for 'time' as this has been defined
    in different ways historically.

    """
    if hasattr(ds, 'variables'):
        if 'Time' in ds.variables.keys():
            result=datetime.datetime.strptime(str(ds.variables['Time'].units).strip(),
                                              'seconds since %Y-%m-%d 00:00:00 +0000')
        elif 'TIME' in ds.variables.keys():
            result=datetime.datetime.strptime(str(ds.variables['TIME'].units).strip(),
                                              'seconds since %Y-%m-%d 00:00:00 +0000')
        elif 'time' in ds.variables.keys():
            result=datetime.datetime.strptime(re.findall('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', ds.variables['time'].units)[0], '%Y-%m-%d 00:00:00')
        elif 'PARA0515' in ds.variables.keys():
            result=datetime.datetime.strptime(ds.title.split()[-1], '%d-%b-%y')
    elif isinstance(ds, dict):
        if ds.has_key('DATE'):
            result=datetime.datetime(ds['DATE'][2], ds['DATE'][1], ds['DATE'][0], 0, 0, 0)
    else:
        return None
    return result


def get_mpl_time(ds, basetime=None, freq=1):
    """Return a matplotlib usable time format from the faam core netCDF4.

    >>> ds = netCDF4.Dataset('core_faam_20130403_v004_r0_b768.nc', 'r')
    >>> t_1hz = get_mpl_time(ds)
    >>> t_1hz.shape
    Out[1]: (37137,)
    >>> t_32hz = get_mpl_time(ds, 32)
    >>> t_32hz.shape
    Out[1]: (37137, 32)
    >>> plot_date(t_32hz.ravel(), ds.variables['U_C'][:].ravel(), 'b-')
    >>>

    """
    if hasattr(ds, 'variables'):
        if 'Time' in ds.variables.keys():
            vtime=ds.variables['Time'][:]
        elif 'time' in ds.variables.keys():
            vtime=ds.variables['time'][:]
        elif 'TIME' in ds.variables.keys():
            vtime=ds.variables['TIME'][:]
        #in old core files the 'Time' variable was c2alled PARA0515
        elif 'PARA0515' in ds.variables.keys():
            vtime=ds.variables['PARA0515'][:]
    elif isinstance(ds, dict):
        if ds.has_key('Time'):
            vtime=ds['Time']
    else:
        return None
    import numpy as np
    rows = len(vtime)
    vtime = vtime.repeat(freq).reshape((rows, freq)) + np.array(range(freq), dtype=np.float64)/freq
    if not basetime:
        basetime=get_base_time(ds)

    result=np.float64(vtime/86400.) + np.float64(date2num(basetime))
    return result


def get_flight_duration(ds, quite=None):
    """Get flight durations by filtering IAS and GSPD data that are
    greater than 60ms-1.

    """
    if not quite:
        quite=False
    else:
        quite=True

    ias=ds.variables['IAS_RVSM'][:]
#    if hasattr(ias, 'data'):
#        ias=ias.data
    if len(ds.variables['IAS_RVSM'].shape) > 1:
        ias=ias[:,0].ravel()
    else:
         ias=ias[:]

    if 'GSPD_GIN' in list(ds.variables.keys()):
        gspd=ds.variables['GSPD_GIN'][:]
        #if hasattr(gspd, 'data'):
        #    gspd=gspd.data
        if len(gspd.shape) > 1: gspd=gspd[:,0].ravel()

    if 'WOW_IND' in ds.variables.keys():
        wow_ind=ds.variables['WOW_IND'][:]
        #if hasattr(wow_ind, 'data'):
        #    wow_ind=wow_ind.data
        if len(wow_ind.shape) > 1: wow_ind=wow_ind[:,0].ravel()

    if 'WOW_IND' in list(ds.variables.keys()):
        ix=np.where(wow_ind == 0)[0]
        ix_min, ix_max=np.min(ix), np.max(ix)
        dur=ds.variables['Time'][ix_max]-ds.variables['Time'][ix_min]
    elif 'GSPD_GIN' in list(ds.variables.keys()):
        #filter for indicated airspeed greater 60
        ix=np.where((ias > 60) & (gspd > 60))
        ix_min, ix_max=np.min(ix), np.max(ix)
        dur=ds.variables['Time'][ix_max]-ds.variables['Time'][ix_min]
    else:
        if not isinstance(ias, np.ndarray):
            ias=ias.data

        #filter for indicated airspeed greater 60
        ix=np.where(ias > 60)
        ix_min, ix_max=np.min(ix), np.max(ix)
        dur=ds.variables['Time'][ix_max]-ds.variables['Time'][ix_min]

    if not quite:
        sys.stdout.write('*'*40+'\n')
        sys.stdout.write('      FID:  %s\n' % (get_fid(ds),))
        sys.stdout.write('      T/O:  %s\n' % conv_secs_to_time(np.min(ds.variables['Time'][ix_min])))
        sys.stdout.write('     Land:  %s\n' % conv_secs_to_time(np.min(ds.variables['Time'][ix_max])))
        sys.stdout.write(' Duration:  %s (%i secs)\n' % (conv_secs_to_time(dur), dur))
        sys.stdout.write('*'*40+'\n')
    return float(dur)


def get_index_from_secs(ds, secs):
    ix = np.where(ds.variables['Time'][:] == secs)
    return ix[0][0]


def get_index_from_hhmmss(ds, hhmmss):
    """return the index from a FAAM core netcdf where the 'Time'-variables matches
    the time 'hhmmss' string matches the

    Example::

        >>> import netCDF4
        >>> ds = netCDF4.Dataset('core_faam_20130225_v004_r0_b753.nc', 'r')
        >>> get_index_from_hhmmss(ds, '120000')
        Out[1]: 7668
        >>>

    """
    #convert time in string format to seconds past midnight
    secs = conv_time_to_secs(hhmmss)
    ix = get_index_from_secs(ds, secs)
    return ix


def get_index(ds, inp):
    """wrapper for the

    get_index_from_secs
      and
    get_index_from_hhmmss

    functions. Determines what type inp is and calls the
    appropriate function.

    """
    if isinstance(inp, int):
        ix = get_index_from_secs(ds, inp)
    elif len(inp) == 6 and re.match('\d{6}', inp):
        ix = get_index_from_hhmmss(ds, inp)
    else:
        pass
    return ix


def freeze_color_cycle(ax):
    """A function that freezes the color cycle. This is useful for example when
    the twinx() command is used and the color cycle would normally be reseted.

    :param ax: axis

    Usage::

    import matplotlib.pyplot as plt
    import numpy as np

    plt.close('all')
    for i in range(3):
        plt.plot(np.random.random(20))

    ax=plt.gca()
    cc=freeze_color_cycle(ax)
    plt.twinx()
    ax=plt.gca()
    ax.set_color_cycle(cc)

    #plot some more on the new twined axes
    for i in range(3):
        plt.plot(np.random.random(20))

    #When we set-up a new figure we start with blue again
    fig=figure()
    for i in range(3):
        plot(np.random.random(20))

    """
    if mpl.__version__ >= '1.5.1':
        next_color = ax._get_lines.prop_cycler.next()['color']
    else:
        next_color = next(ax._get_lines.color_cycle)

    ix = plt.rcParams['axes.color_cycle'].index(next_color)
    color_cycle = plt.rcParams['axes.color_cycle'][ix:] + \
                  plt.rcParams['axes.color_cycle'][:ix]
    return color_cycle
