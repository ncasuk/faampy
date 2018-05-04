'''
Parse the '00README' txt-file and looks for the
line that contains the pattern 'flight manager'

Created on 5 Nov 2011

@author: axel
'''

import os

import faampy
import faampy.utils


def who_was_flightmanager(core_file, fid):
    result = 'unknown'
    filename = os.path.join(os.path.dirname(core_file ), '..', '00README')
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()
    if fid == 648:
        return "Flight Manager - Alan Woolley"    
    for line in lines:
        if 'flight manager' in str.lower(line):
            result = line.strip()
    return result


core_fl = faampy.utils.FileList()
log_fl = faampy.utils.FileList()


core_fl.__filterByType__( 'core-hires' )
core_fl.__filterLatestRevision__()
log_fl.__filterByType__( 'flight-log' )
log_fl.__filterLatestRevision__()

log_fname, log_type, log_fno, log_rev = zip( *log_fl.FileInfo )
core_fname, core_type, core_fno, core_rev = zip( *core_fl.FileInfo )

latest_fno = max(core_fno)
for i in range(latest_fno, 450, -1):
    if i not in core_fno:
        print('b%.3i no core data available' %i)
    else:
        if i not in log_fno:
            timestamp = os.path.basename(core_fname[core_fno.index(i)]).split('_')[2]
            fm = who_was_flightmanager(core_fname[core_fno.index(i)], core_fno[core_fno.index(i)])
            print('b%.3i %s missing: %s' % (i, timestamp, fm))

