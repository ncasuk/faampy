'''
Created on 14 Dec 2010

@author: axel
'''

import os
import sys
sys.path.insert(0, '/home/axel/git-repos/faampy')

from faampy.fltcons.parser import Parser
from faampy.fltcons.db import DB
from faampy.utils.file_list import File_List



def update(inpath=None, clean=False, root_path=None, verbose=False):
    fl = File_List(inpath)
    fl.filter_by_data_type('flight-cst')

    fcdb = DB()
    fcdb.connect()
    if clean:
        fcdb.clean()

    parser = Parser()

    for f in fl:                
        if verbose:
            sys.stdout.write('%s\n' % f)
        #try:
        d = parser.parse(os.path.join(f.path, f.filename))
        #except:
        #    sys.stdout.write('Problem parsing %s ...\n' % f.filename)
        #    continue

        if d:
            par, fid, rev, rdate, line, fname = [], [], [], [], [], []
            for k in d.keys():
                par.append(k)
                fid.append(d[k][0])    # strip the b from the fid
                rev.append(d[k][1])
                rdate.append(d[k][2])
                line.append(d[k][3])
                fname.append(f.filename)
            try:
                fcdb.insert(par, fid, rev, rdate, line, fname)
            except:
                pass


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Flight Constants database creator for instrument debugging purposes.')
    parser.add_argument('--inpath',
                        action='store',
                        type=str,
                        help="directory where the flight constants are stored")
    parser.add_argument('-c', '--clean',
                        action='store',
                        type=bool,
                        default=False,
                        help="Clean db before inserting any data")
    args = parser.parse_args()
    update(inpath=args.inpath, clean=args.clean)


#update(inpath='/media/axel/F60AD5E60AD5A3C1/badcMirror/data/', clean=True)
#inpath='/home/data/faam/badc/2016'
