
b991 - 20/10/2016 - Plume sampling from large cities (Manchester/Liverpool)
---------------------------------------------------------------------------


FAAM netCDF preparation
~~~~~~~~~~~~~~~~~~~~~~~

The FAAM core data do not work with the cis tool straight away. The netCDF need a little tweaking to make them fully CF compliant, so that cis interpretets the data correctly. The global attributes "Conventions" and "Coordinates" need to be added. A small bash script is provide (faam_edit.sh) that does the changes using nc utilities. The example netCDF has already been edited and works with cis.

The example data (core_faam_20161024_v004_r0_b991_1hz_edited.nc) are for flight b991 (24-10-2016), when the aircraft was flying downwind of Manchester and Liverpool measuring the emissions from the two cities ahead of the *Into the Blue* event at Manchester airport


 cd ~/Dropbox/cis_workshop/data/b991
 ./faam_edit.sh core_faam_20161024_v004_r0_b991_1hz.nc

 
Working with the FAAM data
~~~~~~~~~~~~~~~~~~~~~~~~~~

Below are several one line examples that show the functionality of the cis tools. Most of the examples have been taken and adapted from the cis online documentation.

.. note::
   All the commands below go on **one** line in your shell. The page is just too small to get it all printed on one line.

   
Get information about the netCDF::

    cis info TAT_ND_R:core_faam_20161024_v004_r0_b991_1hz_edited.nc

Create scatter plot to compare the deiced (TAT_DI_R) and non-deiced (TAT_ND_R) temperature measurements on the ARA::
    
    cis plot TAT_ND_R:core_faam_20161024_v004_r0_b991_1hz_edited.nc \
      TAT_DI_R:core_faam_20161024_v004_r0_b991_1hz_edited.nc \
      --type comparativescatter --grid \
      --title "True air temperature comparison" \
      --xlabel "non deiced sensor (K)" --ylabel "deiced sensor (K)"

And print some statistics about the TAT_DI_R variable::
    
    cis stats TAT_ND_R:core_faam_20161024_v004_r0_b991_1hz_edited.nc \
      TAT_DI_R:core_faam_20161024_v004_r0_b991_1hz_edited.nc

.. note:: 
    We can remove the warnings about the invalid units using the quiet flag.
    
Like this::    

    cis -q stats TAT_ND_R:core_faam_20161024_v004_r0_b991_1hz_edited.nc \
      TAT_DI_R:core_faam_20161024_v004_r0_b991_1hz_edited.nc



Make a coloured line plot, showing the CO concentration on a map::

  cis plot CO_AERO:core_faam_20161024_v004_r0_b991_1hz_edited.nc:product=NCAR_NetCDF_RAF --xmin -5 --xmax -2 --ymin 52.2 --ymax 55


Calculate mean,min,max for 1min time intervals for the CO_AERO data for the time interval 11:45 to 14:45. The results are written to a netCDF::

    cis aggregate CO_AERO:core_faam_20161024_v004_r0_b991_1hz_edited.nc:product=NCAR_NetCDF_RAF,kernel=mean \
      t=[2016-10-24T11:45,2016-10-24T14:45,PT1M] -o b991_co_aero_1min_mean.nc

    cis aggregate CO_AERO:core_faam_20161024_v004_r0_b991_1hz_edited.nc:product=NCAR_NetCDF_RAF,kernel=max \
      t=[2016-10-24T11:45,2016-10-24T14:45,PT1M] -o b991_co_aero_1min_max.nc

    cis aggregate CO_AERO:core_faam_20161024_v004_r0_b991_1hz_edited.nc:product=NCAR_NetCDF_RAF,kernel=min \
      t=[2016-10-24T11:45,2016-10-24T14:45,PT1M] -o b991_co_aero_1min_min.nc
      
Plot the three lines in one figure::

    cis plot CO_AERO:b991_co_aero_1min_max.nc:label='max' \
      CO_AERO:b991_co_aero_1min_mean.nc:label='mean' \
      CO_AERO:b991_co_aero_1min_min.nc:label='min'


The results from the aggregation will be saved to a netCDF (option -o). The following line aggregates over 5 minutes and over altitude in 200 meter steps in the range of 0 to 1000m::
  
    cis aggregate CO_AERO:core_faam_20161024_v004_r0_b991_1hz_edited.nc:product=NCAR_NetCDF_RAF \
      t=[2016-10-24T11:45,2016-10-24T14:45,PT5M],z=[0,1000,200] \
      -o b991_co_aero_alt_time.nc

Plot a curtain (transect) using the netCDF that we just created::
  
    cis plot CO_AERO:b991_co_aero_alt_time.nc --xaxis time --yaxis altitude


Make a grid plot from the mean, where each grid cell is 0.2 degrees in size. The results are written to a netCDF::  

    cis aggregate CO_AERO:core_faam_20161024_v004_r0_b991_1hz_edited.nc:product=NCAR_NetCDF_RAF,kernel=mean \
      x=[-5,0,0.2],y=[52,55,0.2] -o b991_co_aero_grid_mean.nc

Now plot the grid on a map using the netcdf that we just created::

    cis plot CO_AERO:b991_co_aero_grid_mean.nc
