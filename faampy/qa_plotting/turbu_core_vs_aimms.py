#!/usr/bin/env python
'''
Created on 21 Jan 2015

@author: axel
'''

import datetime
import matplotlib as mpl
if __name__ == '__main__': mpl.use('Agg')
import matplotlib.pyplot as plt
import netCDF4
import numpy as np
import os
import re
import sys

from matplotlib.dates import date2num, num2date
from matplotlib import gridspec
from faampy.core.utils import get_mpl_time

mpl.rcParams['figure.figsize'] = 11.69, 8.27,


FIGURE_FILENAME_TEMPLATE = 'qa-cab_pres_temp_%s_r%.2i_%s.png'

def oplot_wow(ds, ax):
    """oplots take off and landing as vertical lines
        
    """
    wow=ds.variables['WOW_IND'][:].ravel()
    gspd_gin=ds.variables['GSPD_GIN'][:,0]
    wow_min=np.where((wow == 0) & (gspd_gin > 60))[0].min()
    wow_max=np.where(wow == 0)[0].max()

    wow_times=get_mpl_time(ds)
    for i in [wow_min, wow_max]:
        ax.axvline(wow_times[i], lw=2, color='0.7', alpha=0.7)
    return (wow_times[wow_min], wow_times[wow_max])


def get_limits(ds_core, ds_aimms):
    lim_0=np.max([ds_core.variables['Time'][:][0], ds_aimms.variables['TIME'][:][0]])
    lim_1=np.min([ds_core.variables['Time'][:][-1], ds_aimms.variables['TIME'][::20][-1]])
    return (lim_0, lim_1)
    
    
def get_data(ds_core, ds_aimms, var_core, var_aimms, ix_s, ix_e):
    core_ix=np.where((ds_core.variables['Time'][:] > ix_s) & (ds_core.variables['Time'][:] < ix_e))[0]
    core_result=ds_core.variables[var_core][core_ix,:]
    
    rows, cols=(ds_aimms.variables['TIME'][:].size/20, 20)
    aimms_ix=np.where((ds_aimms.variables['TIME'][::20] > ix_s) & (ds_aimms.variables['TIME'][::20] < ix_e))[0]
    aimms_result=ds_aimms.variables[var_aimms][:].reshape((rows, cols))[aimms_ix,:]
 
 
    from scipy.interpolate import UnivariateSpline
    core_rows, core_cols=core_result.shape    
    x1=np.linspace(0, core_rows+1, core_rows*core_cols+1)[:-1]
    x2=np.linspace(0, core_rows+1, core_rows*20+1)[:-1]
    spl=UnivariateSpline(x1, core_result.ravel())
    core_result=spl(x2)
    
    return (core_result.ravel(), aimms_result.ravel())   
 

 
 
 
 



    
ds_core=netCDF4.Dataset('/home/axel/Dropbox/campaigns/spring2015/b908-may-20/core_faam_20150520_v004_r2_b908.nc', 'r')
ds_aimms=netCDF4.Dataset('/home/axel/Dropbox/campaigns/spring2015/data/aimms/metoffice-aimms_faam_20150520_v003_r0_b908.nc', 'r')
#t_core=get_mpl_time(ds_core)

lim=get_limits(ds_core, ds_aimms)
print(lim)

fig0=plt.figure()
fig0.set_size_inches((8.27, 11.69))
gs=gridspec.GridSpec(2,1)
ax0_0=fig0.add_subplot(gs[0,0], aspect='equal')
ax0_1=fig0.add_subplot(gs[1,0], aspect='equal')

core_tat, aimms_tat =get_data(ds_core, ds_aimms, 'TAT_DI_R', 'TK', lim[0], lim[1])

ax0_0.plot(core_tat, aimms_tat, '.')
#ax0_0.set_xlim()
#ax0_0.set_ylim((60, 120))
ax0_0.grid()

ax0_1.plot(core_tat, aimms_tat, '.')
ax0_1.grid()



fig1=plt.figure()
fig1.set_size_inches((8.27, 11.69))
gs=gridspec.GridSpec(3,2)
ax1_0=fig1.add_subplot(gs[0,0], aspect='equal') # u
ax1_1=fig1.add_subplot(gs[1,0], aspect='equal') # v
ax1_2=fig1.add_subplot(gs[2,0], aspect='equal') # W
ax1_3=fig1.add_subplot(gs[0,1], aspect='equal') # TAS
ax1_4=fig1.add_subplot(gs[1,1], aspect='equal') # AOA
ax1_5=fig1.add_subplot(gs[2,1], aspect='equal') # AOSS


