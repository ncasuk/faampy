
Recipe - Data Mining
====================

The code snipped below loops over all FAAM core data files and extracts the CO and O3 data plus coordinates. All the data are conatentated and written out to one large csv file.


.. code-block:: python

    #!/usr/bin/env python2
    # -*- coding: utf-8 -*-
    """
    Scripts finds all FAAM core data files and filters for the filter_latest_revision.
    The FAAM_Dataset object from the faampy module is used, which makes processing easier,
    by synchronicing variables names and adding an artificial WOW FLag for old flights
    
    """
    
    from faampy.core.faam_data import FAAM_Dataset
    from faampy.utils.file_list import File_List
    import os
    import netCDF4
    import numpy as np
    
    
    #================================================================
    
    ROOT_DATA_PATH = '/mnt/faamarchive/badcMirror/data/'
    OUTFILENAME = os.path.join(os.path.expanduser('~'), 'chemistry_spatial.csv')
    
    #================================================================
    
    
    # Get all hires FAAM core data
    fl = File_List(ROOT_DATA_PATH)
    fl.filter_by_data_type('core-hires')
    fl.filter_latest_revision()
    
    
    def extract(core_netcdf):
        """
        Extracts all CO and O3 data from a FAAM core netCDF.
        
        """
        
        ncfilename = os.path.join(core_netcdf.path, core_netcdf.filename)
        ds = FAAM_Dataset(ncfilename)
        _ds_index = ds.index.ravel()
        units = 'seconds since %s 00:00:00 +0000' % str(_ds_index[0])[:10]
        timestamp = netCDF4.num2date(ds.variables['Time'][:].ravel(), units)    
        n = timestamp.size
        
        if 'CO_AERO' in ds.variables.keys():
            co_aero = ds.variables['CO_AERO'][:]
            co_aero_flag = ds.variables['CO_AERO_FLAG'][:]
            co_aero[co_aero_flag != 0] = -9999.0
        else:
            co_aero = np.zeros(n)-9999.0
            
        if 'O3_TECO' in ds.variables.keys():
            o3_teco = ds.variables['O3_TECO'][:]
            o3_teco_flag = ds.variables['O3_TECO_FLAG'][:]
            o3_teco[o3_teco_flag != 0] = -9999.0
        else:
            o3_teco = np.zeros(n)-9999.0
        
        # Old FAAM files didn't have the GIN instrument fitted
        if 'LAT_GIN' in ds.variables.keys():
            lon_var_name = 'LON_GIN'
            lat_var_name = 'LAT_GIN'
            alt_var_name = 'ALT_GIN'
        elif 'LAT_GPS' in ds.variables.keys():
            lon_var_name = 'LON_GPS'
            lat_var_name = 'LAT_GPS'
            alt_var_name = 'GPS_ALT'
        
        if len(ds.variables[lon_var_name][:].shape) > 1:
            x = ds.variables[lon_var_name][:, 0].ravel()
            y = ds.variables[lat_var_name][:, 0].ravel()
            z = ds.variables[alt_var_name][:, 0].ravel()
        else:
            x = ds.variables[lon_var_name][:].ravel()
            y = ds.variables[lat_var_name][:].ravel()
            z = ds.variables[alt_var_name][:].ravel()
        
        wow = ds.variables['WOW_IND'][:].ravel()
        
        timestamp_string = [t.strftime('%Y-%m-%dT%H:%M:%S') for t in timestamp]
        fid = [core_netcdf.fid,]*n
        result = zip(list(np.array(timestamp_string)[wow == 0]),
                     list(np.array(fid)[wow == 0]),
                     list(x[wow == 0]),
                     list(y[wow == 0]),
                     list(z[wow == 0]),
                     list(co_aero[wow == 0]),
                     list(o3_teco[wow == 0]))
        return result
    
    
    # open the output file and write the column labels out
    ofile = open(OUTFILENAME, 'w')
    ofile.write('timestamp,fid,lon,lat,alt,co,o3\n')
    
    # loop over all core files
    for core_netcdf in fl:
        print('Working on ... %s' % core_netcdf.fid)
        try:
            data = extract(core_netcdf)
        except:
            print('  Issue with %s ...' % core_netcdf.fid)
            continue
        
        out_txt = ['%s,%s,%f,%f,%f,%f,%f\n' % l for l in data]
        out_txt = ''.join(out_txt)
        ofile.write(out_txt)
        ofile.flush()
    
    ofile.close()
    
    