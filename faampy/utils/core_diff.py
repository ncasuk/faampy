"""
Compares two FAAM core netCDFs. This utility is useful to get a change history
for FAAM core revision of the same flight.

The comparison is done for several aspects of the datasets

* Size of the dataset

* contained Variables

* Flight Constants

"""

import difflib
from datetime import datetime
import os
import sys
from netCDF4 import Dataset

from faampy.utils.file_list import File_List


def _get_data_date(ds):
    # the data_date attribute exists in different formats; to catch this
    # we go through the different options
    datestring = 'unknown'
    if hasattr(ds, 'Data_Date'):
        try:
            datestring = datetime.strptime(ds.Data_Date, '%Y%m%d').strftime('%Y-%m-%d')
        except:
            pass
        try:
            datestring = datetime.strptime(ds.Data_Date.lower(), '%d-%b-%Y').strftime('%Y-%m-%d')
        except:
            pass
    elif hasattr(ds, 'data_date'):
        datestring = datetime.strptime(ds.data_date, '%Y%m%d').strftime('%Y-%m-%d')
    else:
        pass
    return datestring


def core_diff(ds1_filename, ds2_filename):
    """
    Comparess two FAAM core netCDF. This is especially useful to quickly
    display the differences between two revisions.

    :param str ds1_filename: FAAM core netCDF file name
    :param str ds2_filename: FAAM core netCDF file name
    :returns: The output text, that describes the differences between the two
      FAAM core datasets
    :rtype: string
    """
    ds1 = Dataset(ds1_filename)
    ds2 = Dataset(ds2_filename)

    out = ['\n', '\n']

    # Info about te datasets we are comparing
    out.append('Comparing:\n')
    out.append('  ds-1: %s\n' % os.path.basename(ds1.filepath()))
    out.append('  ds-2: %s\n' % os.path.basename(ds2.filepath()))
    out.append('\n')

    # compare Dimension
    out.append('Dimension size:\n')
    if 'Time' in list(ds1.variables.keys()):
        out.append('  ds-1: %i\n' % (ds1.variables['Time'].size))
    elif 'TIME' in list(ds1.variables.keys()):
        out.append('  ds-1: %i\n' % (ds1.variables['TIME'].size))
    else:
        pass
    if 'Time' in list(ds2.variables.keys()):
        out.append('  ds-2: %i\n' % (ds2.variables['Time'].size))
    elif 'TIME' in list(ds2.variables.keys()):
        out.append('  ds-1: %i\n' % (ds2.variables['TIME'].size))
    else:
        pass
    out.append('\n')

    # compare Data_Date
    out.append('Dataset Creation Timestamp:\n')
    ds1_datestring = _get_data_date(ds1)
    ds2_datestring = _get_data_date(ds2)
    out.append('  ds-1: %s\n' % (ds1_datestring))
    out.append('  ds-2: %s\n' % (ds2_datestring))
    out.append('\n')

    # compore SoftwareVersion
    out.append('SoftwareVersion:\n')
    ds1_sv, ds2_sv = 'undefined', 'undefined'
    if hasattr(ds1, 'SoftwareVersion'):
        ds1_sv = ds1.SoftwareVersion
    if hasattr(ds2, 'SoftwareVersion'):
        ds2_sv = ds2.SoftwareVersion
    out.append('  ds-1: %s\n' % (ds1_sv))
    out.append('  ds-2: %s\n' % (ds2_sv))
    out.append('\n')

    # compare variables
    out.append('Variables Differences:\n\n')
    delta = sorted(list(set(ds1.variables.keys())^set(ds2.variables.keys())))
    if delta:
        # The output is formatted as a nice ASCII table
        out.append(23*'-'+'\n')
        out.append('%12s | ds1  ds2\n' % ('Var'))
        out.append(23*'-'+'\n')
        for var in delta:
            var_in_ds1 = ' '
            var_in_ds2 = ' '
            # x indicates that the variable is available
            if var in list(ds1.variables.keys()):
                var_in_ds1 = 'x'
            if var in list(ds2.variables.keys()):
                var_in_ds1 = 'x'
            # omit any _FLAG variables
            if not var.endswith('_FLAG'):
                out.append('%12s |  %1s    %1s \n' % (var, var_in_ds1, var_in_ds2))
        out.append(23*'-'+'\n')
    else:
        out.append('  Variables are identical\n')
    out.append('\n')

    # comparing Flight Constants
    out.append('Flight Constants:\n')

    if (hasattr(ds1, 'Flight_Constants') and (hasattr(ds2, 'Flight_Constants'))):
        diff = difflib.Differ().compare(ds1.Flight_Constants.split('\n'), ds2.Flight_Constants.split('\n'))
        changes = [l for l in diff if l.startswith('+ ') or l.startswith('- ')]
        for c in changes:
            out.append('  '+c+'\n')
        out.append('\n')
    else:
        out.append('\n  Flight_Constants attribute not in both Datasets.\n')

    ds1.close()
    ds2.close()
    return ''.join(out)


def _argparser():
    import argparse
    #sys.argv.insert(0, 'faampy core_diff')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('faam_core_netcdf_1', action="store", type=str,
                        help='1st FAAM netCDF used for comparison.')
    parser.add_argument('faam_core_netcdf_2', action="store", type=str,
                        help='2nd FAAM netCDF used for comparison.')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()
    print(args)
    out = core_diff(args.faam_core_netcdf_1, args.faam_core_netcdf_2)
    print(out)

if __name__ == '__main__':
    main()



TESTING = False
# TESTING
if TESTING:
    fl = File_List('/home/data/faam/badcMirror')
    fl.filter_by_data_type('core-hires')

    fids = sorted(list(set([f.fid for f in fl])))

    for fid in fids:
        _fl = [f for f in fl if f.fid == fid]
        if len(_fl) >= 2:
            for i in range(0, len(_fl)-1):
                try:
                    netcdf1 = os.path.join(_fl[i].path, _fl[i].filename)
                    netcdf2 = os.path.join(_fl[i+1].path, _fl[i+1].filename)
                    d = core_diff(netcdf1, netcdf2)
                    print(d)
                except:
                    sys.stdout.write('Problem processing %s ...\n' % fid)
        else:
            sys.stdout.write('Only one revision available for %s ...\n' % fid)
