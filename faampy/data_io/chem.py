import datetime
import os

import numpy as np
import pandas as pd


def read_nox(ifile):
    _date = datetime.datetime.strptime(os.path.basename(ifile).split('_')[1], '%y%m%d')
    year = _date.year
    month = _date.month
    day = _date.day
    nox_dateparse = lambda x: pd.datetime(year, month, day) + \
          datetime.timedelta(seconds=int(float(float(x) % 1)*86400.))

    df_nox = pd.read_csv(ifile, parse_dates=[0], date_parser=nox_dateparse)
    df_nox = df_nox.set_index('TheTime')  # Setting index
    t = df_nox.index.values
    df_nox['timestamp'] = t.astype('datetime64[s]')  # Converting index data type
    df_nox = df_nox[['timestamp', 'no_conc', 'no2_conc', 'nox_conc']]
    df_nox[df_nox < 0] = np.nan
    return df_nox
    

def read_fgga(ifile)    :
    fgga_dateparse = lambda x: pd.datetime.utcfromtimestamp(int(x))
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

    # Using the Valve states for flagging out calibration periods
    # TODO: add time buffer around calibration periods
    df_fgga.loc[df_fgga['V1'] != 0, 'ch4_ppb'] = np.nan
    df_fgga.loc[df_fgga['V2'] != 0, 'co2_ppm'] = np.nan
    df_fgga.loc[df_fgga['V2'] != 0, 'ch4_ppb'] = np.nan    
    return df_fgga
