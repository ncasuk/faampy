
b968 - 30/06/2016 - MONSOON - LST survey
----------------------------------------

For this example we compare the brightness temperature measurements from
the Heimann instrument on the aircraft with land surface temperature
data from the MODIS instrument.

.. code:: ipython2

    %matplotlib inline
    
    import matplotlib.pyplot as plt
    import datetime
    import os
    import numpy as np
    
    ROOT_DATA_PATH = os.path.join(os.path.expanduser('~'), 'faampy_data', 'cis_workshop', 'b968')
    
    os.chdir(ROOT_DATA_PATH)

Converting the MODIS hdf into netCDF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The original data were downloaded in hdf format. gdal brings als the
tools to convert it into a netCDF, that cis can work with. The
conversion has been done and the below cell is only kept as a reference.

.. code:: ipython2

    # Show information about the hdf content
    # gdalinfo MOD11A1.A2016182.h24v06.006.2016241041630.hdf
    #
    # extract subset from hdf5 file
    # We got the exact name of the subset from the gdalinfo command above
    # see: http://osgeo-org.1560.x6.nabble.com/Extract-subdataset-from-netCDF-in-a-given-directory-td5161167.html
    # gdal_translate -of netCDF HDF4_EOS:EOS_GRID:"MOD11A1.A2016182.h24v06.006.2016241041630.hdf":MODIS_Grid_Daily_1km_LST:LST_Day_1km MOD11A1.A2016182.h24v06.006.2016241041630.lst.nc
    #
    # Convert it to WGS84 reference system with longitude and latitude
    # gdalwarp -of netCDF -t_srs EPSG:4326 MOD11A1.A2016182.h24v06.006.2016241041630.lst.nc MOD11A1.A2016182.h24v06.006.2016241041630.4326.lst.nc
    #
    # have a look what is in the file
    # ncdump -h MOD11A1.A2016182.h24v06.006.2016241041630.4326.lst.nc
    #
    # Rename the "Band1" variable to "lst"
    # ncrename -v Band1,lst MOD11A1.A2016182.h24v06.006.2016241041630.4326.lst.nc

.. code:: ipython2

    import cis
    modis = cis.read_data(os.path.join(ROOT_DATA_PATH, 'MOD11A1.A2016182.h24v06.006.2016241041630.4326.lst.nc'), 'lst')
    
    # scaling of the land surface temperature data
    # https://gis.stackexchange.com/questions/72524/how-do-i-convert-the-lst-values-on-the-modis-lst-image-to-degree-celsius
    modis.data *= 0.02
    
    ax = modis.plot(label='MODIS lst (K)')
    # add the bluemarble background
    ax.bluemarble()


.. parsed-literal::

    /usr/local/lib/python2.7/dist-packages/Iris-1.12.0.dev0-py2.7.egg/iris/fileformats/cf.py:76: FutureWarning: Conversion of the second argument of issubdtype from `str` to `str` is deprecated. In future, it will be treated as `np.string_ == np.dtype(str).type`.
      return ((six.PY2 and np.issubdtype(var.dtype, np.str)) or
    /usr/local/lib/python2.7/dist-packages/Iris-1.12.0.dev0-py2.7.egg/iris/fileformats/_pyke_rules/compiled_krb/fc_rules_cf_fc.py:1814: FutureWarning: Conversion of the second argument of issubdtype from `str` to `str` is deprecated. In future, it will be treated as `np.string_ == np.dtype(str).type`.
      if np.issubdtype(cf_var.dtype, np.str):
    /usr/local/lib/python2.7/dist-packages/Iris-1.12.0.dev0-py2.7.egg/iris/coords.py:802: UserWarning: Coordinate u'longitude' is not bounded, guessing contiguous bounds.
      'contiguous bounds.'.format(self.name()))
    /usr/local/lib/python2.7/dist-packages/Iris-1.12.0.dev0-py2.7.egg/iris/coords.py:802: UserWarning: Coordinate u'latitude' is not bounded, guessing contiguous bounds.
      'contiguous bounds.'.format(self.name()))



.. image:: /cis_workshop/cis_example_b968_files/cis_example_b968_6_1.png


Reading in brightness temperature from aircraft
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reading the brightness temperature from the Heimann instrument on the
FAAM aircraft

.. code:: ipython2

    ara_bt = cis.read_data(os.path.join(ROOT_DATA_PATH, 'core_faam_20160630_v004_r0_b968_1hz_editted.nc'), 'BTHEIM_U', product='NCAR_NetCDF_RAF')

Some manual tidying up is necessary.

.. code:: ipython2

    ara_bt.data[ara_bt.coords()[1].data == 0] = np.nan
    ara_bt.data[ara_bt.data < 0] = np.nan


.. parsed-literal::

    -c:2: RuntimeWarning: invalid value encountered in less


.. code:: ipython2

    ara_bt.plot()


.. parsed-literal::

    /usr/local/lib/python2.7/dist-packages/numpy/core/_methods.py:29: RuntimeWarning: invalid value encountered in reduce
      return umr_minimum(a, axis, None, out, keepdims)
    /usr/local/lib/python2.7/dist-packages/numpy/core/_methods.py:26: RuntimeWarning: invalid value encountered in reduce
      return umr_maximum(a, axis, None, out, keepdims)