core_u, aimms_u =get_data(ds_core, ds_aimms, 'U_C', 'U', lim[0], lim[1])
core_v, aimms_v =get_data(ds_core, ds_aimms, 'V_C', 'V', lim[0], lim[1])
core_w, aimms_w =get_data(ds_core, ds_aimms, 'W_C', 'W', lim[0], lim[1])
ax1_0.plot(core_u, aimms_u, '.')
ax1_1.plot(core_v, aimms_v, '.')
ax1_2.plot(core_w, aimms_w, '.')




def cabin_pressure(ds, out_filename):
    """Creates an overview plot for GE and BUCK for one flight.

    """
    #Read all necessary data from netCDF dataset and convert to 1Hz
    alt = np.mean(ds.variables['ALT_GIN'][:], axis=1).ravel()

    time_data=get_mpl_time(ds)
    if 'WOW_IND' in ds.variables.keys():
        wow_ind=ds.variables['WOW_IND'][:]
        ix=np.where(wow_ind == 0)[0]
        ix_s, ix_e=np.min(ix), np.max(ix)
    elif 'TAS_RVSM' in ds.variables.keys():
        tas_data=np.mean(ds.variables['TAS_RVSM'][:], axis=1).ravel()
        ix_s=np.min(np.where(tas_data > 80))
        ix_e=np.max(np.where(tas_data > 80))

    fig=plt.figure()
    if hasattr(ds, 'title'):
        fig.suptitle(ds.title[10:])
    elif hasattr(ds, 'Title'):
        fig.suptitle(ds.Title[10:])
    else:
        pass

    cab_pres=ds.variables['CAB_PRES'][:,0]
    cab_temp=ds.variables['CAB_TEMP'][:,0]
    ps_rvsm=ds.variables['PS_RVSM'][:,0]

    cab_pres[cab_pres <= 0] = np.nan
    ps_rvsm[ps_rvsm <= 0] = np.nan
    cab_temp[cab_temp <= 0] = np.nan

    hourloc = mpl.dates.HourLocator()
    xtickformat = mpl.dates.DateFormatter('%H:%M')

    plt.plot_date(time_data, cab_pres,'-',lw=2,color='b', label='CAB_PRES')
    plt.plot_date(time_data, ps_rvsm,'-',lw=2,color='g', label='PS_RVSM')
    oplot_wow(ds, plt.gca())
    plt.legend(loc=3)

    

    plt.gca().xaxis.set_major_formatter(xtickformat)
    plt.grid()
    plt.ylabel('pressure (mb)')
    plt.xlabel('utc')

    plt.twinx()
    plt.plot_date(time_data, cab_temp, '-', lw=2, color='r', label='CAB_TEMP')
    plt.ylabel('cabin temperature (C)')
    plt.legend(loc=4)

    plt.gca().xaxis.set_major_locator(hourloc)
    plt.gca().xaxis.set_major_formatter(xtickformat)

    plt.savefig(out_filename)
    plt.clf()



if __name__ == '__XXXmain__':
    import argparse
    parser = argparse.ArgumentParser(description="""Creates figures comparing the core data variables with those from the aimms probe.""")
    parser.add_argument('ncfile',
			action='store',
			type=str,
                        help='input FAAM core file *or* directory. When input is a directory the script finds recursively all 1hz netcdf files inside the path and processes them.')
    parser.add_argument('ncfile',
			action='store',
			type=str,
                        help='aimms data file.')
    parser.add_argument('--outpath',
			action='store',
			type=str,
			default=os.environ['HOME'],
                        help='outpath for image file')
    args = parser.parse_args()

    file_list = []

    if os.path.isdir(args.ncfile):
        pattern = 'core_faam_\d{8}.*_?\d{3}.*.nc'
        for root, subFolders, files in os.walk(args.ncfile):
            for f in files:
                if re.match(pattern, os.path.basename(f)):
                    file_list.append(os.path.join(root, f))
        if not file_list:
            sys.stdout.write('No core netcdf files found in ... %s\n Leaving \n\n' % args.ncfile)
            sys.exit()
    else:
        file_list = [args.ncfile,]

    file_list.sort()
    #remove duplicates
    unique_file_list = []
    if len(file_list) >= 2:
        for i in range(1, len(file_list)):
            if not (re.sub('_1[H,h]z', '', os.path.basename(file_list[i])) == os.path.basename(file_list[i-1])):
                unique_file_list.append(file_list[i])
        file_list = unique_file_list


    for f in file_list:
        try:
            process(f, args.outpath)
            sys.stdout.write('Processed ... %s\n' % (os.path.basename(f),))
        except:
            sys.stdout.write('Failed to process ... %s\n' % (os.path.basename(f),))
