import os
import sys
import numpy as np


# column names for the udp package
udp_def = [('id', '|S9'),
           ('packet_length', '<u4'),
           ('utc_time', '<u4'),
           ('ptp_sync', '|S1'),
           ('MFM', '<f4'),
           ('flight_num', '|S4'),
           ('CPU_Load', '<f4'),
           ('USB_disk_space', '<f4'),
           ('conc', '<f4'),
           ('pmt_volt', '<i4'),
           ('lamp_volt', '<i4'),
           ('lamp_int', '<i4'),
           ('internal_temp', '<f4'),
           ('react_temp', '<f4'),
           ('react_press', '<f4'),
           ('flow', '<f4'),
           ('flags', '|S9'),
           ('ten_min_so2', '<f4'),
           ('eight_hr_so2', '<u2'),
           ('ten_min_so2_alm', '<u2'),
           ('eight_hr_so2_alm', '<f4'),
           ('MFC2_absolute_pressure', '<f4'),
           ('MFC2_temperature', '<f4'),
           ('MFC2_volumetric_flow', '<f4'),
           ('MFC2_mass_flow', '<f4'),
           ('MFC2_set_point', '<f4'),
           ('MFC3_absolute_pressure', '<f4'),
           ('MFC3_temperature', '<f4'),
           ('MFC3_volumetric_flow', '<f4'),
           ('MFC3_mass_flow', '<f4'),
           ('MFC3_set_point', '<f4'),
           ('V6', '<u2'),
           ('V8', '<u2'),
           ('V9', '<u2'),
           ('MFC2_Set_Value', '<f4'),
           ('MFC3_Set_Value', '<f4'),
           ('concentration_raw', '<f4'),
           ('mean_zero_cal_status', '<u2'),
           ('zero', '<f4'),
           ('sensitivity', '<f4'),
           ('ev8_user_set_time', '<u2'),
           ('auto_zeroing', '>u2'),
           ('ev8_zero_interval', '>u2'),
           ('inflight_alarm_MOCCA', '>u2'),
           ('MOCCA_so2_time', '>u2'),
           ('MOCCA_so2_limit', '>u2'),
           ('ten_min_STEL_limit', '>u2'),
           ('eight_hr_TWA_limit', '>u2'),
           ('cal_conc', '<f4'),
           ('simulate_conc', '>u2'),
           ('mocca_so2_sim', '<f4'),
           ('mocca_so2_alm', '>u2')]

# TCP definition as a dictionary. The key of the dictionary
# represents the version
tcp_def = {}
tcp_def['v4'] = [('id', '|S9'),
                 ('packet_length', '>u4'),
                 ('utc_time', '>u4'),
                 ('ptp_sync', '|S1'),
                 ('dummy', '|S2'),
                 ('flight_num', '|S4'),
                 ('concentration_raw', '>f4'),
                 ('pmt_volt', '>i4'),
                 ('lamp_volt', '>i4'),
                 ('lamp_int', '>i4'),
                 ('internal_temp', '>f4'),
                 ('react_temp', '>f4'),
                 ('react_press', '>f4'),
                 ('flow', '>f4'),
                 ('flags', '|S8'),
                 ('MFM', '>f4'),
                 ('ten_min_so2', '>f4'),
                 ('eight_hr_so2', '>f4'),
                 ('ten_min_so2_alm', '>u2'),
                 ('eight_hr_so2_alm', '>u2'),
                 ('MFC2_absolute_pressure', '>f4'),
                 ('MFC2_temperature', '>f4'),
                 ('MFC2_volumetric_flow', '>f4'),
                 ('MFC2_mass_flow', '>f4'),
                 ('MFC2_set_point', '>f4'),
                 ('MFC3_absolute_pressure', '>f4'),
                 ('MFC3_temperature', '>f4'),
                 ('MFC3_volumetric_flow', '>f4'),
                 ('MFC3_mass_flow', '>f4'),
                 ('MFC3_set_point', '>f4'),
                 ('V6', '>u2'),
                 ('V8', '>u2'),
                 ('V9', '>u2'),
                 ('MFC2_Set_Value', '>f4'),
                 ('MFC3_Set_Value', '>f4'),
                 ('mean_zero_cal_status', '>u2'),
                 ('zero', '>f4'),
                 ('sensitivity', '>f4'),
                 ('ev8_user_set_time', '>u2'),
                 ('auto_zeroing', '>u2'),
                 ('ev8_zero_interval', '>u2'),
                 ('inflight_alarm_MOCCA', '>u2'),
                 ('MOCCA_so2_time', '>u2'),
                 ('MOCCA_so2_limit', '>u2'),
                 ('ten_min_STEL_limit', '>u2'),
                 ('eight_hr_TWA_limit', '>u2'),
                 ('cal_conc', '>f4'),
                 ('simulate_conc', '>u2'),
                 ('mocca_so2_sim', '>f4'),
                 ('mocca_so2_alm', '>u2')]


# https://stackoverflow.com/questions/15575878/how-do-you-remove-a-column-from-a-structured-numpy-array
def rmfield(a, *fieldnames_to_remove):
    return a[[name for name in a.dtype.names if name not in fieldnames_to_remove]]


def so2_udp_to_tcp(ifilename, ofilename, tcp_def_version='v4', verbose=False, to_dataframe=False):
    """
    Tool to convert the SO2 udp package into a tcp data package. This
    utilitity became necessary after the VANAHEIM2017 campaign when the SO2
    package was unavailable and had to be recreated from the udp package for
    post processing.

    :param ifilename: udp data file
    :param ofilename: outputfilename
    :param tcp_def_version: tcp definition version to be used (default: v4)
    :type tcp_def_version: str
    :param verbose: Makes the function a little bit more chatty
    :param to_dataframe: converts result to pandas.DataFrame
    :type to_dataframe: boolean (default: False)
    :return: udp data either as numpy.recarray or pandas.DataFrame (if keyword set)
    """

    if not os.path.exists(ifilename):
        sys.stdout.write('Input file does not exist. Leaving ...\n')
        sys.exit(1)

    # read the udp text file
    arr = np.genfromtxt(ifilename,
                        delimiter=',',
                        dtype=udp_def,
                        skip_header=10,
                        skip_footer=10)
    nrows = arr.shape[0]
    new_recs = np.recarray((nrows,), dtype=tcp_def[tcp_def_version])

    _varnames, _dtype = zip(*tcp_def[tcp_def_version])
    for var, _dt in tcp_def[tcp_def_version]:
        if verbose:
            sys.stdout.write('Processing %s ...\n' & var)
        if var not in arr.dtype.names:
            if verbose:
                sys.stdout.write('Skipping %s ...\n' & var)
            continue
        if var == 'id':
            new_recs[var] = '$CHTSOO02'
        elif var == 'packet_length':
            new_recs[var] = 159
        elif var == 'flags':
            # strip of the last character of the flag
            new_recs[var] = [i[:-1] for i in arr[var]]
        else:
            new_recs[var] = arr[var].astype(_dt)

    new_recs = new_recs[::-1]
    # get unique indices
    _, ix = np.unique(new_recs['utc_time'], return_index=True)
    new_recs = new_recs[ix]

    new_recs.tofile(ofilename)

    if to_dataframe:
        import pandas as pd
        from datetime import datetime
        result = pd.DataFrame.from_records(new_recs)
        result['timestamp'] = [datetime.utcfromtimestamp(i) for i in result['utc_time']]
        result.set_index('timestamp')
    else:
        result = new_recs
    return result
