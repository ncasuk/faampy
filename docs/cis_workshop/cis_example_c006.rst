
c006 - 01/03/2017 - MOYA - Chemistry outflow on the West Coast of Africa
------------------------------------------------------------------------

Flight c006 was part of the MOYA (Methane Observations and Yearly
Assessments) campaign. On this sortie a transect was investigated by
flying stacked runs over the Ocean on the West Coast of Africa. The
flight track (see further down) shows that the aircraft spent most of
the time between 13 degree and 12 degree North at the 16 degree
meridian.

.. code:: ipython2

    %matplotlib inline
    
    import cis
    import datetime
    import os
    
    ROOT_DATA_PATH = os.path.join(os.path.expanduser('~'), 'faampy_data', 'cis_workshop', 'c006')
    
    os.chdir(ROOT_DATA_PATH)

Merging CAMS data files into a single NetCDF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The data merging has already been done. The below code is left only for
reference in case anybody wants to do it themself.

iris can do the merge for us. The only pitfall is that iris refuses to
concatenate datasets with differing history attributes. Therefore this
attribute needs to be removed (popped) from every individual dataset
before the concatenate function is called.

.. code:: ipython2

    #import iris
    
    ## read all the data in
    #cube_list = iris.load('z_cams_c_ecmf_20170301000000_prod_fc_pl*_aermr0*.nc')
    
    ## pop/remove the history attribute, otherwise merging is not possible
    #for i in cube_list:
    #    i.attributes.pop('history')
    
    #ods = cube_list.concatenate()
    ## Use the compression option; this can reduce the size of your netCDF massively
    #iris.save(ods, os.path.join(ROOT_DATA_PATH, 'moya_cams_c006.nc', zlib=True, packing='short'))

Model data
~~~~~~~~~~

