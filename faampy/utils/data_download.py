# -*- coding: utf-8 -*-
"""
Script for downloading faampy data, which are updated regularly

"""

import os
import subprocess
import sys
import tempfile
import urllib2
import zipfile

import faampy

FAAMPY_EXAMPLE_DATA_URL = 'http://www.faam.ac.uk/axel_share/faampy_example_data.zip'
FAAMPY_DATA_URL = 'http://www.faam.ac.uk/axel_share/faampy_data.zip'


def dlfile(url, local_zipfile):
    # Open the url
    try:
        sys.stdout.write("downloading %s\n" % url)
        f = urllib2.urlopen(url)

        # Open our local file for writing
        with open(local_zipfile, "wb") as local_file:
            local_file.write(f.read())

    # handle errors
    except urllib2.HTTPError as e:
        sys.stdout.write("HTTP Error: %i %s\n" % (e.code, url))
    except urllib2.URLError as e:
        sys.stdout.write("URL Error: %i %s\n" % (e.reason, url))
    return


def _argparser():
    import argparse
    from argparse import RawTextHelpFormatter
    if not __name__ == '__main__':
        sys.argv.insert(0, 'faampy data_download')
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('password',
                        action="store",
                        type=str,
                        help='zip file password')
    parser.add_argument('--no_examples',
                        action="store_true",
                        default=False,
                        help='will only download the regularly updated data')
    return parser


def cmd_exists(cmd):
    """
    Check if a cmd is available to use.
    """
    try:
        return subprocess.call("type " + cmd, shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0
    except:
        return False


def main():
    parser = _argparser()
    args = parser.parse_args()
    if args.no_examples:
        dl_file_list = dl_file_list = [FAAMPY_DATA_URL,]
    else:
        dl_file_list = [FAAMPY_EXAMPLE_DATA_URL, FAAMPY_DATA_URL]

    passwd = args.password
    if not os.path.exists(faampy.FAAMPY_DATA_PATH):
            os.makedirs(faampy.FAAMPY_DATA_PATH)
            sys.stdout.write('Created %s ...\n' % faampy.FAAMPY_DATA_PATH)
    if FAAMPY_EXAMPLE_DATA_URL in dl_file_list:
        if not os.path.exists(faampy.FAAMPY_EXAMPLE_DATA_PATH):
            os.makedirs(faampy.FAAMPY_EXAMPLE_DATA_PATH)
            sys.stdout.write('Created %s ...\n' % faampy.FAAMPY_EXAMPLE_DATA_PATH)

    for dl_file in dl_file_list:
        local_zipfile = tempfile.mktemp(suffix='.zip')
        dlfile(dl_file, local_zipfile)

        opath = faampy.FAAMPY_EXAMPLE_DATA_PATH
        if dl_file == FAAMPY_DATA_URL:
            opath = os.path.join(opath, '..')

        # If the unzip command is available we use subprocess, because it is much
        # faster than usein gthe zipfile python module
        if cmd_exists('unzip'):
            cmd = 'unzip -P %s -o %s -d %s' % (passwd, local_zipfile, opath)
            subprocess.call(cmd, shell=True)
        else:
            _zip = zipfile.ZipFile(local_zipfile)
            _zip.extractall(path=opath, pwd=passwd)
    return


if __name__ == '__main__':
    main()
