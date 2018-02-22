==================
Command line tools
==================

The faampy module provides a number of command line tools. All those commands are called via::

   faampy SUBCOMMAND [OPTIONS] ARGUMENTS

A list of available subcommands is shown by just typing "faampy" on the command line.

core_diff
~~~~~~~~~
.. argparse::
   :module: faampy.utils.core_diff
   :func: _argparser
   :prog: faampy core_diff
   :nodefault:

nimrod_to_nc
~~~~~~~~~~~~
.. argparse::
   :module: faampy.data_io.nimrod_to_nc
   :func: _argparser
   :prog: faampy nimrod_to_nc
   :nodefault:

nc_to_gpx
~~~~~~~~~
.. argparse::
   :module: faampy.mapping.nc_to_gpx
   :func: _argparser
   :prog: faampy nc_to_gpx
   :nodefault:

ge_avaps
~~~~~~~~
.. argparse::
   :module: faampy.avaps.dropsonde
   :func: _argparser
   :prog: faampy ge_avaps
   :nodefault:

ge_flight_track
~~~~~~~~~~~~~~~
.. argparse::
   :module: faampy.mapping.ge_flight_track
   :func: _argparser
   :prog: faampy ge_flight_track
   :nodefault:

ge_ncas_airquality
~~~~~~~~~~~~~~~~~~
.. argparse::
   :module: faampy.mapping.ge_ncas_airquality
   :func: _argparser
   :prog: faampy ge_ncas_airquality
   :nodefault:

ge_nimrod_to_kmz
~~~~~~~~~~~~~~~~
.. argparse::
   :module: faampy.mapping.ge_nimrod_to_kmz
   :func: _argparser
   :prog: faampy ge_nimrod_to_kmz
   :nodefault:

ge_photo_album
~~~~~~~~~~~~~~
.. argparse::
   :module: faampy.mapping.ge_photo_album
   :func: _argparser
   :prog: faampy ge_photo_album
   :nodefault:

ge_ncvar_to_kml
~~~~~~~~~~~~~~~
.. argparse::
   :module: faampy.mapping.ge_ncvar_to_kml
   :func: _argparser
   :prog: faampy ge_ncvar_to_kml
   :nodefault:

ge_was_to_kmz
~~~~~~~~~~~~~
.. argparse::
   :module: faampy.mapping.ge_was_to_kmz
   :func: _argparser
   :prog: faampy ge_was_to_kmz
   :nodefault:

sat_tracker
~~~~~~~~~~~
.. argparse::
   :module: faampy.mapping.sat_tracker
   :func: _argparser
   :prog: faampy sat_tracker
   :nodefault:

plt_quicklooks
~~~~~~~~~~~~~~
.. argparse::
   :module: faampy.plotting.quicklooks
   :func: _argparser
   :prog: faampy plt_quicklooks
   :nodefault:

qa_report
~~~~~~~~~
.. argparse::
   :module: faampy.qa_plotting.report
   :func: _argparser
   :prog: faampy qa_report
   :nodefault:
