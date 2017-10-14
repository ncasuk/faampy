import datetime
import netCDF4
import numpy as np
import os
import pandas as pd
import re
import sys
import shutil

from matplotlib.dates import date2num, num2date


def sub_nans(ncfilename):
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
    :param ds: 
    :type ds: netCDF4.Dataset
    :param var_filter: filter definition in form of list of tuplesa tuples

    filter(ds, [('Time', (20000 , 22000)), ('GIN_ALT', (0, 40000))]
    """
    ix = np.empty(0)
    n = len(ds.variables['Time'])
    for item in var_filter:
        key = item[0]
        val = item[1]
        tmp_var = ds.variables[key][:].ravel()
        ix_tmp = np.where((tmp_var < val[0]) | (tmp_var > val[1]))[0]
        if verbose:
            sys.stdout.write('Filtering %s ... %.2f %% removed' % (key, float(ix_tmp.size)/float(tmp_var.size)*100.0))
        ix = np.concatenate((ix, ix_tmp))
    bad_index = set(np.unique(ix))
    full_index = set(range(n))
    good_index = list(full_index.difference(bad_index))
    if verbose:
        sys.stdout.write('Remaining points: %i (%5.2f percent)\n' % (len(good_index), float(len(good_index))/float(len(n))*100.0))
    return good_index


def conv_secs_to_time(secs, no_colons=True):
    """converts seconds past midnight to a time string HH:MM:SS
    
    :param int secs: seconds past midnight
    :param no_colons: by default HH, MM, SS are not separated by ':'
      default True
    :type no_colons: boolean
    :return time string:
    """
    hh = secs/3600
    mm = (secs % 3600)/60
    ss = (secs % 3600)%60
    if no_colons:
        result = '%.2i%.2i%.2i' % (hh, mm, ss)
    else:
        result = '%.2i:%.2i:%.2i' % (hh, mm, ss)
    return result


def conv_time_to_secs(hhmmss):
    """converts time string as it used for ecample in the flight summary
    to seconds past midnight

    :param str hhmmss: timestamp

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
    """
    Get the flight ID ([b,c]nnn) from a netCDF4.Dataset
    
    :param ds: core_faam dataset
    :type param: netCDF4.Dataset

    >>> ncfile = 'core_faam_20130403_v004_r0_b768.nc'
    >>> ds = netCDF4.Dataset(ncfile, 'r')
    >>> print(get_fid(ds))
    b768

    """
    #parse the title global attribute of the netcdf
    if hasattr(ds, 'title'):
        result = str(re.findall('[b,B,c,C,p,P]\d{3}', ds.title)[0])
        result = result.lower()
    elif hasattr(ds, 'Title'):
        result = str(re.findall('[b,B,c,C,p,P]\d{3}', ds.Title)[0])
        result = result.lower()
    else:
        result = ""

    return result


def get_base_time(ds):
    """Get the base time from the units of the time dimension
    
    :param ds: core_faam dataset
    :type param: netCDF4.Dataset
    :return datetime:
    :type return: datetime.datetime object
    """
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
    else:
        return None
    return result


def get_mpl_time(ds, *freq):
    """Return a float wihich is usabale for plt.plot_date from matplotlib.

    :param ds: core_faam dataset
    :type param: netCDF4.Dataset
    :param freq: frequency of the time stamp default=1; if freq > 1 a multidimensional array is returned
    :return: array containing the matplotlib timestamps
    :rtype: numpy.array

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
    if 'Time' in ds.variables.keys():
        vtime=ds.variables['Time'][:]
    elif 'time' in ds.variables.keys():      
        vtime=ds.variables['time'][:]
    elif 'TIME' in ds.variables.keys():
        vtime=ds.variables['TIME'][:]
    #in old core files the 'Time' variable was c2alled PARA0515
    elif 'PARA0515' in ds.variables.keys():
        vtime=ds.variables['PARA0515'][:]
    else:
        return None
    vtime=np.array(vtime)
    if freq:
        rows = len(vtime)
        vtime = vtime.repeat(freq[0]).reshape((rows, freq[0])) + np.array(range(freq[0]), dtype=np.float64)/freq[0]
    result=np.float64(vtime/86400.) + np.float64(date2num(get_base_time(ds)))
    return result


def get_flight_duration(ds, verbose=False):
    """Estimates the flight durations of a flight. If the Weight on Wheels
    indicator flag is available in the netCDF4 dataset, this variable is
    used for determing take-off and landing. Alternatively the method looks 
    at the indicated airspeed (IAS) and ground speed (GSPD) data that are
    greater than 60ms-1 and lower tahn 200ms-1

    :param ds: core_faam dataset
    :type param: netCDF4.Dataset
    :param verbose: more output if needed
    :type verbose: boolean
    """
    
    ias=ds.variables['IAS_RVSM'][:]
    if len(ds.variables['IAS_RVSM'].shape) > 1:
        ias=ias[:,0].ravel()
    else:
         ias=ias[:]

    if 'GSPD_GIN' in ds.variables.keys():
        gspd=ds.variables['GSPD_GIN'][:]
        if len(gspd.shape) > 1:
            gspd=gspd[:,0].ravel()

    if 'WOW_IND' in ds.variables.keys():
        wow_ind=ds.variables['WOW_IND'][:]
        if len(wow_ind.shape) > 1:
            wow_ind=wow_ind[:,0].ravel()

    if 'WOW_IND' in ds.variables.keys():
        if hasattr(wow_ind, 'filled'):
            ix=np.where(wow_ind.filled() == 0)[0]
        else:
            ix=np.where(wow_ind == 0)[0]
        ix_min, ix_max=np.min(ix), np.max(ix)
        dur=ds.variables['Time'][ix_max]-ds.variables['Time'][ix_min]
    elif 'GSPD_GIN' in ds.variables.keys():
        #filter for indicated airspeed greater 60
        ix=np.where((ias > 60) & (ias < 200) & (gspd > 60))
        ix_min, ix_max=np.min(ix), np.max(ix)
        dur=ds.variables['Time'][ix_max]-ds.variables['Time'][ix_min]
    else:
        if not isinstance(ias, np.ndarray):
            ias=ias.data
        #filter for indicated airspeed greater 60
        ix=np.where((ias > 60) & (ias < 200))
        ix_min, ix_max=np.min(ix), np.max(ix)
        dur=ds.variables['Time'][ix_max]-ds.variables['Time'][ix_min]

    if verbose:
        sys.stdout.write('*'*40+'\n')
        sys.stdout.write('      FID:  %s\n' % (get_fid(ds),))
        sys.stdout.write('      T/O:  %s\n' % conv_secs_to_time(np.min(ds.variables['Time'][ix_min])))
        sys.stdout.write('     Land:  %s\n' % conv_secs_to_time(np.min(ds.variables['Time'][ix_max])))
        sys.stdout.write(' Duration:  %s (%i secs)\n' % (conv_secs_to_time(dur), dur))
        sys.stdout.write('*'*40+'\n')
    return float(dur)


def get_index_from_secs(ds, secs):
    """Return index for seconds
    :param ds:  
    :type ds: netCDF4.Dataset
    :param secs: seconds past midnight 
    :type secs: int
    """
    ix = np.where(ds.variables['Time'][:] == secs)
    return ix[0][0]


def get_index_from_hhmmss(ds, hhmmss):
    """return the index from a FAAM core netcdf where the 'Time'-variables matches
    the time 'hhmmss' string matches the

    

    >>> import netCDF4
    >>> ds = netCDF4.Dataset('core_faam_20130225_v004_r0_b753.nc', 'r')
    >>> get_index_from_hhmmss(ds, '120000')
    Out[1]: 7668
    >>>

    """
    # convert time in string format to seconds past midnight
    secs=conv_time_to_secs(hhmmss)
    ix=get_index_from_secs(ds, secs)
    return ix


def get_index(ds, inp):
    """
    wrapper for the methods
      get_index_from_secs
        and
      get_index_from_hhmmss

    function determines what type the input is 
    and calls the appropriate function accordingly.
    
    :param ds: core_faam dataset
    :type param: netCDF4.Dataset
    """
    if isinstance(inp, int):
        ix=get_index_from_secs(ds, inp)
    elif len(inp) == 6 and re.match('\d{6}', inp):
        ix=get_index_from_hhmmss(ds, inp)
    else:
        pass
    return ix


def core_to_pandas(ds):
    """converts a netCDF4.Dataset into a pandas Dataframe using the timestamp
    as index.
    
    ..note: Only the first column of the two dimensional data set is grabbed,
            because of performance issues.

    :param ds: core_faam dataset
    :type param: netCDF4.Dataset
    :return: pandas.Dataframe
    :type return: pandas.Dataframe

    """
    
    # TODO: make it work for the full dataset too
    vars=sorted(ds.variables.keys())
    vars.remove('Time')
    
    index=get_mpl_time(ds, 1)
    index=num2date(index.ravel())
    #initialize an empty Dataframe
    df=pd.DataFrame(index=index)
    for v in vars:
        shp=ds.variables[v].shape
        if len(shp) ==2:
            data=np.copy(ds.variables[v][:,0].data).ravel()
        else:
            data=np.copy(ds.variables[v][:].data)
        df_tmp=pd.DataFrame(data[:], index=index, columns=[v,])
        df = pd.concat([df, df_tmp], axis=1)
    #set all missing values to nan
    df[df == -9999.0] = np.nan
    #set timezone to None otherwise there might be issues merging the data
    #frame with others    
    df.index.tz=None
    return df    
