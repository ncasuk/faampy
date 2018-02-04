"""
Module to create quicklooks from a netCDF using the flight summary
and a configuration file, that defines the plot layout (quicklook.cfg)


The config file should look similar to this::

[['BTHEIM_U']]
[['TSC_BLUU', 'TSC_GRNU', 'TSC_REDU'], ['BSC_BLUU', 'BSC_GRNU', 'BSC_REDU']]
[['PSAP_LIN'], ['PSAP_LOG'], ['PSAP_FLO', 'PSAP_TRA']]
[['NEPH_PR'], ['NEPH_T']]
[['NV_TWC_C', 'NV_LWC_C']]
[['WVSS2R_VMR', 'WVSS2F_VMR']]
[['PTCH_GIN',], ['TAS', 'TAS_RVSM']]

"""


import ast
import sys
import netCDF4
import os
import re
import numpy as np

import matplotlib as mpl
if __name__ == '__main__': mpl.use('Agg')
import matplotlib.pyplot as plt

from faampy.core.utils import get_fid, conv_time_to_secs, \
                              get_index_from_hhmmss, \
                              conv_secs_to_time, get_flight_duration
from faampy.core.flight_summary import FlightSummary, Event
from timeseries import Timeseries
from profile import Profile
from skewt import SkewT
from atlas import Map

try:
    import seaborn
except ImportError:
    sys.stdout.write('seaborn not available ...\n')


Plot_Config = [[['BTHEIM_U']],
               [['TSC_BLUU', 'TSC_GRNU', 'TSC_REDU'], ['BSC_BLUU', 'BSC_GRNU', 'BSC_REDU']],
               [['PSAP_LIN'], ['PSAP_LOG'], ['PSAP_FLO', 'PSAP_TRA']],
               [['NEPH_PR'], ['NEPH_T']],
               [['NV_TWC_C', 'NV_LWC_C']],
               [['WVSS2R_VMR', 'WVSS2F_VMR']],
               [['PTCH_GIN',], ['TAS', 'TAS_RVSM']]]



