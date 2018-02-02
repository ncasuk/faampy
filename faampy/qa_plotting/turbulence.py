#!/usr/bin/python
"""

Quality Assurance-Quality Check (QA-QC) plotting for the FAAM Core Turbulence#
probes:
- Aircraft horizontal wind vectors
- 5-hole turbulence probe

measuring incident airflow and 3-d wind components.


Layout (landscape):

 -------------------------------------------
  |                                         |
  | Timeseries of                           |
  |                                         |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  | Timeseries of                           |
  |                                         |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  | Timeseries of                           |
  |                                         |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  | Timeseries of                           |
  |                                         |
  -------------------------------------------
  -------------------------------------------
  |                                         |
  | Timeseries of                           |
  |                                         |
  -------------------------------------------


"""

import sys

import matplotlib as mpl
if __name__ == '__main__': mpl.use('Agg')
import matplotlib.pyplot as plt
import netCDF4
import numpy as np

from general import *
from style import *
from utils import *

FILTER_RANGES = {'ROLR_GIN':  (-3.0, 3.0),          ## rate-of-change of GIN roll angle
                 'ROLL_GIN':  (-3.0, 3.0),          ## Roll angle from POSAV GPS-aided Inertial Nav. unit (positive for left wing up)
                 'ALT_GIN':   (0, 10000),           ## Altitude from POS AV 510 GPS-aided Inertial Navigation unit
                 'HDGR_GIN':  (-1.5, 1.5),          ## rate-of-change of GIN heading
                 'HDG_GIN':   (2.0, 358.0),         ## Heading from POSAV GPS-aided Inertial Navigation unit
                 'ACLF_GIN':  (-1.0, 1.0),          ## Acceleration along the aircraft longitudinal axis (GIN) (positive forward)
                 'PITR_GIN':  (-2.0, 2.0),          ## rate-of-change of GIN pitch angle
                 'U_C':       (-80.0, 80.0),        ## Eastward wind component from turbulence probe and GIN
                 'V_C':       (-80.0, 80.0),        ## Northward wind component from turbulence probe and GIN
                 'TAS':       (100.0, 240.0),       ## True airspeed (dry-air) from turbulence probe
                 'TAS_RVSM':  (100.0, 240.0)}       ## True air speed from the aircraft RVSM (air data) system and deiced temperature


VARIABLE_NAMES = ['Time',         # Time of measurement (seconds since midnight on start date)
                  'WOW_IND',      # Weight on wheels indicator
                  'U_C',          # Eastward wind component
                  'V_C',          # Northward wind component
                  'TAS',          # True air speed measured by the turbulence probe
                  'TAS_RVSM',
                  'IAS_RVSM']     #


def add_hdg_offset(hdg, hdg_offset):
    """function takes care of angle calculations and substracts 360 if
    hdg is greater than 360 and adds 360 if angle is smaller than 0.
    """
    result = np.array(hdg) + hdg_offset
    result[np.where(result > 360.)] += -360.
    result[np.where(result < 0.)] += 360.
    return result


def calc_bulk_wspd(tas_rvsm, hdg_gin, gspd_north, gspd_east, dit, hdg_offset=None, tas_scale_factor=None):
    """calculates u and v as the aircraft does it

       see: http://delphiforfun.org/programs/Math_Topics/WindTriangle.htm
            http://www.pilotfriend.com/training/flight_training/nav/calcs.htm

    """
    if hdg_offset:
        hdg = add_hdg_offset(hdg_gin, hdg_offset)
    else:
        hdg = hdg_gin

    if not tas_scale_factor:
        tas_scale_factor = 0.9984
    #adjust tas for temperature effects
    tas = correct_tas_rvsm(tas_rvsm, dit, tas_scale_factor=tas_scale_factor)
    air_spd_east = np.cos(np.deg2rad(hdg - 90.)) * tas
    air_spd_north = np.sin(np.deg2rad(hdg - 90.)) * tas
    u = gspd_east - air_spd_east
    v = air_spd_north + gspd_north
    return (u, v)


def calc_wspd(u, v):
    """calculates the horizontal wind speed from u and v

    """
    wspd = np.sqrt(u**2 + v**2)
    return wspd


def calc_wdir(u, v):
    """Wind direction calculated from the northwards and
       eastwards component.

    """
    A = u * 0.0
    A[np.where(v > 0)] = 180.
    A[np.where((u > 0) & (v < 0))] = 360.
    wangle = np.rad2deg(np.arctan(u/v)) + A
    return wangle


