# -*- coding: utf-8 -*-
"""
The processing of the AIMMS data is done in several steps using win32
scripts that are called from the command line. This python script is only a
wrapper for those steps calling the scripts using wine, which allows the
processing to be done on a linux machine.

The final step is the conversion into a netCDF, which is currently done by a
idl routine. Therefore an idl installation is also required on the machine,
where the script runs.

The script is called as:

   python aimms_process.py FID


"""

import os
import re
import shutil
import sys
import tempfile

from file_info import *
from file_list import *

# AIMMS_ROOT_PATH = '/mnt/faamarchive/Data/cloudphysics'
# CORE_ROOT_PATH = '/mnt/faamarchive/badcMirror/'

AIMMS_ROOT_PATH = '/home/tardis/FAAMarchive/Data/cloudphysics'
CORE_ROOT_PATH = '/home/tardis/FAAMarchive/badcMirror/'

TEMPPATH = tempfile.mkdtemp()
OUTPATH = '/home/tardis/'
CALFILE = 'AIMMScalB884.dat'

_VERSION_ = 'v003'


def do_checks():
    # checking if wine and idl are installed
    return True


def get_aimms_raw_files(AIMMS_ROOT_PATH, fid):
    """The AIMMS probe produces severl raw data files for
    a single flight. Those files needs to be sticked together.
    """
    pattern = '.*%s.*odms.*\d{8}.*r\d{2}' % (fid,)
    file_list = []
    for root, subFolders, files in os.walk(AIMMS_ROOT_PATH):
        for f in files:
            filename = os.path.join(root, f)
            if re.match(pattern, filename.lower()):
                file_list.append(filename)
    return file_list


def get_core_file(CORE_ROOT_PATH, fid):
    fl = File_List(CORE_ROOT_PATH)
    fl.filter_by_data_type('core-lowres')
    fl.filter_latest_revision()
    for f in fl:
        if f.fid == fid:
            return os.path.join(os.path.join(f.path, f.filename))


def process(fid, revision, outpath):
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # get the flight number
    # fid = sys.argv[1]

    aimms_raw_files=get_aimms_raw_files(AIMMS_ROOT_PATH, fid)
    core_file = get_core_file(CORE_ROOT_PATH, fid)

    sys.stdout.write('AIMMS ODMS Files:\n%s\n' % '  \n'.join(['%s' % f for f in aimms_raw_files]))
    sys.stdout.write('FAAM Core: %s\n' % core_file)
    sys.stdout.write('Temp dir: %s\n' % TEMPPATH)

    date_string = os.path.basename(core_file).split('_')[2]

    # copy all the files that are needed for processing
    # into a temporary directory
    for f in aimms_raw_files:
        shutil.copy(f, os.path.join(TEMPPATH, os.path.basename(f)))
    shutil.copy(core_file, os.path.join(TEMPPATH, os.path.basename(core_file)))

    # all the files that are needed for the processing will be copied to the TEMPPATH to
    # keep things simple
    for f in ['asmbl.exe',
              'canextr4.exe',
              'ekf556.exe',
              'convert_aimms_netcdf.pro',
              'findcorefile.pro',
              'cal_files/'+CALFILE]:
        shutil.copy(os.path.join(dir_path, f), os.path.join(TEMPPATH, f))

    # move into the temporary directory
    os.chdir(TEMPPATH)

    # get the identifier from the raw files
    idents = list(set([os.path.splitext(os.path.basename(f))[0] for f in aimms_raw_files]))

    for i in idents:
        # stick the odms files together
        cmd = "wine asmbl.exe %s 1" % (i,)
        os.system(cmd)
        #cmd = "wine canextr4.exe %s.raw"
        aimms_out_file = '%s_%s_aimms.out' % (fid, date_string)
        cmd = "wine ekf556.exe %s %s.raw -c on -o %s" % (CALFILE, i, aimms_out_file)
        os.system(cmd)
    aimms_ncfile = os.path.join(outpath, 'metoffice-aimms_faam_%s_%s_r%i_%s.nc' % (date_string, _VERSION_, revision, fid))
    # call the idl script from the command line
    cmd = """idl -e "convert_aimms_netcdf, '%s/', '%s', '%s', '%s'"  """ % (os.path.join(TEMPPATH), os.path.join(TEMPPATH, os.path.basename(core_file)), aimms_ncfile, fid)
    os.system(cmd)






def main():
    import argparse
    from argparse import RawTextHelpFormatter

    parser = argparse.ArgumentParser(description=__doc__,
                                     version=__version__,
                                     epilog="Report bugs to %s." % __email__,
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('fid', action="store", type=str, help='Flight Number')
    parser.add_argument('-r', '--revision', action="store", type=int,
                        required=False, default=0,
                        help='revision nmuber of the AIMMS netcdf.')
    parser.add_argument('-o', '--outpath', action="store", type=str, required=False,
                        default=os.environ['HOME'],
                        help='Outpath for the netCDF Default: $HOME.')
    parser.add_argument('-k', '--keep-folder', action="store_true", required=False, default=False,
                        help='If option is set the temporary directory will *not* be deleted. Default: False')
    args=parser.parse_args()

    process(args.fid, args.revision, args.outpath)
    # clean_up behind ourselves
    if not args.keep_folder:
        sys.stdout.write('Deleting temporary folder %s ... \n' % (TEMPPATH))
        shutil.rmtree(TEMPPATH)


if __name__ == '__main__':
    main()