The model data come from the Copernicus Atmospheric Monitoring Service
(http://atmosphere.copernicus.eu/ftp-access-global-data). The available
NetCDF covers the whole globe and at 25 pressure levels. The variables
we use are the three different dust aerosols.

-  aermr04 Dust Aerosol (0.03 - 0.55 um) Mixing Ratio
-  aermr05 Dust Aerosol (0.55 - 0.9 um) Mixing Ratio
-  aermr06 Dust Aerosol (0.9 - 20 um) Mixing Ratio

The current model products can be looked at online:
http://atmosphere.copernicus.eu/catalogue#/

.. code:: ipython2

    cams_c006 = cis.read_data_list('moya_cams_c006.nc',
                                   ['aermr04', 'aermr05', 'aermr06'])
    print(cams_c006)


.. parsed-literal::

    /usr/local/lib/python2.7/dist-packages/Iris-1.12.0.dev0-py2.7.egg/iris/fileformats/cf.py:76: FutureWarning: Conversion of the second argument of issubdtype from `str` to `str` is deprecated. In future, it will be treated as `np.string_ == np.dtype(str).type`.
      return ((six.PY2 and np.issubdtype(var.dtype, np.str)) or
    /usr/local/lib/python2.7/dist-packages/Iris-1.12.0.dev0-py2.7.egg/iris/fileformats/_pyke_rules/compiled_krb/fc_rules_cf_fc.py:1814: FutureWarning: Conversion of the second argument of issubdtype from `str` to `str` is deprecated. In future, it will be treated as `np.string_ == np.dtype(str).type`.
      if np.issubdtype(cf_var.dtype, np.str):


.. parsed-literal::

    GriddedDataList: 
    0: Dust Aerosol (0.03 - 0.55 um) Mixing Ratio / (kg kg**-1) (time: 9; pressure_level: 25; latitude: 451; longitude: 900)
    1: Dust Aerosol (0.55 - 0.9 um) Mixing Ratio / (kg kg**-1) (time: 9; pressure_level: 25; latitude: 451; longitude: 900)
    2: Dust Aerosol (0.9 - 20 um) Mixing Ratio / (kg kg**-1) (time: 9; pressure_level: 25; latitude: 451; longitude: 900)


.. code:: ipython2

    # Let's look at a curtain
    cams_curtain = cams_c006.subset(x=[16.5, 17.5],
                                    y=[11,14],
                                    z=[300, 1000])

.. code:: ipython2

    cams_curtain = cams_curtain.collapsed('time', how='mean')#
    print(cams_curtain)


.. parsed-literal::

    WARNING:root:Creating guessed bounds as none exist in file
    WARNING:root:Creating guessed bounds as none exist in file
    WARNING:root:Creating guessed bounds as none exist in file
    WARNING:root:Creating guessed bounds as none exist in file
    /usr/local/lib/python2.7/dist-packages/Iris-1.12.0.dev0-py2.7.egg/iris/coords.py:964: FutureWarning: Conversion of the second argument of issubdtype from `str` to `str` is deprecated. In future, it will be treated as `np.string_ == np.dtype(str).type`.
      if np.issubdtype(self.dtype, np.str):
    WARNING:root:Creating guessed bounds as none exist in file
    WARNING:root:Creating guessed bounds as none exist in file
    WARNING:root:Creating guessed bounds as none exist in file
    WARNING:root:Creating guessed bounds as none exist in file
    WARNING:root:Creating guessed bounds as none exist in file
    WARNING:root:Creating guessed bounds as none exist in file
    WARNING:root:Creating guessed bounds as none exist in file
    WARNING:root:Creating guessed bounds as none exist in file


.. parsed-literal::

    GriddedDataList: 
    0: Dust Aerosol (0.03 - 0.55 um) Mixing Ratio / (kg kg**-1) (pressure_level: 11; latitude: 8; longitude: 2)
    1: Dust Aerosol (0.55 - 0.9 um) Mixing Ratio / (kg kg**-1) (pressure_level: 11; latitude: 8; longitude: 2)
    2: Dust Aerosol (0.9 - 20 um) Mixing Ratio / (kg kg**-1) (pressure_level: 11; latitude: 8; longitude: 2)


We like to see the relation of small to middle sized aerosol.

.. code:: ipython2

    # create a new GriddedDataList
    grid_list = cis.data_io.gridded_data.GriddedDataList()
    grid_list.append(cams_curtain[0])
    grid_list.append(cams_curtain[1])
    ax = grid_list.plot(how='comparativescatter')
    ax.grid()



.. image:: /cis_workshop/cis_example_c006_files/cis_example_c006_12_0.png


.. code:: ipython2

    cams_curtain = cams_curtain.collapsed('longitude', how='mean')

.. code:: ipython2

    ax = cams_curtain[0].plot(yaxis='pressure_level', xaxis='latitude')
    ax.invert_yaxis()



.. image:: /cis_workshop/cis_example_c006_files/cis_example_c006_14_0.png


Aircraft data
~~~~~~~~~~~~~

Read in the total scatter and back scatter data from the Nephelometer.

.. code:: ipython2

    from cis.data_io.products.NCAR_NetCDF_RAF import NCAR_NetCDF_RAF, NCAR_NetCDF_RAF_variable_name_selector
    from cis.data_io.ungridded_data import UngriddedDataList
    
    # We have to do a bit of magic with the plugin so that it recognises 'PS_RVSM' as the pressure variable
    #  We could also have added the relavent metadata to the file
    selector = NCAR_NetCDF_RAF_variable_name_selector
    selector.CORRECTED_PRESSURE_VAR_NAME = 'PS_RVSM'
    plugin = NCAR_NetCDF_RAF(selector)
    
    variables = ['TSC_BLUU', 'TSC_GRNU', 'TSC_REDU', 'BSC_BLUU', 'BSC_GRNU', 'BSC_REDU']
    
    ara = UngriddedDataList(plugin.create_data_object(['core_faam_20170301_v004_r0_c006_1hz_edited.nc'], v) for v in variables)

We cut the first 10 and last 10 data points of, because they are not
errorenous and screw up the scaling of the figures in further steps.

.. code:: ipython2

    ara = [a[10:-10] for a in ara]

.. code:: ipython2

    print(ara)


.. parsed-literal::

    [<cis 'UngriddedData' of Ungridded data: Uncorrected blue total scattering coefficient from TSI 3563 Nephelometer / (m-1) 
    >, <cis 'UngriddedData' of Ungridded data: Uncorrected green total scattering coefficient from TSI 3563 Nephelometer / (m-1) 
    >, <cis 'UngriddedData' of Ungridded data: Uncorrected red total scattering coefficient from TSI 3563 Nephelometer / (m-1) 
    >, <cis 'UngriddedData' of Ungridded data: Uncorrected blue back scattering coefficient from TSI 3563 Nephelometer / (m-1) 
    >, <cis 'UngriddedData' of Ungridded data: Uncorrected green back scattering coefficient from TSI 3563 Nephelometer / (m-1) 
    >, <cis 'UngriddedData' of Ungridded data: Uncorrected red back scattering coefficient from TSI 3563 Nephelometer / (m-1) 
    >]


.. code:: ipython2

    ara = [a[10:-10] for a in ara]

.. code:: ipython2

    # TODO: Make the variables share one colorbar
    ax = ara[0].plot()
    ax.grid(True)



.. image:: /cis_workshop/cis_example_c006_files/cis_example_c006_22_0.png


.. code:: ipython2

    ax = ara[0].plot(xaxis='latitude', yaxis='air_pressure', how='scatter2d')



.. image:: /cis_workshop/cis_example_c006_files/cis_example_c006_23_0.png


Add pressure as a new coordinate to the CIS aircraft dataset.

.. code:: ipython2

    # Rename the CAMS pressure coordinate to match the aircraft
    cams_c006[0].coord('pressure_level').rename('air_pressure')

.. code:: ipython2

    col, = cams_c006[0].collocated_onto(ara[0])

.. code:: ipython2

    print(col)


.. parsed-literal::

    Ungridded data: Dust Aerosol (0.03 - 0.55 um) Mixing Ratio / (kg kg**-1) 
         Shape = (17047,)
    
         Total number of points = 17047
         Number of non-masked points = 13058
         Long name = Dust Aerosol (0.03 - 0.55 um) Mixing Ratio
         Standard name = None
         Units = kg kg**-1
         Missing value = nan
         Range = (-11465.600086975088, 3.81593147195343e-11)
         History = 2018-02-23T13:48:11Z Collocated onto sampling from: [] 
    using CIS version 1.6.1 
    variables: aermr04 
    with files: ['moya_cams_c006.nc'] 
    using collocator: <cis.collocation.col_implementations.GriddedUngriddedCollocator object at 0x7f3478cae550> 
    kernel: lin
         Coordinates: 
           time
              Long name = time of measurement
              Standard name = time
              Units = days since 1600-01-01 00:00:00
              Missing value = -1
              Range = (2017-03-01 15:35:34.000005, 2017-03-01 20:19:40.000003)
              History = 
              Misc attributes: 
                _Fillvalue = -1
                Calendar = gregorian
           latitude
              Long name = Latitude from POS AV 510 GPS-aided Inertial Navigation unit
              Standard name = latitude
              Units = degree_north
              Missing value = 0.0
              Range = (11.549055, 14.818923)
              History = 
              Misc attributes: 
                _Fillvalue = 0.0
                Frequency = 32
                Type = Data
                Number = 610
           longitude
              Long name = Longitude from POS AV 510 GPS-aided Inertial Navigation unit
              Standard name = longitude
              Units = degree_east
              Missing value = 0.0
              Range = (-17.774808883666992, -16.989221572875977)
              History = 
              Misc attributes: 
                _Fillvalue = 0.0
                Frequency = 32
                Type = Data
                Number = 611
           altitude
              Long name = Altitude from POS AV 510 GPS-aided Inertial Navigation unit
              Standard name = altitude
              Units = m
              Missing value = 0.0
              Range = (55.10959, 6529.192)
              History = 
              Misc attributes: 
                _Fillvalue = 0.0
                Frequency = 32
                Type = Data
                Number = 612
           air_pressure
              Long name = Static pressure from the aircraft RVSM (air data) system
              Standard name = air_pressure
              Units = hPa
              Missing value = -9999.0
              Range = (465.0087, 1008.6232)
              History = 
              Misc attributes: 
                _Fillvalue = -9999.0
                Frequency = 32
                Type = Data
                Number = 576
    


.. code:: ipython2

    col.plot(vmin=0.0)




.. parsed-literal::

    <cartopy.mpl.geoaxes.GeoAxesSubplot at 0x7f347864b650>




.. image:: /cis_workshop/cis_example_c006_files/cis_example_c006_28_1.png


.. code:: ipython2

    col.plot(xaxis='latitude', yaxis='air_pressure', how='scatter2d', vmin=0.0, vmax=1e-10)




.. parsed-literal::

    <matplotlib.axes._subplots.AxesSubplot at 0x7f3478590f10>




.. image:: /cis_workshop/cis_example_c006_files/cis_example_c006_29_1.png


.. code:: ipython2

    from cis.plotting.plot import basic_plot
    for a in ara:
        _, ax = basic_plot(col, xaxis=a, how='comparativescatter')
        ax.set_ylim([1e-11, 4e-11])



.. image:: /cis_workshop/cis_example_c006_files/cis_example_c006_30_0.png



.. image:: /cis_workshop/cis_example_c006_files/cis_example_c006_30_1.png



.. image:: /cis_workshop/cis_example_c006_files/cis_example_c006_30_2.png



.. image:: /cis_workshop/cis_example_c006_files/cis_example_c006_30_3.png



.. image:: /cis_workshop/cis_example_c006_files/cis_example_c006_30_4.png



.. image:: /cis_workshop/cis_example_c006_files/cis_example_c006_30_5.png

