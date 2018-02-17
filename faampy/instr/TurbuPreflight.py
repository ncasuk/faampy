'''
Created on 9 Feb 2012

@author: axel
'''

import matplotlib as mpl
if __name__ == '__main__': mpl.use('Agg')
import matplotlib.pyplot as plt
import netCDF4
import os
import numpy as np
import scipy.stats

from faampy.utils.FileList import FileList
from faampy.utils.getFlightNumberFromFilename import getFlightNumberFromFilename
from faampy.utils.getDateFromFilename import getDateFromFilename
from faampy.utils.getRevisionFromFilename import getRevisionFromFilename

import faampy.core.utils

fid_to_int = lambda x: int(x.strip()[1:])


def guess_takeoff_time(ds):
    ias = np.mean(ds.variables['IAS_RVSM'][:], axis=1)
    ptch = np.mean(ds.variables['PTCH_GIN'][:], axis=1)
    flag = np.nanmin(np.where((ias > 60) & (ptch > 1))[0])
    return flag


def plot_flight(ncfile, *figname):
    ds = netCDF4.Dataset(ncfile, 'r')

    t = get_mpl_time(ds, 32)
    plt.clf()

    plt.plot_date(t.ravel(), ds.variables['P0_S10'][:].ravel(), '-', label='p0-centre')
    plt.plot_date(t.ravel(), ds.variables['PA_TURB'][:].ravel(), '-', label='pa-vertical')
    plt.plot_date(t.ravel(), ds.variables['PB_TURB'][:].ravel(), '-', label='pb-horizontal')
    plt.grid()
    ax = plt.gca()
    xtickformat = mpl.dates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(xtickformat)
    plt.ylabel('pressure (mb)')
    plt.xlabel('time (UTC)')
    plt.legend()
    take_off_time = t[guess_takeoff_time(ds)-600,0]
    xl = ax.get_xlim()
    plt.xlim((xl[0], take_off_time))
    plt.ylim((-5,5))
    if figname:
        print(figname)
        title = os.path.splitext(os.path.basename(figname[0]))[0]
        plt.title(title)
        plt.savefig(figname[0])


def plot_summary(infile, *figname):
    rawdata = np.genfromtxt(infile, delimiter=',', skiprows=1, converters={0: fid_to_int})
    data = np.array(zip(*rawdata))
    data = data.T
    plt.clf()
    plt.plot(data[:,0], data[:,1], 'o', label='pa-vertical')
    plt.plot(data[:,0], data[:,4], 'o', label='pb-horizontal')
    plt.plot(data[:,0], data[:,7], 'o', label='p0-centre')
    plt.grid()
    plt.xlim(np.min(data[:,0])-1, np.max(data[:,0])+1)
    plt.ylabel('pressure (mb)')
    plt.xlabel('fid')
    plt.legend()
    plt.tight_layout()
    if figname:
        plt.savefig(figname)


def turbu_stats(ncfile):
    ds = netCDF4.Dataset(ncfile, 'r')
    fid = faampy.core.utils.get_fid(ds)
    for parnam in ds.variables.keys():
        ds.variables[parnam].set_auto_maskandscale(False)
    take_off_index = guess_takeoff_time(ds)
    ix = (take_off_index-2400, take_off_index-1200)

    pa = ds.variables['PA_TURB'][ix[0]:ix[1],:]
    pa = np.reshape(pa, (20,1920))
    pb = ds.variables['PB_TURB'][ix[0]:ix[1],:]
    pb = np.reshape(pb, (20,1920))
    p0 = ds.variables['P0_S10'][ix[0]:ix[1],:]
    p0 = np.reshape(p0, (20,1920))

    ds.close()

    #pa[np.abs(pa) > 20] = np.nan
    #pb[np.abs(pb) > 20] = np.nan
    #p0[np.abs(p0) > 20] = np.nan

    pa_mean = np.mean(pa, 1)
    pb_mean = np.mean(pb, 1)
    p0_mean = np.mean(p0, 1)

    #n_trd_wspd, (min_trd_wspd, max_trd_wspd), mean_trd_wspd, var_trd_wspd, skew_trd_wspd, kurt_trd_wspd = scipy.stats.describe(trd_wspd)


    return (fid, pa_mean, pb_mean, p0_mean)


def process():
    pass


def test():
    ofilename = '/home/axel/turbu_preflight.txt'
    ofile = file(ofilename, 'w')
    ofile.write('fid,pa_mean,pa_min,pa_max,pb_mean,pb_min,pb_max,p0_mean,p0_min,p0_max\n')


    for ncfile in cdfl.FileList:
        out = []

        fid = getFlightNumberFromFilename(ncfile)
        if fid < 900:
            return
        try:
        #else:
            #fid, pa,pb,p0 = turbu_stats(file)
            print(ncfile)
            fid, pa,pb,p0 = turbu_stats(ncfile)
            out.append(fid)
            out.append(str(np.mean(pa)))
            out.append(str(np.min(pa)))
            out.append(str(np.max(pa)))

            out.append(str(np.mean(pb)))
            out.append(str(np.min(pb)))
            out.append(str(np.max(pb)))

            out.append(str(np.mean(p0)))
            out.append(str(np.min(p0)))
            out.append(str(np.max(p0)))
            print(out)
            ofile.write(','.join(out)+'\n')
        except:
            pass

    ofile.close()




#cdfl = FileList()
#cdfl.__createFileList__()
#cdfl.__createFileInfo__()
#cdfl.__filterByType__('core-hires')
#cdfl.__filterLatestRevision__()
#cdfl.__sortByFlightNumber__()


#cdfl.FileList.reverse()
test()

#for f in cdfl.FileList:
#    fid = getFlightNumberFromFilename(f)
#    d = getDateFromFilename(f)
#    r = getRevisionFromFilename(f)
#    try:
#        outfile = os.path.join('/home/axel/faam/faam_figures/qa_turbu_preflight/', 'qa-turbu_preflight_%s_r%.2i_b%.3i.png' % (d, r, fid))
#        plot_flight(f, outfile)
#    except:
#        pass


