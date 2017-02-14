#!/usr/bin/env python

"""
Extracts variables from netCDF and writes those to a csv file.

"""


from faampy.core.utils import get_mpl_time
from matplotlib.dates import num2date

import netCDF4
import os
import re
import sys
import zipfile


def get_fid(ds):
    """
    Get the flight ID ([b,d]nnn) from netCDF4.Dataset.

    :param ds: core_faam dataset
    :type param: netCDF4.Dataset

    >>> ncfile = 'core_faam_20130403_v004_r0_b768.nc'
    >>> ds = netCDF4.Dataset(ncfile, 'r')
    >>> print(get_fid(ds))
    b768

    """
    # parse the title global attribute of the netcdf
    if hasattr(ds, 'title'):
        result = str(re.findall('[b,B,d, D, p,P]\d{3}', ds.title)[0])
        result = result.lower()
    elif hasattr(ds, 'Title'):
        result = str(re.findall('[b,B,d, D, p,P]\d{3}', ds.Title)[0])
        result = result.lower()
    else:
        result = ""
    return result


PARAMS = ['ACLD_GIN',
          'ACLF_GIN',
          'ACLS_GIN',
          'ALT_GIN',
          'AOA',
          'AOSS',
          'GSPD_GIN',
          'HDGR_GIN',
          'HDG_GIN',
          'HGT_RADR',
          'IAS_RVSM',
          'LAT_GIN',
          'LON_GIN',
          'LWC_JW_U',
          'NV_LWC_U',
          'NV_TWC_U',
          'P0_S10',
          'P9_STAT',
          'PALT_RVS',
          'PA_TURB',
          'PB_TURB',
          'PITR_GIN',
          'PSP_TURB',
          'PS_RVSM',
          'PTCH_GIN',
          'Q_RVSM',
          'ROLL_GIN',
          'ROLR_GIN',
          'TAS',
          'TAS_RVSM',
          'TAT_DI_R',
          'TAT_ND_R',
          'TDEW_GE',
          'TRCK_GIN',
          'TWC_EVAP',
          'TWC_TDEW',
          'U_C',
          'U_NOTURB',
          'VELD_GIN',
          'VELE_GIN',
          'VELN_GIN',
          'VMR_CR2',
          'VMR_C_U',
          'V_C',
          'V_NOTURB',
          'WOW_IND',
          'WVSS2F_VMR',
          'WVSS2R_VMR',
          'W_C']



def process(ds, params, outfile=None, include_flag=False):

    if include_flag:
        new_params = []
        for p in params:
            new_params.append(p)
            new_params.append(p+'_FLAG')
        params = new_params

    n = ds.variables['Time'][:].size
    dt = [i[0].strftime('%Y-%m-%d %H:%M:%S') for i in num2date(get_mpl_time(ds, 1))]

    result = [[None,]*(len(params)+1) for i in range(n)]

    for i in range(n):
        result[i][0] = dt[i]
        for j, var in enumerate(params, 1):
            if var.endswith('_FLAG'):
                if var not in ds.variables.keys():
                    result[i][j] = '3'
                else:
                    try:
                        result[i][j] = str(int(ds.variables[var][i,0]))
                    except:
                        result[i][j] = '3'
            else:
                if var not in ds.variables.keys():
                    result[i][j] = '-9999.0'
                else:
                    result[i][j] = str(float(ds.variables[var][i,0]))
    header = ','.join(['utc',]+params)

    if outfile:
        out = open(outfile, 'w')
        txt='\n'.join([','.join(line) for line in result])
        out.write(header+'\n')
        out.write(txt)
        out.close()
    return (result, header+txt)



if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Creates a csv file from a netCDF.')
    parser.add_argument('ncfile', action='store', type=str,
                        help="FAAM core file *or* a directory. When input is a directory the script finds recursively all 1hz netCDF files inside the path and processes them.")
    parser.add_argument('--outpath',
                        action='store',
                        type=str,
                        default=os.environ['HOME'],
                        help="Outpath for the csv file.")
    args = parser.parse_args()

    file_list=[]
    if os.path.isdir(args.ncfile):
        pattern = 'core_faam_\d{8}.*_?\d{3}.nc'
        for root, subFolders, files in os.walk(args.ncfile):
            for f in files:
                if re.match(pattern, os.path.basename(f)):
                    file_list.append(os.path.join(root, f))
        if not file_list:
            sys.stdout.write('No core netcdf files found in ... %s\n Leaving \n\n' % args.ncfile)
            sys.exit()
    else:
        file_list = [args.ncfile,]

    for f in file_list:
        sys.stdout.write('Processing ... %s\n' % (f,))
        ds = netCDF4.Dataset(f, 'r')
        fid = get_fid(ds)
        outfile = os.path.join(args.outpath, os.path.basename(f)[:-3]+'_tamdar_extract.csv')
        hdr, data = process(ds, PARAMS, outfile=outfile, include_flag=True)
        arc = zipfile.ZipFile(os.path.splitext(outfile)[0]+'.zip', 'w', zipfile.ZIP_DEFLATED)
        arc.write(outfile, os.path.basename(outfile))
        arc.close()