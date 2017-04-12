
Recipe - FAAM meets cis
=======================


CIS Installation
----------------

Information about installing anaconda2 and cis:
  | anaconda2: https://www.continuum.io/downloads
  | cis:       http://cistools.net/get-started#installation

Please note that the cis instructions say that you should install python 2.7 and **not** 3.x. If you are new to python you might be irritated why you wouldn't install the very latest version. In brief: The two versions are not fully compatible and many people decided to stick with 2.7. 
  
FAAM netCDF preparation
-----------------------

The FAAM core data do not work with the cis tool straight away. The netCDF need a little tweaking to make them fully CF compliant, so that cis interpretets the data correctly. The global attributes "Conventions" and "Coordinates" need to be added. A small bash script is provide (faam_edit.sh) that does the changes using nc utilities. The example netCDF has already been edited and works with cis.

The example data (core_faam_20161024_v004_r0_b991_1hz_editted.nc) are for flight b991 (24-10-2016), when the aircraft was flying downwind of Manchester and Liverpool measuring the emissions from the two cities ahead of the *Into the Blue* event. 


Starting cis
------------

The next thing to do is to start the cis environment that we installed earlier. Go to the bin directory of your conda installation::
    
    cd ~/anaconda2/bin/

and activate the environment::
    
    source activate cis_env

From now on the shell should have the string '(cis_env)' in front indicating that we are working in the cis envrionment.

In a next step we need to tell cis where to look for the FAAM_NetCDF plugin which is needed to read in the FAAM core data. The envronment variable CIS_PLUGIN_HOME has to be set to the directory that contains the FAAM_NetCDF.py file. For me the command looks like this::
    
     export CIS_PLUGIN_HOME=/home/axel/cis_plugin_development
     
Go to the directory where the edited faam core netcdf is stored to keep the file path short in the cis commands::

   cd ~/cis_plugin_development/data


Working with cis and FAAM data
------------------------------

Below are several one line examples that show the functionality of the cis tools. Most of the examples have been taken and adapted from the cis online documentation.

.. note::
   All the commands below go on **one** line in your shell. The page is just too small to get it all printed on one line.

.. note::
   If you get an Error message similar to:
     
     ERROR - 'DimCoord' object has no attribute 'data' - check cis.log for details
   
   cis can not find the FAAM_NetCDF plugin and it is most likely that the CIS_PLUGIN_HOME variable was not defined correctly.
   
Get information about the netCDF::

    cis info TAT_ND_R:core_faam_20161024_v004_r0_b991_1hz_editted.nc

Create scatter plot to compare the deiced (TAT_DI_R) and non-deiced (TAT_ND_R) temperature measurements on the ARA::
    
    cis plot TAT_ND_R:core_faam_20161024_v004_r0_b991_1hz_editted.nc \
      TAT_DI_R:core_faam_20161024_v004_r0_b991_1hz_editted.nc \
      --type comparativescatter --grid \
      --title "True air temperature comparison" \
      --xlabel "non deiced sensor (K)" --ylabel "deiced sensor (K)"

And print some statistics about the TAT_DI_R variable::
    
    cis stats TAT_ND_R:core_faam_20161024_v004_r0_b991_1hz_editted.nc \
      TAT_DI_R:core_faam_20161024_v004_r0_b991_1hz_editted.nc
    

Make a coloured line plot, showing the CO concentration on a map::

  cis plot CO_AERO:core_faam_20161024_v004_r0_b991_1hz_editted.nc \
    --xaxis longitude --yaxis latitude --xmin -5 --xmax -2 --ymin 52.2 --ymax 55


Calculate mean,min,max for 1min time intervals for the CO_AERO data for the time interval 11:45 to 14:45. The results are written to a netCDF::

    cis aggregate CO_AERO:core_faam_20161024_v004_r0_b991_1hz_editted.nc:kernel=mean \
      t=[2016-10-24T11:45,2016-10-24T14:45,PT1M] -o b991_co_aero_1min_mean.nc

    cis aggregate CO_AERO:core_faam_20161024_v004_r0_b991_1hz_editted.nc:kernel=max \
      t=[2016-10-24T11:45,2016-10-24T14:45,PT1M] -o b991_co_aero_1min_max.nc

    cis aggregate CO_AERO:core_faam_20161024_v004_r0_b991_1hz_editted.nc:kernel=min \
      t=[2016-10-24T11:45,2016-10-24T14:45,PT1M] -o b991_co_aero_1min_min.nc
      
Plot the three lines in one figure::

    cis plot CO_AERO:b991_co_aero_1min_max.nc \
      CO_AERO:b991_co_aero_1min_mean.nc \
      CO_AERO:b991_co_aero_1min_min.nc

Reproducing an aggregation example from the documentation:
  http://cis.readthedocs.io/en/stable/aggregation.html#aircraft-track

The results from the aggregation will be saved to a netCDF (option -o). The following line aggregates over 5 minutes and over altiude in 200 meter steps in the range of 0 to 1000m::
  
    cis aggregate CO_AERO:core_faam_20161024_v004_r0_b991_1hz_editted.nc \
      t=[2016-10-24T11:45,2016-10-24T14:45,PT5M],z=[0,1000,200] \
      -o b991_co_aero_alt_time.nc

Plot a curtain using the netCDF that we just created::
  
    cis plot CO_AERO:b991_co_aero_alt_time.nc --xaxis time --yaxis altitude


Make a grid plot from the mean, where each grid cell is 0.2 in size. The results are written to a netCDF::  

    cis aggregate CO_AERO:core_faam_20161024_v004_r0_b991_1hz_editted.nc:kernel=mean \
      x=[-5,0,0.2],y=[52,55,0.2] -o b991_co_aero_grid_mean.nc

Now plot the grid on a map using the netcdf that we just created::

    cis plot CO_AERO:b991_co_aero_grid_mean.nc
