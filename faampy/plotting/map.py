'''
Created on 7 Jul 2013

@author: axel
'''

import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import scipy
import numpy as np

#import faampy.mapping.FlightTrack


class Map(object):

    def __init__(self):
        self.fig = plt.figure()
    
    def setup(self, ds, limit):      
        self.limit = limit 
        #self.ft = faampy.mapping.FlightTrack.FlightTrack()
        #self.ft.set_rawlatlonalt_from_netcdf(ds)
        
        step = 15
        self.ft = {}
        if len(ds.variables['LON_GIN'][:].shape) == 2:
            self.ft['lon'] = ds.variables['LON_GIN'][:,0].ravel()[::step]
            self.ft['lat'] = ds.variables['LAT_GIN'][:,0].ravel()[::step]
        else:
            self.ft['lon'] = ds.variables['LON_GIN'][:].ravel()[::step]
            self.ft['lat'] = ds.variables['LAT_GIN'][:].ravel()[::step]
        #self.ft.secs = [(x - self.ft.BaseTime).seconds for x in self.ft.time]
        self.ft['secs'] = ds.variables['Time'][:][::step]

        
        self.urcrnrlon = np.ceil(np.max(self.ft['lon']))
        self.llcrnrlon = np.floor(np.min(self.ft['lon']))
        self.urcrnrlat = np.ceil(np.max(self.ft['lat']))
        self.llcrnrlat = np.floor(np.min(self.ft['lat']))
        self.lat0 = (self.urcrnrlat + self.llcrnrlat) / 2.0
        self.lon0 = (self.urcrnrlon + self.llcrnrlon) / 2.0

    def plot(self):
        self.m = Basemap(llcrnrlon=self.llcrnrlon, 
                         llcrnrlat=self.llcrnrlat,
                         urcrnrlon=self.urcrnrlon,
                         urcrnrlat=self.urcrnrlat,
                         resolution='h',
                         projection='merc',
                         lat_0=self.lat0,
                         lon_0=self.lon0)     
        self.m.drawcoastlines()    
        # draw parallels and meridians.
        self.m.drawparallels(scipy.arange(-90.,91.,1.), labels=[1,1,0,0])
        self.m.drawmeridians(scipy.arange(-180.,181.,1.), labels=[0,0,0,1])
        self.m.drawcountries()
        self.m.drawmapboundary()     
        # TODO: change the colors 
        self.m.fillcontinents(color='coral',lake_color='aqua')
        x, y = self.m(self.ft['lon'], self.ft['lat'])
        self.m.plot(x, y, color='0.55', lw=1.4)
        ix = list(np.where((np.array(self.ft['secs']) > self.limit[0]) & (np.array(self.ft['secs']) < self.limit[1]))[0])
        self.m.plot(x[min(ix):max(ix)], y[min(ix):max(ix)], 'r', lw=3.5)
        self.m.plot(x[min(ix)], y[min(ix)], 'ko')

    def get_figure(self):
        return self.fig
