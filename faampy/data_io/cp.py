import sys


import netCDF4
import numpy as np
from numpy.lib import recfunctions
import pandas as pd
from faampy.core.utils import get_mpl_time
from matplotlib.dates import num2date


def read_core_cloud(ifile):
    """reads in the core cloud data and 

    :param str ifile: core cloud netcdf file
    :return: pandas.Dataframe
    :type return: pandas.Dataframe

    """
    ds = netCDF4.Dataset(ifile, 'r')
    vars = sorted(ds.variables.keys())
    vars.remove('Time')
    
    # create and indexed pandas DataFrame
    tindex = get_mpl_time(ds, 1)
    tindex = num2date(tindex.ravel())
    # initialize an empty Dataframe
    df = pd.DataFrame(index=tindex)
    for v in vars:
        shp = ds.variables[v].shape
        if not shp[0] == len(index):
            continue
        if len(shp) == 2:
            data = np.copy(ds.variables[v][:,0].data).ravel()
        else:
            data = np.copy(ds.variables[v][:])
        df_tmp = pd.DataFrame(data[:].ravel(), index=index, columns=[v,])
        df = pd.concat([df, df_tmp], axis=1)
    
    df[df == -9999.0] = np.nan  # set all missing values to nan
    t = df.index.values
    df['timestamp'] = t.astype('datetime64[s]')  # Converting index data type

    # TODO: Check that this is really necessary
    # set timezone to None otherwise there might be issues merging
    # this DataFrame with others    
    df.index.tz = None
    return df    
