#!/usr/bin/python

import datetime
import numpy as np

import matplotlib as mpl
if __name__ == '__main__':  mpl.use('Agg')

import matplotlib.pyplot as plt
from matplotlib.dates import date2num
from matplotlib.pyplot import *
import os
import re
import glob
import sys
import scipy
import scipy.stats


from ppodd.core import *
import ppodd.pod

from faampy.core.utils import conv_secs_to_time
from faampy.core.mrfdata import *

__author__ = "Axel Wellpott"
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Axel Wellpott"
__email__ = "axll@faam.ac.uk"
__status__ = "Development"

FIGURE_FILENAME_TEMPLATE='qa-heimann_%s_%s.png'


DATA_LOGGING_SYSTEM='DECADES'

class qa_heimann(cal_base):
    """QA plot for nevzorov

    """

    def __init__(self,dataset):
        self.input_names=['PRTAFT_heimann_calib_flag',
                          'CORCON_heim_c',
                          'CORCON_heim_t',
                          'WOW_IND']
        self.outputs=[]
        self.version=1.00
        cal_base.__init__(self,dataset)                                                                                                                                                              
                                                                                                                                                                                                     
    def process(self):                                                                                                                                                                               
        fig=process(self.dataset['FLIGHT'].data, self.dataset)
        


def remove_nans(arr):
    ix = np.where(np.isnan(arr) == True)[0]
    arr[ix] = 0
    return(arr)


def cal_heimann(drs141):
    """Calibrate target temperature. DRS -> Kelvin
    
    HEIMCAL  -6.252273E+1  1.896504E-3   0.00000E+0 ! Celsius #876 12_12_07
    """
    if DATA_LOGGING_SYSTEM == 'DECADES':
        result = 273.15 + -4.455532E+1 + 3.033176E-3 * drs141 
    elif DATA_LOGGING_SYSTEM == 'HORACE':
        result = 273.15 + -6.252273E+1 + 1.896504E-3 * drs141 
    else:
        result = None
    return result


def cal_bb(drs142):
    """Calibrates black body reference temperature. DRS -> Kelvin
    
    PRTCCAL  -2.963744E+1  1.152025E-3  0.00000E+0 ! Celsius  H686BA 10_11_07
    """ 
    if DATA_LOGGING_SYSTEM == 'DECADES':
        result = 273.15 + -2.230400E+1 + 1.920578E-3 * drs142
    elif DATA_LOGGING_SYSTEM == 'HORACE':
        result = 273.15 + -2.963744E+1 + 1.152025E-3 * drs142
    else:
        result = None
    return result


def oplot_wow(ds, ax):
    """oplots take off and landing as vertical lines
        
    """
    wow_min=np.where(ds['WOW_IND'] == 0)[0].min()
    wow_max=np.where(ds['WOW_IND'] == 0)[0].max()

    wow_times=ds['WOW_IND'].data.times/86400.+date2num(datetime.datetime.strptime('%i-%i-%i' % tuple(ds['DATE']), '%d-%m-%Y'))
    for i in [wow_min, wow_max]:
        ax.axvline(wow_times[i], lw=2, color='0.7', alpha=0.7)


def linear_fit(cal_data):
    y, x, _none, _none = zip(*cal_data)
    y = np.vstack(np.array(y)).flatten()
    x = np.vstack(np.array(x)).flatten()
    slope, intercept, r_value, p_value, slope_std_error = scipy.stats.linregress(x, y)
    if intercept > 0:
        result = 'y=%.2f*x+%.2f r^2=%.2f' % (slope, intercept, r_value**2)
    else:
        result = 'y=%.2f*x%.2f r^2=%.2f' % (slope, intercept, r_value**2)
    return result


def cal_on_decades(drs27):
    """Checks the last bit of the Signal Register to see
    if calibration flag is set.
    
    """
    status = drs27
    result = np.array(status, dtype=float)
    #convert to 1Hz and times to zero
    #result = np.sum(result, axis=1)
    #result[np.where(result < 2)] = 0
    #result[np.where(result == 2)] = 1
    #split into individual calibrations
    s_ix = list(np.where((result - np.roll(result, 1)) == 1)[0])
    e_ix = list(np.where((result - np.roll(result, 1)) == -1)[0])
    tmp = []
    for i in range(len(s_ix)):
        #only use calibration which lasted longer than 60 seconds
        if (e_ix[i]-s_ix[i]) > 60:
            tmp.append(range(s_ix[i], e_ix[i]))
    return tmp


