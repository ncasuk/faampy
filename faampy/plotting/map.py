'''
Created on 7 Jul 2013

@author: axel
'''

import matplotlib.pyplot as plt

import numpy as np

import cartopy
import cartopy.crs as ccrs
from cartopy.feature import NaturalEarthFeature


class Map(object):

    def __init__(self):
        self.fig = plt.figure()
    
    def setup(self, ds, limit, step=15):      
        self.limit = limit        
        self.ft = {}
        if len(ds.variables['LON_GIN'][:].shape) == 2:
            self.ft['lon'] = ds.variables['LON_GIN'][:,0].ravel()[::step]
            self.ft['lat'] = ds.variables['LAT_GIN'][:,0].ravel()[::step]
        else:
            self.ft['lon'] = ds.variables['LON_GIN'][:].ravel()[::step]
            self.ft['lat'] = ds.variables['LAT_GIN'][:].ravel()[::step]
        self.ft['secs'] = ds.variables['Time'][:][::step]        
        self.urcrnrlon = np.ceil(np.max(self.ft['lon']))
        self.llcrnrlon = np.floor(np.min(self.ft['lon']))
        self.urcrnrlat = np.ceil(np.max(self.ft['lat']))
        self.llcrnrlat = np.floor(np.min(self.ft['lat']))
        self.lat0 = (self.urcrnrlat + self.llcrnrlat) / 2.0
        self.lon0 = (self.urcrnrlon + self.llcrnrlon) / 2.0

    def plot(self):
        proj = ccrs.TransverseMercator(central_longitude=self.lon0,
                                       central_latitude=self.lat0,
                                       false_easting=0.0,
                                       false_northing=0.0,
                                       scale_factor=1.0)
        proj = ccrs.PlateCarree()
        self.ax = plt.axes([0.1, 0.1, 0.8, 0.8],
                           projection=proj)
        
        self.ax.set_extent([self.llcrnrlon,
                            self.urcrnrlon,
                            self.llcrnrlat,
                            self.urcrnrlat])

        self.ax.gridlines()
        # https://ocefpaf.github.io/python4oceanographers/blog/2015/06/22/osm/
        #self.ax.add_feature(cartopy.feature.LAND)
        #self.ax.add_feature(cartopy.feature.OCEAN)
        coast = NaturalEarthFeature(category='physical', scale='10m',
                                    facecolor='none', name='coastline')
        self.ax.add_feature(coast, edgecolor='black', facecolor='lightgrey')
        self.ax.add_feature(cartopy.feature.BORDERS, linestyle=':')
        self.ax.add_feature(cartopy.feature.LAKES, alpha=0.5)
        self.ax.add_feature(cartopy.feature.RIVERS)

        #self.ax.set_extent([-20, 60, -40, 40])
        gl = self.ax.gridlines(crs=proj, draw_labels=True,
                  linewidth=1, color='grey', alpha=0.5, linestyle='--')
        gl.ylabels_right = False
        gl.xlabels_top = False
        x, y = self.ft['lon'], self.ft['lat']
        self.ax.plot(x, y, color='0.35', lw=1.4, transform=proj)
        ix = list(np.where((np.array(self.ft['secs']) > self.limit[0]) & (np.array(self.ft['secs']) < self.limit[1]))[0])
        self.ax.plot(x[min(ix):max(ix)], y[min(ix):max(ix)],
                     color='firebrick', lw=3.5, transform=proj)
        self.ax.plot(x[min(ix)], y[min(ix)],
                     'o', color='dodgerblue', markeredgecolor='black', transform=proj)

    def get_figure(self):
        return self.fig


