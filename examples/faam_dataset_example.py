
import os
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from faampy.core.faam_data import FAAM_Dataset


ifile = os.path.join(os.path.expanduser('~'),
                     'gdrive',
                     'core_processing',
                     '2017',
                     'c013-may-17',
                     'core_faam_20170517_v004_r0_c013_1hz.nc')

# read in the FAAM netCDF
ds = FAAM_Dataset(ifile)
# get a pandas dataframe
df = ds.as_dataframe()
# strip of data when aircraft is on the ground
df = df[df.WOW_IND == 0]
# Plot a time series of TAT_ND_R
df.TAT_ND_R.plot()
plt.legend()
plt.grid()
# create 2nd y-axis
plt.twinx()
df.ALT_GIN.plot(color='firebrick')
plt.legend()

# The FAAM_Dataset has a coords attribute which contains the lon, lat, alt
# values for the flight. Those values can be used for plotting a flight track

# opening a new plotting window
plt.figure()
# Setting up the map
ax = plt.axes(projection=ccrs.PlateCarree())
ax.coastlines(resolution='10m')
# extract longitude and latitude from the coords
lon, lat, alt = zip(*ds.coords)
# plot the flight track
ax.plot(lon[::10], lat[::10], lw=2)