def cal_on_horace(drs27):
    """Checks the last bit of the Signal Register to see
    if calibration flag is set.
    
    """
    status = []
    for val in drs27.ravel():
        try:
            status.append(int(tobin(int(val))[-1]))
        except:
            status.append(0)
    result = np.array(status).reshape(drs27.shape)
    #convert to 1Hz and times to zero
    result = np.sum(result, axis=1)
    result[np.where(result < 2)] = 0
    result[np.where(result == 2)] = 1
    #split into individual calibrations
    s_ix = list(np.where((result - np.roll(result, 1)) == 1)[0])
    e_ix = list(np.where((result - np.roll(result, 1)) == -1)[0])
    tmp = []
    for i in range(len(s_ix)):
        #only use calibration which lasted longer than 60 seconds
        if (e_ix[i]-s_ix[i]) > 60:
            tmp.append(range(s_ix[i], e_ix[i]))
    return tmp


def cal_on(drs27):
    if DATA_LOGGING_SYSTEM == 'DECADES':
        result = cal_on_decades(drs27)
    elif DATA_LOGGING_SYSTEM == 'HORACE':
        result = cal_on_horace(drs27)
    else:
        result = None
    return result

  
def extract_calibration_data(drs141, drs142, drs27, secs):
    #ix_arr = list(np.where(drs27 == 1)[0])
    ix_arr=cal_on(drs27)
    result = []
    if ix_arr:
        for ix in ix_arr:
	    #remove the first and last two seconds of data, because they are regularly unreliable
	    ix=ix[2:-2]
            if DATA_LOGGING_SYSTEM == 'DECADES':
	      result.append([drs141[ix,:], drs142[ix,:], ix, secs[ix]])
              #  result.append([drs141[ix], drs142[ix], ix, secs[ix]])
            elif DATA_LOGGING_SYSTEM == 'HORACE':
                result.append([drs141[ix,:], drs142[ix,:], ix, secs[ix,:]])

    return result


    
def heimann_cal_plot(cal_data, offset=None):
    
    #cut the last n values
    if not offset:
        offset = 10
    for cal in cal_data:
        l = '%s - %s' % (conv_secs_to_time(np.min(cal[3])), conv_secs_to_time(np.max(cal[3])))
        #plot(cal[1].ravel()[offset:], cal[0].ravel()[offset:], 'o', label=l)
        #plot(cal[1][offset:], cal[0][offset:], 'o', label=l)
        #print(cal)
        #stop
        plot(cal[1][offset:].ravel(), cal[0][offset:].ravel(), 'o', label=l)
    legend(loc=2, prop={'size': 10})
    xlabel('BB Temp (K)')
    ylabel('Surface Temp (K)')
    lim0 = np.min([xlim()[0], ylim()[0]])
    lim1 = np.max([xlim()[1], ylim()[1]])
    gca().set_aspect('equal')
    xlim((lim0, lim1))
    ylim((lim0, lim1))
    gca().set_autoscale_on(False)
    #oplot 1-to-1 line
    plot(gca().get_xlim(),gca().get_ylim(), linestyle='--', color='grey', linewidth=2)
    grid()
    
    
    
    
    
def process_horace(raw_data_file, outpath):
    fid = os.path.basename(raw_data_file)[0:4]
    #raw_data = os.path.join(root_data_path, '%s_raw_data.dat' % fid)
    fid=re.findall('b\d{3}', os.path.basename(raw_data_file))[0]
    import tempfile
    import zipfile
    temp_directory=tempfile.mkdtemp()
    with zipfile.ZipFile(raw_data_file, 'r') as z:
        z.extractall(temp_directory)
    for f in z.namelist():
        if 'raw_data' in f:
	    data_file=f
	elif 'raw_hddr' in f:
	    header_file=f
    m3 = M3()
    #m3.read_data(raw_data_file)
    m3.read_data(os.path.join(temp_directory, data_file))
    m3.read_hddr(os.path.join(temp_directory, header_file))
    p141 = remove_nans(m3.get_data(141))
    p142 = remove_nans(m3.get_data(142))
    p27 = remove_nans(m3.get_data(27))    
    secs = np.array(range(m3.Header.Issrtt[0], m3.Header.Issrtt[-1]+m3.Header.Length[-1]))
    heim_temp = cal_heimann(p141)
    bb_temp = cal_bb(p142)
    cal_data = extract_calibration_data(heim_temp, bb_temp, p27, secs)
    heimann_cal_plot(cal_data)
    if cal_data:
        ax = gca()
        formula = linear_fit(cal_data)
        ax.text(0.97, 0.05, formula,
                horizontalalignment='right',
                verticalalignment='bottom',
                transform=ax.transAxes)
            
    title(fid + ' ' + datetime.datetime.strptime(m3.Header.Date, '%d-%b-%y').strftime('%d-%m-%Y'))
    savefig(os.path.join(outpath, FIGURE_FILENAME_TEMPLATE % (datetime.datetime.strptime(m3.Header.Date, '%d-%b-%y').strftime('%Y%m%d'), fid)))
    clf()

    