.. parsed-literal::

    <cartopy.mpl.geoaxes.GeoAxesSubplot at 0x7f788d712190>




.. image:: /cis_workshop/cis_example_b968_files/cis_example_b968_12_2.png


.. code:: ipython2

    # reading in the gin altitude
    ara_alt = cis.read_data(os.path.join(ROOT_DATA_PATH, 'core_faam_20160630_v004_r0_b968_1hz_editted.nc'), 'ALT_GIN', product='NCAR_NetCDF_RAF')
    
    ara_alt.plot(xaxis='time')




.. parsed-literal::

    <matplotlib.axes._subplots.AxesSubplot at 0x7f78c35459d0>




.. image:: /cis_workshop/cis_example_b968_files/cis_example_b968_13_1.png


For the further analysis we are interested in the low level leg which
starts at about 05:25Z and ends at 07:00Z. Clipping the brightness data
using the subset method.

.. code:: ipython2

    # Defining start and end time
    stime = datetime.datetime.strptime('2016-06-30T05:25', '%Y-%m-%dT%H:%M')
    etime = datetime.datetime.strptime('2016-06-30T07:00', '%Y-%m-%dT%H:%M')
    
    # create a subset using the start and end time
    ara_bt = ara_bt.subset(t=[stime, etime])
    ara_bt.plot()




.. parsed-literal::

    <cartopy.mpl.geoaxes.GeoAxesSubplot at 0x7f78bd73e190>




.. image:: /cis_workshop/cis_example_b968_files/cis_example_b968_15_1.png


.. code:: ipython2

    import cartopy.crs as ccrs
    fig, ax = plt.subplots(figsize=(12, 8), subplot_kw=dict(projection=ccrs.PlateCarree()))
    
    modis.plot(ax=ax, label='MODIS lst (K)', cmap='Reds', vmin=300, vmax=330, cbarorient='vertical')
    ara_bt.plot(ax=ax, cmap='Greens', vmin=300, vmax=330, cbarorient='vertical')
    ax.bluemarble()



.. image:: /cis_workshop/cis_example_b968_files/cis_example_b968_16_0.png


We can create nice overlays to get a feel for the location and sampling,
but if we want to pergorm a quantitive comparison we'll need to
collocate the data

.. code:: ipython2

    # collocate brightness temperature with MODIS. Note this time we're aggregating the aircraft data
    ara_bt_col = ara_bt.collocated_onto(modis, kernel='mean')
    print(ara_bt_col[0])


.. parsed-literal::

    WARNING:root:Creating guessed bounds as none exist in file
    WARNING:root:Creating guessed bounds as none exist in file
    WARNING:root:Standard name 'None' not CF-compliant, this standard name will not be used in the output file.


.. parsed-literal::

    Uncorrected brightness temperature from the Heimann radiometer / (degK) (latitude: 1505; longitude: 2555)
         Dimension coordinates:
              latitude                                                               x                -
              longitude                                                              -                x
         Attributes:
              history: 2018-02-23T14:09:18Z Collocated onto sampling from: ['/home/axel/faampy_data/cis_workshop/b968/MOD11A1.A2016182.h24v06.006.2016241041630.4326.lst.nc']...


.. code:: ipython2

    # copy the mask over from the brightness temperature - because of the way we did the collocation
    modis.data.mask |= ara_bt_col[0].data.mask
    
    # aggregate over the latitude dimensions
    modis2 = modis.collapsed('latitude', how='mean')
    ara_bt_col_meridional = ara_bt_col.collapsed('latitude', how='mean')
    
    # plot MODIS and FAAM data against longitude for comparison
    ax = modis2.plot(label='MODIS')
    ara_bt_col_meridional.plot(ax=ax, label='FAAM')
    
    ax.grid(True)


.. parsed-literal::

    /usr/local/lib/python2.7/dist-packages/Iris-1.12.0.dev0-py2.7.egg/iris/analysis/cartography.py:368: UserWarning: Assuming spherical earth from ellipsoid.
      warnings.warn("Assuming spherical earth from ellipsoid.")
    /usr/local/lib/python2.7/dist-packages/Iris-1.12.0.dev0-py2.7.egg/iris/coords.py:964: FutureWarning: Conversion of the second argument of issubdtype from `str` to `str` is deprecated. In future, it will be treated as `np.string_ == np.dtype(str).type`.
      if np.issubdtype(self.dtype, np.str):



.. image:: /cis_workshop/cis_example_b968_files/cis_example_b968_19_1.png


.. code:: ipython2

    # Append the modis data onto our collocated data so we can plot them together easily
    ara_bt_col.append(modis)

.. code:: ipython2

    ara_bt_col.plot(how='histogram2d')




.. parsed-literal::

    <matplotlib.axes._subplots.AxesSubplot at 0x7f788c5a0690>




.. image:: /cis_workshop/cis_example_b968_files/cis_example_b968_21_1.png

