#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Script updates the flight constants and flight track databases.

"""

import datetime
import os
import sys

import faampy
import faampy.fltcons.update
from faampy.utils.file_list import File_List
from faampy.core.faam_data import FAAM_Dataset
from faampy.core.faam_spatial import FAAM_Spatial_DB
import faampy.core.flight_summary

def update_fltcons_db(inpath):
    faampy.fltcons.update.update(inpath=inpath, clean=True)
    return


def time_convert(base_time, time_string):
    secs = int(time_string[0:2])*3600+\
           int(time_string[2:4])*60+\
           int(time_string[4:6])
    result = base_time+datetime.timedelta(seconds=secs)
    return result


def update_spatial_db(inpath, overwrite=False):
    # connect to database
    try:
        sdb = FAAM_Spatial_DB(os.path.join(faampy.FAAMPY_DATA_PATH,
                                           'db',
                                           'faam_spatial_db.sqlite'))
    except:
        sys.stdout.write('Can not connect to db ...\n')
        sys.stdout.write('Leaving ...\n')
        return
    core_file_list = File_List(inpath)
    core_file_list.filter_by_data_type('core-hires')
    core_file_list.filter_latest_revision()

    fltsumm_file_list = File_List(inpath)
    fltsumm_file_list.filter_by_data_type('flight-sum')
    fltsumm_file_list.filter_latest_revision()

    for f in core_file_list:
        try:
            # check if the fid exists in the db, otherwise just move on
            ds = FAAM_Dataset(os.path.join(f.path, f.filename))
            dt = datetime.datetime.strptime(f.date, '%Y%m%d')
            sdb.insert_flight_track(f.fid, dt, ds.coords.as_wkt(simplified=True, as_type='LINESTRINGZ'), overwrite=overwrite)
            for fltsumm_file in fltsumm_file_list:
                if f.fid == fltsumm_file.fid:
                    fs = faampy.core.flight_summary.process(os.path.join(fltsumm_file.path,
                                                                         fltsumm_file.filename),
                                                            os.path.join(f.path, f.filename))
        except:
            pass

        for ent in fs.Entries:
            # Only consider two-point events
            if ent.Stop_time:
                try:
                    wkt = 'LINESTRINGZ(%s, %s)' % (' '.join([str(e) for e in ent.Coords[0]]),
                                                  ' '.join([str(e) for e in ent.Coords[-1]]))
                    sdb.insert_fltsumm_event(f.fid,
                                             ent.Name,
                                             time_convert(fs.date, ent.Start_time_48),
                                             time_convert(fs.date, ent.Stop_time_48),
                                             wkt,
                                             overwrite=overwrite)
                    sys.stdout.write('Added %s to %s ...\n' % \
                              (f.fid, os.path.basename(sdb.db_file)))
                except:
                    sys.stdout.write('Errors adding %s to %s ...\n' % \
                              (f.fid, os.path.basename(sdb.db_file)))

    sdb.close()
    return


def _argparser():
    import argparse
    #if not __name__ == '__main__':
    #    sys.argv.insert(0, 'faampy data_update')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--inpath',
                        action="store",
                        default='/mnt/faamarchive/badcMirror',
                        type=str,
                        help='inpath where all the FAAM core data are stored')
    parser.add_argument('-o', '--overwrite',
                        action="store_true",
                        default=False,
                        help='whether to overwrite the data or not')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()
    if not os.path.exists(args.inpath):
        sys.stdout.write('Data directory does not exists ...\n')
        sys.stdout.write('Leaving ...\n')
        sys.exit(1)
    update_fltcons_db(args.inpath)
    update_spatial_db(args.inpath, overwrite=args.overwrite)


if __name__ == '__main__':
    main()
