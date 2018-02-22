#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import OrderedDict
import pandas as pd
import datetime

def read_grimm_raw(ifile):
    """Routine for reading in the text file data from the Grimm instrument.
    The time resolution is 1 measurement every six seconds and the data for
    every timestamp are over several lines. In total the Grimm measures 32 the
    particel counts for 32 bins

    :param ifile: Grimm data text file; RS232 rawoutput stream
    :return: pandas DataFrame; using the timestamp as index
    :rtype: pandas.DataFrame
    """
    f = open(ifile, 'r')
    lines = f.readlines()
    f.close()

    # reading in the data into an OrderedDict using the unix timestamp as key
    result = OrderedDict()
    # go through every single line
    for line in lines:
        items = line.split()
        if items[0].endswith(',P'):
            continue
        else:
            key = line.split(',')[0]
            data = [int(i) for i in line.strip()[15:].split()]
            # check if key exist
            if key in list(result.keys()):
                result[key] += data
            else:
                result[key] = data
    ts = [datetime.datetime.utcfromtimestamp(float(i)) for i in list(result.keys())]
    # Transform dictionary to a pandas.DataFrame
    df = pd.DataFrame.from_dict(result, orient='index')
    df = df.set_index(pd.to_datetime(ts))
    # rename columns as grimm_bin01, grimm_bin02, ...
    df.columns = ['grimm_bin%.2i' % i for i in range(1, 33)]
    return df


def read_grimm(ifile, year, month, day, interp_1Hz=False):
    """Routine for reading in the post processed Grimm data text file. The
    data file does not contain a date, that is why year, month and day have to
    be passed to the routine.

    :param ifile: Grimm data text file; the raw RS232 output stream
    :type ifile: str
    :param year: year
    :type year: int
    :param month: month
    :type month: int
    :param day: day
    :params interp_1Hz: reindexes the data to 1Hz using the nearest fill method
    :type interp_1Hz: boolean
    :returns: data as pandas.DataFrame and size_table as 2d-list
    """
    f = open(ifile, 'r')
    lines = f.readlines()
    f.close()

    # reading in the data into an OrderedDict using the unix timestamp as key
    data = OrderedDict()
    size_table = []

    _names = lines[0].split()
    # go through every single line
    for line in lines[1:]:
        items = line.strip().split()
        if len(items) == 36:
            key = line.split()[0]
            _dat = [float(i) for i in line.strip().split()[1:]]
            data[key] = _dat
        elif len(items) == 3:
            try:
                items = [float(i) for i in items]
            except:
                items = [i for i in items]
            size_table.append(items)
        else:
            pass
    ts = [datetime.datetime(year, month, day, 0, 0, 0)+
          datetime.timedelta(seconds=int(sec)) for sec in list(data.keys())]
    # Transform dictionary to a pandas.DataFrame
    df = pd.DataFrame.from_dict(data, orient='index')
    df = df.set_index(pd.to_datetime(ts))
    df.columns = ['Grimm_%s' % s for s in _names[1:]]

    if interp_1Hz:
        new_index = pd.date_range(df.index.min(), df.index.max(), freq='S')
        df = df.reindex(index=new_index, method='nearest')
    return (df, size_table)

#ifile = '/home/axel/gdrive/atsc/data/faam/c065-oct-12/Grimm_UTC++.txt'
#df, st = read_grimm(ifile, 2017, 10, 12)