
Recipe - FAAM core
==================

FAAM core data have been available as NetCDF ever since the 1st FAAM science flight took place back in 2004. However, details of the NetCDF have changed over time and the FAAM_Dataset class helps to iron out those small annoyances. Maybe at some point all FAAM flights will be reprocessed to create an unified format.

.. code-block:: python
    
    import os
    from faampy.core.faam_data import FAAM_Dataset
    
    ifile = os.path.join(os.path.expanduser('~'), 
                         'gdrive',
                         'core_processing',
                         '2017',
                         'c013-may-17',
                         'core_faam_20170517_v004_r0_c013_1hz.nc')

     ds = FAAM_Dataset(ifile)
     # get a pandas dataframe
     df = ds.as_dataframe()
     # Plot a time series of TAT_ND_R
     df.TAT_ND_R.plot()
