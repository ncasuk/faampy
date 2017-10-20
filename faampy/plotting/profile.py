'''
Created on 15 May 2013

@author: axel
'''

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
import sys
import scipy

from matplotlib.ticker import MaxNLocator, ScalarFormatter

import faampy.core.utils

params = {'legend.fontsize': 10,}
plt.rcParams.update(params)


class Profile(object):

    def __init__(self, *args):
        """

        """
        self.NO_DATA = None
        self.fig = None
        self.x_data = []
        self.y_data = []


    def __get_mask__(self, parname):
        if not parname+'_FLAG' in self.ds.variables.keys():
            flag_data = np.zeros(self.ds.variables[parname].shape).astype(bool)
        else:
            flag_data = self.ds.variables[parname+'_FLAG'][:]
        mask = np.ones(flag_data.shape).astype(bool)
        for f in self.flag:
            mask[flag_data == f] = False
        mask[self.ds.variables[parname][:] == -9999] = True
        return mask

    def setup(self, ds, vars, *args):
        self.ds = ds
        self.vars = list(vars)

        self.index = range(self.ds.variables['Time'].shape[0])

        #check that all the pars exist in netcdf file
        #is_var = lambda var: var.upper() in self.ds.variables.keys()
        is_var = lambda var: var.upper() in [i.upper() for i in self.ds.variables.keys()]
        pars = []
        for l in self.vars:
            pars.append([item for item in l if is_var(item)])
            diff = set(l).difference(pars[-1])
            if diff:
                sys.stdout.write('Skip %s because it is not in dataset.\n' % (','.join(diff)))
        if not [item for sublist in pars for item in sublist]:
            self.NO_DATA = True
            return 0
        else:
            self.NO_DATA = False
        self.vars = pars


        try:
            self.index = faampy.core.utils.data_filter(self.ds, args[0])
        except:
            pass
        self.index=sorted(self.index)
        try:
            self.flag = args[1]
        except:
            self.flag = [0,1,2,3]

        #for i in range(len(self.vars)):
        #    self.subplt.append(self.fig.add_subplot(1, len(self.vars), 1+i))
        self.fig, self.axs=plt.subplots(ncols=len(self.vars), sharey=True)
        if len(self.vars) == 1:
            self.axs=np.array([self.axs,])

        for i in range(len(self.vars)):
            self.x_data.append([])
            self.y_data.append([])
            for j in range(len(self.vars[i])):
                if len(ds.variables[self.vars[i][j]][:].shape) == 1:
                    self.x_data[i].append(ds.variables['ALT_GIN'][self.index].ravel())
                    mask = self.__get_mask__(self.vars[i][j])
                    y = ma.masked_array(ds.variables[self.vars[i][j]][self.index].ravel(), mask=mask[self.index].ravel())
                else:
                    (rows, cols) = ds.variables[self.vars[i][j]][:].shape
                    #print(self.vars[i][j], cols)
                    if cols > 32:
                        self.x_data[i].append(ds.variables['ALT_GIN'][self.index,:].ravel())
                        mask = self.__get_mask__(self.vars[i][j])
                        #y = ds.variables[self.vars[i][j]][:,0:64:2]
                        y = ma.masked_array(ds.variables[self.vars[i][j]][self.index,0:64:2].ravel(), mask=mask[self.index,0:64:2].ravel())
                    else:
                        #self.x_data[i].append(ds.variables['ALT_GIN'][self.index,0:32:32/cols].ravel())
                        #self.x_data[i].append(ds.variables['ALT_GIN'][self.index,0:32:32/cols].ravel())
                        _x = ds.variables['ALT_GIN'][self.index, :]
                        _x = scipy.misc.imresize(_x, (len(self.index), cols))[:].ravel()
                        self.x_data[i].append(_x)
                        mask = self.__get_mask__(self.vars[i][j])
                        y = ma.masked_array(ds.variables[self.vars[i][j]][self.index,:].ravel(), mask=mask[self.index,:].ravel())
                        
                    #mask = self.__get_mask__(ds, vars[i][j])
                #y = ma.masked_array(ds.variables[vars[i][j]], mask=mask)

                #y = np.ravel(y[self.index,:])
                #y[y == -9999] = np.nan
                #TODO
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
                ax.plot(y, x, '-', label=self.vars[i][j].lower())
            try:
                xunits_str = ', '.join([(self.ds.variables[p].units).strip() for p in self.vars[i]])
                ax.set_xlabel(xunits_str)
            except:
                pass

    def plot_formatter(self):
        #for ax in self.subplt:
        ax=self.axs[0]
        y_range=ax.get_ylim()[1]-ax.get_ylim()[0]
        _ylim=(ax.get_ylim()[0]-(y_range/100.)*3,
               ax.get_ylim()[1]+(y_range/100.)*3)
        ax.set_ylim(_ylim)
        for ax in self.axs:
            ax.grid(b='on')
            plt.setp(ax.get_yticklabels(), visible=False)
            #http://stackoverflow.com/questions/4700614/how-to-put-the-legend-out-of-the-plot
            #box = ax.get_position()
            #ax.set_position([box.x0, box.y0 + box.height * 0.2, box.width, box.height * 0.8])
            #ax.set_position([box.x0, box.y0, box.width, box.height * 0.8])
            #ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12))
            leg=ax.legend()
            leg.get_frame().set_alpha(0.5)
            if ax.get_xticklabels().__len__() > 5:
                ax.xaxis.set_major_locator(MaxNLocator(5))
                ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
                #set y-axis lower limit to zero
                cur_ylim = ax.get_ylim()
                if cur_ylim[0] < 0:
                    ax.set_ylim((0, cur_ylim[1]))

        plt.setp((self.axs[0].get_yticklabels()), visible=True)
        (self.axs[0]).set_ylabel('alt (m)')

    def get_figure(self):
        return(self.fig)

