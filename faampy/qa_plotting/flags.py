'''
Created on 10 May 2013

@author: axel
'''

import numpy as np
import netCDF4
import texttable


def get_flag_data(ds):
    """
    This function gets all of the flag data in a netCDF dataset
    
    """
    result = []

    #if isinstance(ds, netCDF4.Dataset):
    if 'netCDF4.Dataset' in str(type(ds)):
        for k in sorted(ds.variables.keys()):
            if k.endswith('_FLAG'):
                size=ds.variables[k][:].size
                h=(np.histogram(ds.variables[k][:], range(-1, 5))[0]).astype(float) / float(size) * 100.
                line=[k[:-5]] + list(h) + [100.-np.sum(h)]
                result.append(line)
        ds.close()
    #elif isinstance(ds, decades_dataset):
    elif 'decades_dataset' in str(type(ds)):
        for k in sorted(ds.keys()):
            if hasattr(ds[k], 'flag'):                
                size=ds[k][:].size
                try:
                    h=(np.histogram(ds[k][:].flag, range(-1, 5))[0]).astype(float) / float(size) * 100.
                    line=[k] + list(h) + [100.-np.sum(h)]
                except:
                    line=[k] + [-9999,]*6
                result.append(line)
    return result


def create_table(data):
    """
    This function sets the layout for a table
    
    """
    tab = texttable.Texttable()
    tab.set_chars(['-','|','+','-'])
    tab.set_deco(tab.HEADER | tab.VLINES | tab.BORDER)
    tab.set_cols_align(['r','r','r', 'r', 'r', 'r', 'r'])
    tab.set_cols_width([10, 5, 5, 5, 5, 5, 5])
    tab.set_precision(1)
    tab.add_rows(data)
    tab.header(['var',  '-1', '0', '1', '2', '3', 'na'])
    tab.set_precision(1)
    return tab


def process(ncfile):
    """
    This function produces a table of the flag data within the netCDF file.
    
    """
    flag_data = get_flag_data(ncfile)
    tab = create_table(flag_data)
    return tab.draw()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Prints flag summary table for netcdf file.')
    parser.add_argument('ncfile', action="store", type=str, help='Input netcdf file.')
    args = parser.parse_args()
    ds=netCDF4.Dataset(args.ncfile, 'r')
    flag_data = get_flag_data(ds)
    tab = create_table(flag_data)
    print(tab.draw())



