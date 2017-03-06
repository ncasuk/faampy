'''
Created on 15 May 2013

@author: axel
'''

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
from matplotlib.ticker import MaxNLocator, ScalarFormatter
import sys

import faampy.core.utils

params = {'legend.fontsize': 10,}
plt.rcParams.update(params)

#TODO: add xlabel and ylabel
#TODO: use flagging
#TODO: deal with parameter input that do not exist in the core faam data set


class Timeseries(object):
    """Timeseries plotting class to create matplotlib figures from the FAAM
    core netcdf data files. This is especially useful for creating quick
    overview plots for qa purposes.
    
    Several parameters can be plotted in one axes or axes are stacked vertically.
    
    """
    
    def __init__(self, *args, **kwargs):
        """

        """
        self.NO_DATA = None
        self.fig = None
        self.x_data = []
        self.y_data = []
        self.label = []        


    def __get_mask__(self, parname):
        if not parname+'_FLAG' in self.ds.variables.keys():
            flag_data = np.zeros(self.ds.variables[parname].shape).astype(bool)
        else:
            flag_data = self.ds.variables[parname+'_FLAG'][:]
        mask = np.zeros(self.ds.variables[parname].shape).astype(bool)
        if not parname+'_FLAG' in self.ds.variables.keys():
            return mask
        
        flag_data = self.ds.variables[parname+'_FLAG'][:]        
        for f in self.flag:
            mask[flag_data == f] = False
        mask[self.ds.variables[parname][:] == -9999] = True
        return mask

    def setup(self, ds, vars, *args):
        """ds: netCDF4.Dataset
        vars: list of variable names that should be plotted
        """
        self.ds=ds
        self.vars=list(vars)
        self.index=range(self.ds.variables['Time'].shape[0])

        #check that all the pars exist in netcdf file
        is_var = lambda var: var.upper() in [i.upper() for i in self.ds.variables.keys()]
        pars = []
        for l in self.vars:            
            pars.append([item for item in l if is_var(item)])
            diff = set(l).difference(pars[-1])
            if diff:
                sys.stdout.write('Skip %s because variable is not in dataset.\n' % (','.join(diff)))
        if not [item for sublist in pars for item in sublist]:
            self.NO_DATA = True
            return 0
        else:
            self.NO_DATA = False
        self.vars = pars
        
        try:
            self.index = faampy.core.utils.data_filter(self.ds, args[0])
        except:
            self.index = range(0, self.ds.variables['Time'].size)
        self.index=sorted(self.index)
        try:
            self.flag = args[1]
        except:
            self.flag = [0,1,2,3]
                        
        #for i in range(len(self.vars)):
        #    self.subplt.append(self.fig.add_subplot(len(self.vars), 1, i+1))    
        self.fig, self.axs=plt.subplots(nrows=len(self.vars), sharex=True)
        if len(self.vars) == 1:
	    self.axs=np.array([self.axs,])
                    
        for i in range(len(self.vars)):
            self.x_data.append([])
            self.y_data.append([])
            for j in range(len(self.vars[i])):
                if len(ds.variables[self.vars[i][j]][:].shape) == 2:
                    (rows, cols) = ds.variables[self.vars[i][j]][:].shape
                    self.x_data[i].append(np.ravel(faampy.core.utils.get_mpl_time(ds, cols)[self.index,:]))
                else:
                    self.x_data[i].append(np.ravel(faampy.core.utils.get_mpl_time(ds)[self.index]))
                mask = self.__get_mask__(self.vars[i][j])
                #y = ma.masked_array(ds.variables[vars[i][j]][:], mask=mask)
                #print(vars[i][j])
                #y = ds.variables[self.vars[i][j]][:]
                #y = np.ravel(y[self.index,:])
                #y[y == -9999] = np.nan
                #TODO
                if len(ds.variables[self.vars[i][j]][:].shape) == 2:
                    y = ma.masked_array(ds.variables[self.vars[i][j]][self.index,:].ravel(), mask=mask[self.index,:].ravel())
                else:
                    y = ma.masked_array(ds.variables[self.vars[i][j]][self.index].ravel(), mask=mask[self.index].ravel())
                    #y = self.__set_mask__(y, vars[i][j])
                #self.y_data[i].append(np.ravel(ds.variables[vars[i][j]][self.index,:]))
                self.y_data[i].append(y)
                            
    def plot(self):
        for i in range(len(self.vars)):
            for j in range(len(self.vars[i])):                
                #ax = self.subplt[i]
                ax=self.axs[i]
                #TODO: weird behaviour; there shouldn't be a need to sort the data
                ix = np.argsort(self.x_data[i][j])
                x = self.x_data[i][j][ix]
                y = self.y_data[i][j][ix]
                ax.plot_date(x, y, '-', label=self.vars[i][j].lower())
                try:
                    yunits_str = ', '.join(set([(self.ds.variables[p].units).strip() for p in self.vars[i]]))
                    ax.set_ylabel(yunits_str)
                except:
                    pass

    def plot_formatter(self):
        ax=self.axs[0]
        #
        if ax.get_xlim()[1]-ax.get_xlim()[0] > 3600./86400.:
            minloc = mpl.dates.HourLocator()
            xformat = mpl.dates.DateFormatter('%H:%M')
        else:
            minloc = mpl.dates.MinuteLocator()
            xformat = mpl.dates.DateFormatter('%H:%M')
        #for ax in self.subplt:
        x_range=ax.get_xlim()[1]-ax.get_xlim()[0]
        _xlim=(ax.get_xlim()[0]-(x_range/100.)*3,
               ax.get_xlim()[1]+(x_range/100.)*3)
	ax.set_xlim(_xlim)
        for ax in self.axs:
            ax.grid(b='on')
            #TODO
            try:
                plt.setp(ax.get_xticklabels(), visible=False)
            except:
                pass         
            ax.xaxis.set_major_formatter(xformat)
            ax.xaxis.set_major_locator(minloc)            
            if ax.get_xticklabels().__len__() > 6:
                ax.xaxis.set_major_locator(MaxNLocator(6))                
            ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
            #http://stackoverflow.com/questions/4700614/how-to-put-the-legend-out-of-the-plot
            #box = ax.get_position()
            #ax.set_position([box.x0, box.y0, box.width * 0.90, box.height])
            #ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
            #ax.legend()                                          
            leg=ax.legend()
            leg.get_frame().set_alpha(0.5)
        plt.setp(ax.get_xticklabels(), visible=True)        
        ax.set_xlabel('utc')
    
    def create_filename(self):
        pass
    
    def get_figure(self):
        return(self.fig)

