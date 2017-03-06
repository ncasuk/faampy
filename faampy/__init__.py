"""
faampy main command which calls subcommands

The usage is for example
   faampy nc_to_gpx ....

"""


import argparse
import importlib
import os
import sys


__version__ = '0.1.2'
__status__ = 'a'


def command_line():
    # list of subcommands and assosciated python script
    # this has to be maintained manually and has to be
    # checked/updated with every release

    MODULES = [('data_download',      'faampy.utils.data_download'),
               ('nimrod_to_nc',       'faampy.data_io.nimrod_to_nc'),
               ('ge_ncas_airquality', 'faampy.mapping.ge_ncas_airquality'),
               ('ge_nimrod_to_kmz',   'faampy.mapping.ge_nimrod_to_kmz'),
               ('ge_photo_album',     'faampy.mapping.ge_photo_album'),
               ('ge_was_to_kmz',      'faampy.mapping.ge_was_to_kmz'),
               ('nc_to_gpx',          'faampy.mapping.nc_to_gpx'),
               ('ncvar_to_kml',       'faampy.mapping.ncvar_to_kml'),
               ('world_map',          'faampy.mapping.world_map'),
               ('sat_tracker',        'faampy.mapping.sat_tracker'),
               ('plt_quicklooks',     'faampy.plotting.quicklooks'),
               ('flight_summary',     'faampy.core.flight_summary')]

    parser = argparse.ArgumentParser(description="faampy",
                                     usage="""faampy <command> [<args>]

%s
""" % ('    \n'.join(['  '+m[0] for m in MODULES])))
    parser.add_argument('command', help='Subcommand to run')
    # parse_args defaults to [1:] for args, but you need to
    # exclude the rest of the args too, or validation will fail
    args = parser.parse_args(sys.argv[1:2])
    # check if subcommand is available. If not leave
    if args.command not in zip(*MODULES)[0]:
        print 'Unrecognized command\n'
        parser.print_help()
        sys.exit(1)
    else:
        sys.argv = sys.argv[2:]
    # use dispatch pattern to invoke method with same name
    for MOD in MODULES:
        if args.command == MOD[0]:
            mod = importlib.import_module(MOD[1])
            mod.main()  # the main method is called

FAAMPY_DATA_PATH = os.path.join(os.environ['HOME'], 'faampy_data')
SRTM_DATA_PATH = os.path.join(FAAMPY_DATA_PATH, 'srtm')

FAAM_DATA = ['icons/camera_icon_32x32.png',
             'icons/dot_blue_32x32.png',
             'icons/dot_green_32x32.png',
             'icons/dot_orange_32x32.png',
             'icons/dot_red_32x32.png',
             'icons/dropsonde_32x32.png',
             'icons/was_bottle_32x32.png',
             'img/world_osm_54030_6804x3450.png',
             'img/uk_osm_background_2244x2642.png',
             'img/world_osm_54030_27234x13812.png',
             'img/world_osm_54030_4806x2437.png',
             'img/world_osm_54030_13617x6906.png',
             'img/uk_osm_background_3366x3963.png',
             'img/world_osm_54030_9633x4885.png',
             'img/world_osm_54030_3402x1725.png',
             'img/uk_osm_background_9507x11195.png',
             'img/uk_osm_background_6732x7927.png',
             'img/uk_osm_background_19014x22390.png',
             'img/world_osm_54030_1134x575.png', ]
