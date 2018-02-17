'''
Created on 13 Jan 2012

@author: axel
'''

import netCDF4
import datetime
from matplotlib.dates import date2num, num2date 

import matplotlib.pyplot as plt
import numpy as np
import os

from pylab import *
rcParams['figure.figsize'] = 10, 10
    

def get_index( data, time_start, time_end ):
    t = data.variables['Time'][:]
    time_start_secs = float( time_start[0:2] ) * 3600. + \
                      float( time_start[2:4] ) * 60. + \
                      float( time_start[4:6] )
    time_end_secs = float( time_end[0:2] ) * 3600. + \
                    float( time_end[2:4] ) * 60. + \
                    float( time_end[4:6] )
    ix = np.where( (t > time_start_secs ) & ( t < time_end_secs ) )
    return ix


def create_plot_title( mano, fid, id, time_start, time_end ):
    plt_title = '%s %s#%02i %s-%s' % ( fid, str.capitalize(mano), id, time_start, time_end )
    return plt_title


def create_img_filename( mano, plt_type, fid, id, time_start, time_end ):
    img_name = '%s_%s_%02i_%s_%s_%s' % ( fid, mano, id, plt_type, time_start, time_end )
    return img_name
    
   
class Turbu_qa( object ):
    
    def __init__(self, data, mano, fid, id, time_start, time_end ):
        self.Data = data
        self.fid = fid
        self.id = id
        self.mano = mano
        self.time_start = time_start
        self.time_end = time_end
        self.PlotData = {}
    
    def __get_index__( self ):         
        return get_index( self.Data, self.time_start, self.time_end )
    
    def __get_lim__(self, dat, step=None ):
        if not step:
            step = 5
        
        try:
            dummy = dat
            dummy = dummy[ np.isfinite( dummy ) ]
            dummy.sort()
            min = np.floor( dummy[20] / float( step ) ) * step
            max = np.ceil( dummy[-20] / float( step ) ) * step
            return ( min, max )
        except:
            return
    
    def __tidy__(self, data, limits=None ):
        if not limits:
            limits = (-9000, 9000)
        flag = np.where( (data <= limits[0]) | ( data >= limits[1] ))[0]
        flag = list( flag )
        if flag:
            data[flag] = np.NAN
        return data
        
    
    def get_data( self ):
        ix = list( self.__get_index__()[0] )
        self.ix = np.array( range( len(ix) * 32 ))
        #self.PlotData[ 'Time' ]  = self.Data.variables['Time'][ix,] / 86400. + date2num( datetime.datetime.strptime( self.Data.Data_Date, '%Y%m%d' ))
        
        tmp1 = self.Data.variables['Time'][ix,] # + date2num( datetime.datetime.strptime( self.Data.Data_Date, '%Y%m%d' ))
        tmp2 = (np.array( range( len( self.ix ))) * 1./32. + np.min( tmp1 )) / 86400.
        try:
            self.PlotData[ 'Time' ] = tmp2 + date2num( datetime.datetime.strptime( self.Data.Data_Date, '%Y%m%d' ))
        except:
            self.PlotData[ 'Time' ] = tmp2 + date2num( datetime.datetime.strptime( str.strip(self.Data.Data_Date), '%d-%b-%Y' ))            
        
        if 'TAS' in self.Data.variables.keys():
            try:
                self.PlotData[ 'TAS' ] = self.__tidy__( self.Data.variables[ 'TAS' ][ix,:].ravel(), limits = ( 0, 250 ))
            except:
                pass
        elif 'PARA0779' in self.Data.variables.keys():
            try:
                self.PlotData[ 'TAS' ] = self.__tidy__( self.Data.variables[ 'PARA0779' ][ix,:].ravel(), limits = ( 0, 250 ))
            except:
                pass
        
        if 'TAS_RVSM' in self.Data.variables.keys():
            self.PlotData[ 'TAS_RVSM' ] = self.__tidy__( self.Data.variables[ 'TAS_RVSM' ][ix,:].ravel(), limits = ( 0, 250 ))
        elif 'PARA0517' in self.Data.variables.keys():
            self.PlotData[ 'TAS_RVSM' ] = self.__tidy__( self.Data.variables[ 'PARA0517' ][ix,:].ravel(), limits = ( 0, 250 ))        
        
        if 'U_C' in self.Data.variables.keys():
            self.PlotData[ 'U' ] = self.__tidy__( self.Data.variables[ 'U_C' ][ix,:].ravel(), limits = ( -100, 100 ))
        elif 'PARA0715' in self.Data.variables.keys():
            self.PlotData[ 'U' ] = self.__tidy__( self.Data.variables[ 'PARA0715' ][ix,:].ravel(), limits = ( -100, 100 ))
        
        if 'V_C' in self.Data.variables.keys():
            self.PlotData[ 'V' ] = self.__tidy__( self.Data.variables[ 'V_C' ][ix,:].ravel(), limits = ( -100, 100 ))
        elif 'PARA0714' in self.Data.variables.keys():            
            self.PlotData[ 'V' ] = self.__tidy__( self.Data.variables[ 'PARA0714' ][ix,:].ravel(), limits = ( -100, 100 ))

        if 'W_C' in self.Data.variables.keys():            
            self.PlotData[ 'W' ] = self.__tidy__( self.Data.variables[ 'W_C' ][ix,:].ravel(), limits = ( -10, 10 ))
        elif 'PARA0716' in self.Data.variables.keys():
            self.PlotData[ 'W' ] = self.__tidy__( self.Data.variables[ 'PARA0716' ][ix,:].ravel(), limits = ( -10, 10 ))

        if 'W_C' in self.Data.variables.keys():            
            self.PlotData[ 'W' ] = self.__tidy__( self.Data.variables[ 'W_C' ][ix,:].ravel(), limits = ( -10, 10 ))
        elif 'PARA0716' in self.Data.variables.keys():
            self.PlotData[ 'W' ] = self.__tidy__( self.Data.variables[ 'PARA0716' ][ix,:].ravel(), limits = ( -10, 10 ))

        if 'W_C' in self.Data.variables.keys():            
            self.PlotData[ 'W' ] = self.__tidy__( self.Data.variables[ 'W_C' ][ix,:].ravel(), limits = ( -10, 10 ))
        elif 'PARA0716' in self.Data.variables.keys():
            self.PlotData[ 'W' ] = self.__tidy__( self.Data.variables[ 'PARA0716' ][ix,:].ravel(), limits = ( -10, 10 ))

        if 'W_C' in self.Data.variables.keys():            
            self.PlotData[ 'W' ] = self.__tidy__( self.Data.variables[ 'W_C' ][ix,:].ravel(), limits = ( -10, 10 ))
        elif 'PARA0716' in self.Data.variables.keys():
            self.PlotData[ 'W' ] = self.__tidy__( self.Data.variables[ 'PARA0716' ][ix,:].ravel(), limits = ( -10, 10 ))

        if 'VELN_GIN' in self.Data.variables.keys():            
            self.PlotData[ 'VELN_GIN' ] = self.__tidy__( self.Data.variables[ 'VELN_GIN' ][ix,:].ravel(), limits = ( -200, 200 ))
        elif 'PARA0613' in self.Data.variables.keys():
            self.PlotData[ 'VELN_GIN' ] = self.__tidy__( self.Data.variables[ 'PARA0613' ][ix,:].ravel(), limits = ( -200, 200 ))
        elif 'PARA0735' in self.Data.variables.keys():
            self.PlotData[ 'VELN_GIN' ] = self.__tidy__( self.Data.variables[ 'PARA0735' ][ix,:].ravel(), limits = ( -200, 200 ))

        if 'VELE_GIN' in self.Data.variables.keys():            
            self.PlotData[ 'VELE_GIN' ] = self.__tidy__( self.Data.variables[ 'VELE_GIN' ][ix,:].ravel(), limits = ( -200, 200 ))
        elif 'PARA0614' in self.Data.variables.keys():
            self.PlotData[ 'VELE_GIN' ] = self.__tidy__( self.Data.variables[ 'PARA0614' ][ix,:].ravel(), limits = ( -200, 200 ))
        elif 'PARA0736' in self.Data.variables.keys():
            self.PlotData[ 'VELE_GIN' ] = self.__tidy__( self.Data.variables[ 'PARA0736' ][ix,:].ravel(), limits = ( -200, 200 ))

        if 'TAT_DI_R' in self.Data.variables.keys():            
            self.PlotData[ 'TAT_DI_R' ] = self.__tidy__( self.Data.variables[ 'TAT_DI_R' ][ix,:].ravel(), limits = ( 0, 340 ))
        elif 'PARA0520' in self.Data.variables.keys():
            self.PlotData[ 'TAT_DI_R' ] = self.__tidy__( self.Data.variables[ 'PARA0520' ][ix,:].ravel(), limits = ( 0, 340 ))
        
        if 'HDG_GIN' in self.Data.variables.keys():
            self.PlotData[ 'HDG_GIN' ] = self.__tidy__( self.Data.variables['HDG_GIN'][ix,:].ravel(), limits=(0,360))
        elif 'PARA0618' in self.Data.variables.keys():
            self.PlotData[ 'HDG_GIN' ] = self.__tidy__( self.Data.variables['PARA0618'][ix,:].ravel(), limits=(0,360))
        elif 'PARA0562' in self.Data.variables.keys():
            self.PlotData[ 'HDG_GIN' ] = self.__tidy__( self.Data.variables['PARA0562'][ix,:].ravel(), limits=(0,360))
        
                                    
        self.PlotData[ 'WDIR' ] = self.__tidy__( calc_wdir( self.PlotData[ 'U' ], self.PlotData[ 'V' ] ), limits=(0,360))

            
        #self.PlotData[ 'U_alter'], self.PlotData[ 'V_alter'] = calc_bulk_wspd( self.Data, ix )        
        self.PlotData[ 'U_alter'], self.PlotData[ 'V_alter'] = calc_bulk_wspd( self.PlotData['TAS_RVSM'][:].ravel(),
                                                                               self.PlotData['HDG_GIN'][:].ravel(),
                                                                               self.PlotData['VELN_GIN'][:].ravel(),
                                                                               self.PlotData['VELE_GIN'][:].ravel(),
                                                                               self.PlotData['TAT_DI_R'][:].ravel() )


    def plot_timeseries(self):
        
        fig = plt.figure()        
        plt.plot( self.PlotData['HDG_GIN'], self.PlotData['WDIR'], 'o' )
        plt.title( create_plot_title(self.mano, self.fid, self.id, self.time_start, self.time_end )) 
        #plt.xlim( [1,359] )
        #plt.ylim( [-75, -40] )
        plt.xlabel( 'HDG_GIN (degree)' )
        plt.ylabel( 'WDIR (degree)' )
        if self.mano == 'orbit':
            plt.xlim( [1,359] )
            plt.ylim( self.__get_lim__( self.PlotData['WDIR']) )
        plt.savefig( os.path.join( self.OUTPATH, create_img_filename( self.mano, 'xyplot', self.fid, self.id, self.time_start, self.time_end)))
        plt.clf()

    def plot_histogram(self):
        bins = np.array( range(360) ) + 0.5
        cnts = np.histogram( self.PlotData['WDIR'], range(361) )[0]
        freq = cnts.astype(float) / float( len(self.PlotData['WDIR'] )) * 100.
        
        fig = plt.figure()
        ax = fig.add_subplot( 111 )
        ax.bar( bins - 0.5, freq, width=1 )
        plt.title( create_plot_title(self.mano, self.fid, self.id, self.time_start, self.time_end ))
        plt.xlabel( 'WDIR' )
        plt.ylabel( 'frequency (%)' )
        if self.mano == 'orbit':
            plt.xlim( self.__get_lim__( self.PlotData['WDIR']) )
        plt.savefig( os.path.join( self.OUTPATH, create_img_filename( self.mano, 'histogram', self.fid, self.id, self.time_start, self.time_end )))
        plt.clf()

    
    def plot_overview( self ):
        fig = plt.figure()    
        # see: http://matplotlib.sourceforge.net/examples/pylab_examples/subplots_demo.html        
        
        minuteloc = mpl.dates.MinuteLocator()
        minuteformat = mpl.dates.DateFormatter( '%H:%M' )
               
        ax0 = fig.add_subplot( 511 )        
        plt.title( create_plot_title(self.mano, self.fid, self.id, self.time_start, self.time_end ))
        #plt.plot( self.ix, self.PlotData['HDG_GIN'] )
        plt.plot_date( self.PlotData['Time'], self.PlotData['HDG_GIN'], '-' )
        plt.setp( ax0.get_xticklabels(), visible=False )
        plt.ylabel( 'hdg (deg)' )        
        if self.mano == 'orbit':
            plt.ylim( self.__get_lim__( self.PlotData['HDG_GIN']) )
        ax0.xaxis.set_major_locator( minuteloc )
        ax0.xaxis.set_major_formatter( minuteformat )
        
                
        ax1 = fig.add_subplot( 512 )                        
        #plt.plot( self.ix, self.PlotData['WDIR'] )
        plt.plot_date( self.PlotData['Time'], self.PlotData['WDIR'], '-' )
        plt.setp( ax1.get_xticklabels(), visible=False )
        plt.ylabel( 'wdir (deg)' )        
        if self.mano == 'orbit':
            plt.ylim( self.__get_lim__( self.PlotData['WDIR']) )
        ax1.xaxis.set_major_locator( minuteloc )
        ax1.xaxis.set_major_formatter( minuteformat )
        
        ax2 = fig.add_subplot( 513, sharex=ax1 )
        #plt.plot( self.ix, self.PlotData['U'] )
        plt.plot_date( self.PlotData['Time'], self.PlotData['U'], '-' )
        plt.setp( ax2.get_xticklabels(), visible=False )
        plt.ylabel( 'u (ms-1)' )
        if self.mano == 'orbit':
            plt.ylim( self.__get_lim__( self.PlotData['U'], step=2 ))
        ax2.xaxis.set_major_locator( minuteloc )
        ax2.xaxis.set_major_formatter( minuteformat )
                
        ax3 = fig.add_subplot( 514, sharex=ax1 )
        #plt.plot( self.ix, self.PlotData['V'] )
        plt.plot_date( self.PlotData['Time'], self.PlotData['V'], '-' )
        plt.setp( ax3.get_xticklabels(), visible=False )
        plt.ylabel( 'v (ms-1)' )
        if self.mano == 'orbit':
            plt.ylim( self.__get_lim__( self.PlotData['V'], step=2 ))        
        ax3.xaxis.set_major_locator( minuteloc )
        ax3.xaxis.set_major_formatter( minuteformat )
        
        ax4 = fig.add_subplot( 515, sharex=ax1 )
        #plt.plot( self.ix, self.PlotData['W'] )            
        plt.plot_date( self.PlotData['Time'], self.PlotData['W'], '-' )
        plt.ylabel( 'w (ms-1)' )
        if self.mano == 'orbit':
            plt.ylim( self.__get_lim__( self.PlotData['W'], step=1 ))        
        ax4.xaxis.set_major_locator( minuteloc )
        ax4.xaxis.set_major_formatter( minuteformat )
        #fig.autofmt_xdate()
        
        plt.savefig( os.path.join( self.OUTPATH, create_img_filename( self.mano, 'overview', self.fid, self.id, self.time_start, self.time_end )))
        plt.clf()


    def plot_scatter( self, x, y, xlabel, ylabel, name ):
        #import numpy as np
        #import matplotlib.pyplot as plt
        from matplotlib.ticker import NullFormatter
        from matplotlib.lines import Line2D
        nullfmt = NullFormatter()         # no labels
        
        # definitions for the axes
        left, width = 0.1, 0.60
        bottom, height = 0.1, 0.60
        bottom_h = left_h = left + width + 0.02
        
        rect_scatter = [left, bottom, width, height]
        rect_histx = [left, bottom_h, width, 0.2]
        rect_histy = [left_h, bottom, 0.2, height]
            
        # start with a rectangular Figure
        plt.figure(1, figsize=(10,10))

        axScatter = plt.axes( rect_scatter )
        axScatter.set_xlabel( xlabel )
        axScatter.set_ylabel( ylabel )
        axHistx = plt.axes( rect_histx )
        axHistx.set_title( create_plot_title(self.mano, self.fid, self.id, self.time_start, self.time_end ))
        axHisty = plt.axes( rect_histy )
        
        # no labels
        axHistx.xaxis.set_major_formatter(nullfmt)
        axHisty.yaxis.set_major_formatter(nullfmt)
        
        # the scatter plot:
        axScatter.scatter( x, y )        
        axScatter.grid()
    
        # now determine nice limits by hand:
        binwidth = 0.25
        if self.mano == 'orbit':
            xymin = np.nanmin( [ np.nanmin(self.__get_lim__(x, 1)), np.nanmin(self.__get_lim__(y, 1)) ]) 
            xymax = np.nanmax( [ np.nanmax(self.__get_lim__(x, 1)), np.nanmax(self.__get_lim__(y, 1)) ])
        else:
            xymin = np.nanmin( [np.nanmin(x), np.nanmin(y) ]) 
            xymax = np.nanmax( [np.nanmax(x), np.nanmax(y) ])
        
        lim = ( np.floor(xymin), np.ceil( xymax ))
        #print( lim )
        axScatter.set_xlim( lim )
        axScatter.set_ylim( lim ) 
        l = Line2D([-1000,1000],[-1000,1000], color='0.8', linewidth=2 )    
        #l = Line2D([lim[0], lim[1]], [lim[1], lim[1]] )                                    
        axScatter.add_line(l)                                             
         
        bins = np.arange( lim[0], lim[1] + binwidth, binwidth)
        axHistx.hist(x, normed=True, bins=bins)
        axHisty.hist(y, normed=True, bins=bins, orientation='horizontal')
        
        axHistx.set_xlim( axScatter.get_xlim() )
        axHistx.set_ylim( (0, np.nanmax( [axHistx.get_ylim()[1], axHisty.get_xlim()[1]] )))
        axHisty.set_ylim( axScatter.get_ylim() )
        axHisty.set_xlim( (0, np.nanmax( [axHistx.get_ylim()[1], axHisty.get_xlim()[1]] )))
    
        plt.savefig( os.path.join( self.OUTPATH, create_img_filename( self.mano, name, self.fid, self.id, self.time_start, self.time_end )))
        plt.clf()
            
    
if __name__ == "__main__":
    pass     
    
        



