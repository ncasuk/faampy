
Recipe - Post Flight Analysis
=============================

This is an example for what the post flight analysis for a typical FAAM chemistry flight could look like.

The data we are using are from the "Into the Blue" flight b991 on the 24th October 2016. This flight took us up and down the west coast between Morecambe and Wales. On that stretch some "plumes" were sampled, that originated from the Manchester/Liverpool area.

.. image:: ./img/b991_flight_track.png

.. warning:: All the provided chemistry data in the example dataset are preliminary and uncalibrated. Therefore the data are not suitable for scientific publication.


Getting Started
---------------

At the start we need to import a number of modules and define a few variables that we need in later steps.

.. literalinclude:: ./../../examples/faampy_flight_analysis_example.py
   :language: python
   :start-after: Step:Start:Setup
   :end-before: Step:End:Setup


Reading in data from the different chemistry instruments.

.. literalinclude:: ./../../examples/faampy_flight_analysis_example.py
   :language: python
   :start-after: Step:Start:Reading in data
   :end-before: Step:End:Reading in data

Merge the data different datasets.

.. literalinclude:: ./../../examples/faampy_flight_analysis_example.py
   :language: python
   :start-after: Step:Start:Merging data
   :end-before: Step:End:Merging data

Google-Earth overlays
---------------------

The commands in this section are run from the konsole. To keep the filenames short we move into the directory where the data for b991 are located::

    cd ~/faampy_data/example_data/b991


We create a gpx (`GPS Exchange Format <https://en.wikipedia.org/wiki/GPS_Exchange_Format>`_) file::

    faampy nc_to_gpx core/core_faam_20161024_v004_r0_b991.nc .


We use the gpx data file to geotag a few photographs that were taking during the flight. The gpscorrelate utility can be installed from the linux distribution package manager::

    gpscorrelate --gps b991_20161024.gpx --photooffset -3600 photos/*jpg


Now that the photos are geotagged it is possible to create a photo album::

    faampy ge_photo_album ./photos ./ge_photo_album_20161024_b991.kmz


WAS (Whole Air Sample) bottle overlay::

    faampy ge_was_to_kmz ./chem_data/B991.WAS ./core/core_faam_20161024_v004_r0_b991_1hz.nc .


Now make profiles for some of the variables in the created merged file.

.. literalinclude:: ./../../examples/faampy_flight_analysis_example.py
   :language: python
   :start-after: Step:Start:Create google-earth profiles
   :end-before: Step:End:Create google-earth profiles

   
Quicklook Figures
-----------------

faampy provides a tool to create quicklook figures using information from the flight summary. According to the event name (e.g. Profile, Run, ...) either a time series or a profile plot is produced. Maps are created for every event and tephigrams for every profile.

.. literalinclude:: ./../../examples/faampy_flight_analysis_example.py
   :language: python
   :start-after: Step:Start:Quicklook Figures
   :end-before: Step:End:Quicklook Figures
      
Make the output directory for the quicklook figure files::    
    
    mkdir ~/b991_quicklooks


The quicklook tool is also available from the command line. First create a quicklooks configuration file (quicklooks.cfg) which defines the figure layout::
     
     touch quicklooks.cfg

Add the following text to the quicklooks.cfg file using a text editor::

    [['TSC_BLUU', 'TSC_GRNU' , 'TSC_REDU'], ['BSC_BLUU', 'BSC_GRNU', 'BSC_REDU']]
    [['CO_AERO'],]
    [['ch4_ppb'], ['co2_ppm']]
    [['no_conc'], ['no2_conc'], ['nox_conc']]

Every line defines one figure and the number of subplots. For example the first line ([['TSC_BLUU', 'TSC_GRNU' , 'TSC_REDU'], ['BSC_BLUU', 'BSC_GRNU', 'BSC_REDU']]) will create two subplots. In the 1st of these the total scatter values from the Nephelometer will be plotted and in the 2nd subplot the backscatter values will be plotted.

We will use the merged data file, which we produced in the previous section. This file contains the NOx and FGGA data. The command for creating the quicklooks is::

    faampy plt_quicklooks --config_file quicklooks.cfg b991_merged.nc \
      ./core/flight-sum_faam_20161024_r0_b991.txt ~/b991_quicklooks/

If the above commmand was successful the figures should have been created in the b991_quicklooks directory in your home directory.

Coloured Line Figure
--------------------

.. literalinclude:: ./../../examples/faampy_flight_analysis_example.py
   :language: python
   :start-after: Step:Start:Coloured Line
   :end-before: Step:End:Coloured Line

Transect Figure   
---------------

.. literalinclude:: ./../../examples/faampy_flight_analysis_example.py
   :language: python
   :start-after: Step:Start:Transect Figure
   :end-before: Step:End:Transect Figure