class Quicklooks(object):
    def __init__(self, fltsumm_file, core_file, outpath, *plot_config_file):
        self.Plot_Config = Plot_Config
        if plot_config_file:
            f = open(plot_config_file[0], 'r')
            lines = f.readlines()
            f.close()
            _pc = [ast.literal_eval('({0})'.format(line)) for line in lines]
            _pc = filter(bool, _pc) # remove empty lines
            self.Plot_Config = _pc

        self.Fltsumm_file = fltsumm_file
        self.Core_file = core_file
        self.Outpath = outpath
        self.flag = [0]
        self.no_overwrite = False

    def process(self):
        fltsumm_file = self.Fltsumm_file
        core_file = self.Core_file
        outpath = self.Outpath

        fs = FlightSummary(fltsumm_file)
        ds = netCDF4.Dataset(core_file, 'r')


        plot_type = 'timeseries'
        Start_time = fs.Entries[[x.Name.lower() for x in fs.Entries].index('t/o')].Start_time
        fs.Entries.reverse()
        try:
            Stop_time = fs.Entries[[x.Name.lower() for x in fs.Entries].index('land')].Start_time
        except:
            Stop_time = ''
        fs.Entries.reverse()
        if not Stop_time:
            duration = get_flight_duration(ds)
            Stop_time = conv_secs_to_time(conv_time_to_secs(Start_time)+duration, no_colons=True)
        Name = 'full-flight'
        e = Event()
        e.Start_time = Start_time
        e.Stop_time = Stop_time
        e.Name = Name
        fs.Entries.insert(0, e)

        cnt = -1

        for e in fs.Entries:
            cnt += 1
            if re.findall('full-flight', e.Name.lower()):
                plot_type='timeseries'
                # make a full plot
            elif re.findall('run|circle|leg|box', e.Name.lower()):
                plot_type='timeseries'
            elif re.findall('prof', e.Name.lower()):
                plot_type='profile'
            else:
                continue

            fid=get_fid(ds)

            sys.stdout.write('\n%s: %s to %s\n' % (e.Name, e.Start_time, e.Stop_time))
            if e.Start_time and e.Stop_time:
                x1=conv_time_to_secs(e.Start_time)
                e.Start_time=re.sub(':','',conv_secs_to_time(x1))
                x2=conv_time_to_secs(e.Stop_time)
                e.Stop_time=re.sub(':','',conv_secs_to_time(x2))
            else:
                continue
            limit=[('Time', (x1, x2)),]

            try:
                outfile=os.path.join(outpath,  '%s_e%.2i_%s_to_%s_%s.png' %  (fid,  cnt,  e.Start_time,  e.Stop_time,  'map'))
                if os.path.exists(outfile) and self.no_overwrite == True:
                    sys.exit(1)
                m=Map()
                m.setup(ds, [x1, x2])
                m.plot()
                fig=m.get_figure()
                fig.suptitle('%s-%s - %s to %s' % (fid, e.Name, e.Start_time, e.Stop_time))
                fig.savefig(outfile)
                plt.close(fig)
                sys.stdout.write('Created ... %s\n' % outfile)
            except:
                pass


            for cat in self.Plot_Config:
                plt.close('all')
                if 'WVSS2' in cat[0][0]:
                    flag=[0,1]
                else:
                    flag=[0,]
                par_str='-'.join([item.lower() for sublist in cat for item in sublist])
                outfile = os.path.join(outpath, '%s_e%.2i_%s_to_%s_%s_%s.png' %  (fid,  cnt,  e.Start_time,  e.Stop_time,  plot_type,  par_str))
                if os.path.exists(outfile) and self.no_overwrite == True:
                    pass
                else:
                    try:
                        if plot_type == 'timeseries':
                            p=Timeseries()
                        else:
                            p=Profile()
                    #plot for the time limits and only data values that are flagged 0
                        p.setup(ds, cat, limit, flag)
                        if not p.NO_DATA:
                            p.plot()
                            p.plot_formatter()
                            #flattened parameter string
                            #par_str='-'.join([item.lower() for sublist in cat for item in sublist])
                            outfile=os.path.join(outpath, '%s_e%.2i_%s_to_%s_%s_%s.png' % (fid, cnt, e.Start_time, e.Stop_time, plot_type, par_str))
                            fig=p.get_figure()
                            fig.suptitle('%s-%s - %s to %s' % (get_fid(ds), e.Name, e.Start_time, e.Stop_time))
                            plt.savefig(outfile)
                            sys.stdout.write('Created ... %s\n' % outfile)
                            plt.close(fig)
                    except:
                        outfile=os.path.join(outpath, '%s_e%.2i_%s_to_%s_%s_%s.png' % (fid, cnt, e.Start_time, e.Stop_time, plot_type, par_str))
                        sys.stdout.write('Could not create ... %s\n' % outfile)

            if plot_type == 'profile':
                outfile=os.path.join(outpath, '%s_e%.2i_%s_to_%s_%s.png' % (fid, cnt, e.Start_time, e.Stop_time, 'skewt'))
                if os.path.exists(outfile) and self.no_overwrite == True:
                    pass
                else:
                    try:
                        #sort index
                        s_ix=get_index_from_hhmmss(ds, e.Start_time)
                        e_ix=get_index_from_hhmmss(ds, e.Stop_time)

                        if len(ds.variables['PS_RVSM'].shape) == 2:
                            ix=np.argsort(np.mean(ds.variables['PS_RVSM'][:], axis=1).ravel())
                            pres=np.mean(ds.variables['PS_RVSM'][:], axis=1).ravel()[s_ix:e_ix]
                            dewp=np.mean(ds.variables['TDEW_GE'][:], axis=1).ravel()[s_ix:e_ix]-273.15

                            if 'U_C' in ds.variables.keys():
                                u=np.mean(ds.variables['U_C'][:], axis=1).ravel()[s_ix:e_ix]
                                v=np.mean(ds.variables['V_C'][:], axis=1).ravel()[s_ix:e_ix]
                            elif 'U_NOTURB' in ds.variables.keys():
                                u=np.mean(ds.variables['U_NOTURB'][:], axis=1).ravel()[s_ix:e_ix]
                                v=np.mean(ds.variables['V_NOTURB'][:], axis=1).ravel()[s_ix:e_ix]
                            else:
                                u=pres[:]*0.0
                                v=pres[:]*0.0
                            tat_di_r=np.mean(ds.variables['TAT_DI_R'][:], axis=1).ravel()[s_ix:e_ix]
                        else:
                            ix=np.argsort(ds.variables['PS_RVSM'][:])
                            pres=ds.variables['PS_RVSM'][:][s_ix:e_ix]
                            dewp=ds.variables['TDEW_GE'][:][s_ix:e_ix]-273.15

                            if 'U_C' in ds.variables.keys():
                                u=ds.variables['U_C'][:][s_ix:e_ix]
                                v=ds.variables['V_C'][:][s_ix:e_ix]
                            elif 'U_NOTURB' in ds.variables.keys():
                                u=ds.variables['U_NOTURB'][:][s_ix:e_ix]
                                v=ds.variables['V_NOTURB'][:][s_ix:e_ix]
                            else:
                                u=pres[:]*0.0
                                v=pres[:]*0.0
                            tat_di_r=ds.variables['TAT_DI_R'][:][s_ix:e_ix]

                        theta=(tat_di_r*(1000./pres)**(0.286)).ravel()
                        s=SkewT()
                        s.set_data(pres, theta, dewp, u, v)
                        if np.max(pres) > 900 and (np.max(pres)-np.min(pres) > 500):
                            s.zoom=False
                        else:
                            s.zoom=True
                        s.plot()
                        fig=s.get_figure()
                        fig.suptitle('%s-%s - %s to %s' % (get_fid(ds), e.Name, e.Start_time, e.Stop_time))
                        outfile=os.path.join(outpath, '%s_e%.2i_%s_to_%s_%s.png' % (fid, cnt, e.Start_time, e.Stop_time, 'skewt'))
                        sys.stdout.write('Created ... %s\n' % outfile)
                        fig.savefig(outfile)
                        plt.close(fig)
                    except:
                        outfile=os.path.join(outpath, '%s_e%.2i_%s_to_%s_%s.png' % (fid, cnt, e.Start_time, e.Stop_time, 'skewt'))
                        sys.stdout.write('Could not create ... %s\n' % outfile)
        ds.close()
        return

def _argparser():
    import argparse
    from argparse import RawTextHelpFormatter
    sys.argv.insert(0, 'faampy plt_quicklooks')
    parser = argparse.ArgumentParser(prog = 'faampy quicklooks', description=__doc__,
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('core_file', action="store", type=str, help='FAAM core netCDF')
    parser.add_argument('fltsumm_file', action="store", type=str, help='FAAM Flight Summary file')
    parser.add_argument('outpath', action="store", type=str, help='outpath where all the quicklook figures will be saved')
    parser.add_argument('--config_file', action="store", type=str, help='config file that defines the plots that are produced', default='')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()
    q = Quicklooks(args.fltsumm_file,
                   args.core_file,
                   args.outpath,
                   args.config_file)
    q.process()
    sys.stdout.write('Done ...\n')


if __name__ == '__main__':
    main()

#fltsumm_file = '/home/axel/gdrive/core_processing/2017/c013-may-17/flight-sum_faam_20170517_r0_c013.txt'
#core_file = '/home/axel/gdrive/core_processing/2017/c013-may-17/core_faam_20170517_v004_r0_c013.nc'

#q = Quicklooks(fltsumm_file, core_file, '/home/axel/c013_tmp')
#q.process()
