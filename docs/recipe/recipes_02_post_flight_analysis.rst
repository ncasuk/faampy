

Recipe - Post Flight Analysis
=============================

A standard example what the post flight analysis could look like using faampy.
  
Flight Data
-----------

The data we are using here are from the "Into the Blue" flight b991 on the 24th October 2016. This flight took us up and down the west coast between Morecambe and Wales.

Warning: All the Chemistry data are preliminary uncalibrated and not suitable for scientific analysis. The purpose here is to show an example for a post flight
work flow.


FAAM Dataset
------------

merging data
get it back as pandas dataframe
writing out as a new netcdf
Create a gpx file from the core data, which will be useful later on to create a photo album


Google-Earth overlays
---------------------




gpscorrelate --gps ~/Dropbox/campaigns/itb2016/ge/b991_20161024.gpx --photooffset -3600 *jpg

faampy ge_photo_album xxx


Quicklook Figures
-----------------

Create quicklook.cfg file

faampy quicklooks 
