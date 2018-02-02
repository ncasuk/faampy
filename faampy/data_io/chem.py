
import os
import sys
import netCDF4

from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def read_nox(ifile):
    """
    Reads the NOx data from a simple txt file
    
    :param ifile: input data filename
    :type ifile: str
    :rtype: pandas.Dataframe
    
    """
    _date = datetime.strptime(os.path.basename(ifile).split('_')[1], '%y%m%d')
    year = _date.year
    month = _date.month
    day = _date.day
    nox_dateparse = lambda x: pd.datetime(year, month, day) + \
          timedelta(seconds=int(float(float(x) % 1)*86400.))

    df_nox = pd.read_csv(ifile, parse_dates=[0], date_parser=nox_dateparse)
    df_nox = df_nox.set_index('TheTime')  # Setting index using 'TheTime' col
    t = df_nox.index.values
    df_nox['timestamp'] = t.astype('datetime64[s]')  # Converting index data type
    df_nox = df_nox[['timestamp', 'no_conc', 'no2_conc', 'nox_conc']]
    df_nox[df_nox < 0] = np.nan
    return df_nox


def read_fgga_txt(ifile):
    """
    Reads the FGGA data from a txt file

    :param ifile: data filename
    :rtype: pandas.Dataframe
    """
    fgga_dateparse = lambda x: pd.datetime.utcfromtimestamp(int(x))
    # column names for the FGGA txt file
    fgga_names = ['identifier', 'packet_length', 'timestamp', 'ptp_sync',
                  'MFM', 'flight_num', 'CPU_Load', 'USB_disk_space', 'ch4',
                  'co2', 'h2o', 'press_torr', 'temp_c', 'fit_flag',
                  'rda_usec', 'rdb_usec', 'ch4_ppb', 'co2_ppm',
                  'MFC_1_absolute_pressure', 'MFC_1_temperature',
                  'MFC_1volumetic_flow', 'MFC_1mass_flow', 'MFC_1set_point',
                  'V1', 'V2', 'V3', 'V4', 'restart_FGGA', 'FGGA_Pump',
                  'CAL_MFC_1Set_Value']
    df_fgga = pd.read_csv(ifile,
                          names=fgga_names,
                          delimiter=',',
                          parse_dates=[2],
                          date_parser=fgga_dateparse,
                          skiprows=100)     # To be sure to skip the header

    # Using the valve states for flagging out calibration periods
    # TODO: add time buffer around calibration periods
    df_fgga.loc[df_fgga['V1'] != 0, 'ch4_ppb'] = np.nan
    df_fgga.loc[df_fgga['V2'] != 0, 'co2_ppm'] = np.nan
    df_fgga.loc[df_fgga['V2'] != 0, 'ch4_ppb'] = np.nan
    return df_fgga


def read_fgga_na(ifile):
    """
    Reads the FGGA data

    :param ifile: nasaAmes input filename
    :rtype: pandas.Dataframe
    
    """
    try:
        import nappy
    except:
        sys.stdout.write('Can not import nappy ...\n')
        return
    ds = nappy.openNAFile(ifile)
    ds.readData()

    timestamp = netCDF4.num2date(ds.X, ds.getIndependentVariable(0)[1])
    from collections import OrderedDict

    dict = OrderedDict()
    dict['timestamp'] = timestamp
    for i, v in enumerate(['co2_ppm', 'co2_flag', 'ch4_ppb', 'ch4_flag']):
        dict[v] = ds.V[i]
    df = pd.DataFrame(dict)
    df = df.set_index('timestamp')
    return df


def read_fgga(ifile):
    """Just a wrapper for the two other FGGA readers. Function looks at the
    suffix of the input file and uses either the txt or the nasaAMES reader.
    """
    if ifile.lower().endswith('.na'):
        return read_fgga_na(ifile)
    elif ifile.lower().endswith('.txt'):
        return read_fgga_txt(ifile)
    else:
        return


def read_icl_na(ifile, apply_flag=False):
    """Reads in the ICL data from the Manchester Aerodyne Tunable IR Laser
    Direct Absorption Spectrometer (TILDAS) model QC-TILDAS-DUAL

    :param ifile: nasaAmes input filename
    :type ifile: str
    :param apply_flag: flagged data are replaced by np.nan
    :type apply_flag: boolean
    :return: pandas.DataFrame
    
    """

    try:
        import nappy
    except:
        sys.stdout.write('Can not import nappy ...\n')
        return
    ds = nappy.openNAFile(ifile)
    ds.readData()

    timestamp = netCDF4.num2date(ds.X, ds.getIndependentVariable(0)[1])
    from collections import OrderedDict

    dict = OrderedDict()
    dict['timestamp'] = timestamp
    for i, v in enumerate(['c2h6_conc', 'c2h6_flag']):
        dict[v] = ds.V[i]
    df = pd.DataFrame(dict)
    df = df.set_index('timestamp')
    if apply_flag:
        df['c2h6_conc'][df['c2h6_flag'] != 0] = np.nan
    return df
