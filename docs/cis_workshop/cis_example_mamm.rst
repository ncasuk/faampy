
MAMM - 2012 to 2014 - Analysing multiple flights covering several years
-----------------------------------------------------------------------

For the MAMM campaign (Methane in the Arctic: Measurements and
Modelling) the FAAM aircraft went to Kiruna, Sweden several times to
measure methane concentrations over the wetlands in Sweden and Finland.

.. code:: ipython2

    %matplotlib inline
    
    import cis
    import datetime
    import os
    import numpy as np
    
    ROOT_DATA_PATH = os.path.join(os.path.expanduser('~'), 'faampy_data', 'cis_workshop', 'mamm')
    
    os.chdir(ROOT_DATA_PATH)

Reading in modified FAAM core data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reading in **all** data files. Those files have been created previously
by merging the FAAM core netCDF with the FGGA (Fast Greenhouse Gashouse
Analyser) instrument nasa-AMES data. By default the core dataset does
not contain either the CO2 or CH4 data.

.. code:: ipython2

    methane = cis.read_data(ROOT_DATA_PATH+'/*/core_faam*.nc', 'CH4')

Flag all methane data, when the latitude coordinate is '0' or below.

.. code:: ipython2

    methane.data = np.ma.masked_where(methane.data < 0, methane.data)
    methane.data = np.ma.masked_where(methane.coords()[1].data <= 0, methane.data)

Plot time series of methane.

.. code:: ipython2

    methane.plot(xaxis='time')




.. parsed-literal::

    <matplotlib.axes._subplots.AxesSubplot at 0x7fdaa3b7f990>




.. image:: /cis_workshop/cis_example_mamm_files/cis_example_mamm_9_1.png


Analysis
~~~~~~~~

Subsetting for the three years 2012, 2013, and 2014.

.. code:: ipython2

    from cis.time_util import PartialDateTime
    data = {}
    data['2012'] = methane.subset(t=PartialDateTime(2012))
    data['2013'] = methane.subset(t=PartialDateTime(2013))
    data['2014'] = methane.subset(t=PartialDateTime(2014))

.. code:: ipython2

    data['2012'].plot()




.. parsed-literal::

    <cartopy.mpl.geoaxes.GeoAxesSubplot at 0x7fdaa38f0410>




.. image:: /cis_workshop/cis_example_mamm_files/cis_example_mamm_13_1.png


Aggregate all data for each year, where every cell is 0.5x0.5 degrees
and look only data points for the lowest 1000m.

.. code:: ipython2

    for year in ['2012', '2013', '2014']:
        data[year+'_agg'] = data[year].aggregate(x=[10, 40, 0.5],
                                                 y=[65, 85, 0.5],
                                                 z=[0, 1000, 1000],
                                                 how='mean')


.. parsed-literal::

    WARNING:root:Standard name 'None' not CF-compliant, this standard name will not be used in the output file.
    WARNING:root:Standard name 'None' not CF-compliant, this standard name will not be used in the output file.
    WARNING:root:Standard name 'None' not CF-compliant, this standard name will not be used in the output file.


.. code:: ipython2

    data['2012_agg'].plot()
    data['2013_agg'].plot()
    data['2014_agg'].plot()




.. parsed-literal::

    <cartopy.mpl.geoaxes.GeoAxesSubplot at 0x7fdaa3e224d0>




.. image:: /cis_workshop/cis_example_mamm_files/cis_example_mamm_16_1.png



.. image:: /cis_workshop/cis_example_mamm_files/cis_example_mamm_16_2.png



.. image:: /cis_workshop/cis_example_mamm_files/cis_example_mamm_16_3.png