def correct_tas_rvsm(tas_rvsm, dit, tas_scale_factor=None):
    """Correcting true airspeed measurement for temperature effect.
       dit is the deiced temperature measurements.

       see: http://en.wikipedia.org/wiki/Airspeed

    """
    if not tas_scale_factor:
        tas_scale_factor = 0.9984
    mach = tas_rvsm / (661.4788 * 0.514444) / np.sqrt(dit/288.15)
    delta_tas = 4.0739 - (32.1681 * mach) + (52.7136 * (mach**2))
    tas = (tas_rvsm - delta_tas) * tas_scale_factor
    return tas


def smooth(x, window_len=None):
    if not window_len:
        window_len=160
    #s = np.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
    w = np.ones(window_len, 'd')
    y = np.convolve(w/w.sum(), x, mode='same')
    return y


class TurbuOverview(object):

    def __init__(self):
        self.Data = None
        self.Index = None
        self.Hdg_offset = 0.35
        self.PlotData = {}

    def __get_index__(self):
        ix = np.empty(0)
        for key, val in FILTER_RANGES.items():
            #tmp = self.Data.variables[key][:]
            ix = np.concatenate((ix, np.where((self.Data.variables[key][:] < val[0]) |
                                              (self.Data.variables[key][:] > val[1]))[0]))
        self.Index = (np.unique(ix.astype(int))).tolist()

    def __get_xlim__(self):

        tmp = self.PlotData['TAS_RVSM'][:]
        if hasattr(tmp, 'fill_value'):
            tmp = tmp.data.ravel()
        else:
            tmp = tmp.ravel()
        ix = np.where(tmp > 100)
        xmin = self.PlotData['Time'][:].ravel()[np.min(ix)]
        xmax = self.PlotData['Time'][:].ravel()[np.max(ix)]
        return(xmin, xmax)

    def __mask_plot_data__(self, arr):
        #tmp = self.Data.variables[key][:].ravel()FIGURE_FILENAME_TEMPLATE = 'qa-cab_pres_temp_%s_r%.2i_%s.png
        #arr.ravel()[self.Index] = np.NAN
        arr[self.Index] = np.NAN
        return arr

    def __get_data_from_mfda__(self, mfda_file):
        if not mfda_file:
	    return
        m5 = M5()
        m5.read_data(mfda_file)
        m5.read_hddr()

        try:
            self.PlotData['TBPO'] = m5.get_data(773)
            self.PlotData['TBPC'] = m5.get_data(776)
            self.PlotData['TBPD'] = m5.get_data(777)
        except:
            pass

    def __get_data_from_netcdf__(self, ds):
        self.Data = ds

        for parnam in self.Data.variables.keys():
            self.Data.variables[parnam].set_auto_maskandscale(False)

        self.__get_index__()
        self.PlotData['Time'] = get_mpl_time(self.Data).repeat(32)

        if 'U_NOTURB' in self.Data.variables.keys():
            sys.stdout.write('Using [U,V]_NOTURB data from netcdf ...\n')
            u_bulk = self.Data.variables['U_NOTURB'][:].repeat(32).reshape(self.Data.variables['TAS_RVSM'].shape)
            v_bulk = self.Data.variables['V_NOTURB'][:].repeat(32).reshape(self.Data.variables['TAS_RVSM'].shape)
        else:
            hdg_offset = self.Hdg_offset
            sys.stdout.write('TurbuOverview hdg_offset set to %f\n' % (hdg_offset))
            u_bulk, v_bulk = calc_bulk_wspd(self.Data.variables['TAS_RVSM'][:],
                                            self.Data.variables['HDG_GIN'][:],
                                            self.Data.variables['VELN_GIN'][:],
                                            self.Data.variables['VELE_GIN'][:],
                                            self.Data.variables['TAT_DI_R'][:],
                                            hdg_offset=hdg_offset)

        u_c = self.Data.variables['U_C'][:]
        v_c = self.Data.variables['V_C'][:]

        wspd_bulk = calc_wspd(u_bulk, v_bulk)
        wdir_bulk = calc_wdir(u_bulk, v_bulk)
        wspd = calc_wspd(u_c, v_c)
        wdir = calc_wdir(u_c, v_c)

        if 'PA_TURB' in self.Data.variables.keys():
            self.PlotData['PA_TURB']= self.Data.variables['PA_TURB'][:]
        if 'PB_TURB' in self.Data.variables.keys():
            self.PlotData['PB_TURB']= self.Data.variables['PB_TURB'][:]
        if 'P0_S10' in self.Data.variables.keys():
            self.PlotData['P0_S10']= self.Data.variables['P0_S10'][:]

        self.PlotData['TAT_DI_R'] = self.Data.variables['TAT_DI_R'][:]

        if 'LWC_JW_U' in self.Data.variables.keys():
            self.PlotData['LWC_JW_U'] = self.Data.variables['LWC_JW_U'][:].repeat(8) # original data are 4Hz

        self.PlotData['WSPD_BULK'] = self.__mask_plot_data__(calc_wspd( u_bulk, v_bulk))
        self.PlotData['WSPD'] = self.__mask_plot_data__(calc_wspd(u_c, v_c))
        self.PlotData['TAS_RVSM'] = correct_tas_rvsm(self.Data.variables['TAS_RVSM'][:], self.Data.variables['TAT_DI_R'][:])
        self.PlotData['TAS_DIFF'] = self.__mask_plot_data__(self.Data.variables['TAS'][:] - \
                                                            correct_tas_rvsm(self.Data.variables['TAS_RVSM'][:], \
                                                                             self.Data.variables['TAT_DI_R'][:]))

        self.PlotData['WSPD_DIFF'] = self.__mask_plot_data__(wspd - wspd_bulk)
        self.PlotData['WDIR_DIFF'] = self.__mask_plot_data__(wdir - wdir_bulk)

    def close(self):
        """Closing netCDF dataset."""
        self.Data.close()

    def plot(self):
        # see: http://matplotlib.sourceforge.net/examples/pylab_examples/subplots_demo.html

        #fig = plt.figure()
        fig=self.fig
        #define xtick interval and format
        hourloc = mpl.dates.HourLocator()
        xtickformat = mpl.dates.DateFormatter('%H:%M')

        ax1 = fig.add_subplot(511)

        line1=plt.plot_date( self.PlotData['Time'][:].ravel(), self.PlotData['TAT_DI_R'][:].ravel(), '-', label= 'deiced TAT')
        plt.ylabel('Temp (K)')
        plt.ylim((210,310))
        plt.xlim(self.__get_xlim__())
        plt.setp(ax1.get_xticklabels(), visible=False)
        ax1.xaxis.set_major_locator(hourloc)
        ax1.xaxis.set_major_formatter(xtickformat)
        #ax1.legend()

        for label in ax1.get_yticklabels()[::2]:
            label.set_visible(False)


        xl = self.__get_xlim__()

        #liquid water measurements are not always available
        if 'LWC_JW_U' in self.PlotData.keys():
            cc=freeze_color_cycle(ax1)
            ax11=ax1.twinx()
            ax11.set_color_cycle(cc)

            line2=plt.plot_date(self.PlotData['Time'][:].ravel(), self.PlotData['LWC_JW_U'][:].ravel(), '-', label= 'LWC')
            plt.ylim((-0.2, 1.0))
            ax11.set_ylabel('LWC (g/kg)')
            ax11.grid(False)
            lines = line1+line2
            labs = [l.get_label() for l in lines]
            ax11.legend(lines,labs)

            for label in ax11.get_yticklabels()[::2]:
                label.set_visible(False)


        #plt.title(os.path.splitext(os.path.basename(imgfilename))[0], fontsize=24)

        ax1.set_autoscalex_on(False)

        ax2 = fig.add_subplot(512, sharex=ax1)
        ax2.set_autoscalex_on(False)
        ax2.set_ylabel('Pressure (mb)')
        plt.plot_date(self.PlotData['Time'].ravel(), self.PlotData['PA_TURB'].ravel(), '-', label='PA_TURB')
        plt.plot_date(self.PlotData['Time'].ravel(), self.PlotData['PB_TURB'].ravel() + 5, '-', label='PB_TURB+5')
        plt.plot_date(self.PlotData['Time'].ravel(), self.PlotData['P0_S10'].ravel(), '-', label='P0_S10')
        if 'TBPO' in self.PlotData.keys():
            plt.plot_date(self.PlotData['Time'].ravel(), self.PlotData['TBPO'].ravel(), '-', label='TBPO')
        if 'TBPC' in self.PlotData.keys():
            plt.plot_date(self.PlotData['Time'].ravel(), self.PlotData['TBPC'].ravel(), '-', label='TBPC')
        if 'TBPD' in self.PlotData.keys():
            plt.plot_date(self.PlotData['Time'].ravel(), self.PlotData['TBPD'].ravel(), '-', label='TBPD')
        ax2.legend()
        plt.xlim(self.__get_xlim__())
        plt.ylim((-20,200))
        plt.setp(ax2.get_xticklabels(), visible=False)
        ax2.xaxis.set_major_locator(hourloc)
        ax2.xaxis.set_major_formatter(xtickformat)

        for label in ax2.get_yticklabels()[::2]:
                label.set_visible(False)


        ax3 = fig.add_subplot(513, sharex=ax1)
        ax3.set_autoscalex_on(False)
        ix = np.where(np.isfinite(self.PlotData['WSPD_DIFF'].ravel()))[0]
        plt.plot_date(self.PlotData['Time'].ravel()[ix], self.PlotData['TAS_DIFF'].ravel()[ix], '.', label= 'tas_diff')
        plt.plot_date(self.PlotData['Time'].ravel()[ix], smooth(self.PlotData['TAS_DIFF'].ravel()[ix]), '.', label='smooth tas_diff' )
        #plt.ylabel('tas - tas_rvsm (ms-1)')
        plt.ylabel(r'$\Delta$ tas (m/s)')
        plt.setp(ax3.get_xticklabels(), visible=False)
        plt.xlim( self.__get_xlim__())
        plt.ylim((-5, 5))
        ax3.xaxis.set_major_locator(hourloc)
        ax3.xaxis.set_major_formatter(xtickformat)
        #ax3.legend()

        for label in ax3.get_yticklabels()[::2]:
                label.set_visible(False)

        ax4 = fig.add_subplot(514, sharex=ax1)
        ax4.set_autoscalex_on(False)
        ix = np.where(np.isfinite(self.PlotData['WSPD_DIFF'].ravel()))[0]
        plt.plot_date(self.PlotData['Time'].ravel()[ix], self.PlotData['WSPD_DIFF'].ravel()[ix], '.', label= 'wspd_diff')
        plt.plot(self.PlotData['Time'].ravel()[ix], smooth(self.PlotData['WSPD_DIFF'].ravel()[ix]), '.', label= 'smooth wspd_diff')
        #plt.ylabel('wspd - wspd_noturb (ms-1)')
        plt.ylabel(r'$\Delta$ wspd (m/s)')
        plt.xlim(self.__get_xlim__())
        plt.ylim((-6, 6))
        plt.setp(ax4.get_xticklabels(), visible=False)
        ax4.xaxis.set_major_locator(hourloc)
        ax4.xaxis.set_major_formatter(xtickformat)
        #ax4.legend()

        for label in ax4.get_yticklabels()[::2]:
            label.set_visible(False)

        ax5 = fig.add_subplot(515, sharex=ax1)
        ax5.set_autoscalex_on(False)
        ix = np.where(np.isfinite(self.PlotData['WDIR_DIFF'].ravel()))[0]
        plt.plot_date(self.PlotData['Time'].ravel()[ix],self.PlotData['WDIR_DIFF'].ravel()[ix], '.', label= 'wdir_diff')
        plt.plot_date(self.PlotData['Time'].ravel()[ix], smooth(self.PlotData['WDIR_DIFF'].ravel()[ix]), '.', label= 'smooth wdir_diff')
        plt.xlim(self.__get_xlim__())
        plt.ylim((-20, 20))
        plt.setp(ax5.get_xticklabels(), visible=True)
        plt.ylabel(r'$\Delta$ wdir (deg)')
        ax5.xaxis.set_major_locator(hourloc)
        ax5.xaxis.set_major_formatter(xtickformat)
        #ax5.legend()

        for label in ax5.get_yticklabels()[::2]:
            label.set_visible(False)

        #plt.savefig(imgfilename, sharex=ax1)
        #plt.clf()
        return plt.gcf()


def main(ds):
    fig=QaQc_Figure(landscape=True).setup()
    set_suptitle(fig, ds, 'QA-Turbulence')

    data=get_data(ds, VARIABLE_NAMES)

    TO = TurbuOverview()
    TO.__get_data_from_netcdf__(ds)
    TO.fig=fig
    fig=TO.plot()

    for ax in fig.get_axes():
        add_takeoff(ax, data)
        add_landing(ax, data)

    ax=fig.get_axes()[0]
    zoom_to_flight_duration(ax, data)
    add_time_buffer(ax)
    return TO.fig

#plt.close('all')
#ds = netCDF4.Dataset('./data/core_faam_20160215_v004_r0_b943.nc', 'r')
#fig = main(ds)