def process_decades(raw_data_file, outpath):
    d=decades_dataset()
    d.add_file(raw_data_file)
    d.process()
    plt.close('all')
    #  d=decades_dataset
    fid=d['FLIGHT'].data
    input_names=['PRTAFT_heimann_calib_flag',
		 'CORCON_heim_c',
                 'CORCON_heim_t',
                 'WOW_IND']
    match=d.matchtimes(input_names)
    heim_c=d['CORCON_heim_c'].data.ismatch(match)
    #heim_c=heim_c.ravel()
    heim_t=d['CORCON_heim_t'].data.ismatch(match)
    #heim_t=heim_t.ravel()
    
    wow_ind=d['WOW_IND'].data.ismatch(match)
    calib_flag=d['PRTAFT_heimann_calib_flag'].data.ismatch(match)

    secs=heim_c.times

    heim_temp = cal_heimann(heim_t)
    bb_temp = cal_bb(heim_c)
    
    cal_data = extract_calibration_data(heim_temp, bb_temp, calib_flag, secs)

    heimann_cal_plot(cal_data)
    if cal_data:
        ax = gca()
        formula = linear_fit(cal_data)
        ax.text(0.97, 0.05, formula,
                horizontalalignment='right',
                verticalalignment='bottom',
                transform=ax.transAxes)
    fid=d['FLIGHT'].data
    datestring=re.findall('\d{8}', os.path.basename(raw_data_file))[0]

    plt.title('QA-Heimann\n'+ '%s - %s' % (fid, datetime.datetime.strptime(datestring, '%Y%m%d').strftime('%d-%m-%Y')))
    plt.savefig(os.path.join(outpath, FIGURE_FILENAME_TEMPLATE % (datestring, fid)))
    return plt.gcf()


  
  
def process(raw_data_file, outpath):
    global DATA_LOGGING_SYSTEM
    if raw_data_file.endswith('_rawdlu.zip'):
        DATA_LOGGING_SYSTEM='DECADES'
        result = process_decades(raw_data_file, outpath)
    elif raw_data_file.endswith('_rawdrs.zip'):
        DATA_LOGGING_SYSTEM='HORACE'
        result = process_horace(raw_data_file, outpath)        
    else:
        result = None
    return result




if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Creates Heimann calibration qa plot.',
                                     version=__version__,
                                     epilog='Report bugs to %s.' % __email__)
    #parser.add_argument('fid', action='store', type=str,
    #                    help='Single flight ID number or several separated by ","')
    parser.add_argument('raw_data_file',
			action='store',
			type=str,
                        help="raw data file. Either decades or horace format.")
    parser.add_argument('--outpath',
			action='store',
			type=str,
			default=os.environ['HOME'],
			help='outpath for image file')
    args = parser.parse_args()
    #plt.close('all')
    #process(args.raw_data_file, args.outpath)
    file_list=[]
    if os.path.isdir(args.raw_data_file):
        pattern = ['core_faam_\d{8}.*_?\d{3}_rawdlu.zip', 'core_faam_\d{8}.*_?\d{3}_rawdrs.zip']

        for root, subFolders, files in os.walk(args.raw_data_file):
            for f in files:
	        for p in pattern:
                    if re.match(p, os.path.basename(f)):
                        file_list.append(os.path.join(root, f))   
        if not file_list:
            sys.stdout.write('No raw data files found in ... %s\n Leaving \n\n' % args.ncfile)
            sys.exit()
    else:
        file_list = [args.raw_data_file,]

    file_list.sort()
    #remove duplicates
    #unique_file_list = []
    #if len(file_list) >= 2:
    #    for i in range(1, len(file_list)):
    #        if not (re.sub('_1[H,h]z', '', os.path.basename(file_list[i])) == os.path.basename(file_list[i-1])):
    #            unique_file_list.append(file_list[i])
    #    file_list = unique_file_list


    for f in file_list:
        try:
            process(f, args.outpath)
            sys.stdout.write('Processed ... %s\n' % (os.path.basename(f),))
        except:
            sys.stdout.write('Failed to process ... %s\n' % (os.path.basename(f),))

