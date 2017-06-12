import os
import sys
import fnmatch
import matplotlib as mpl
mpl.use('Agg')

from ppodd.core import *
import ppodd.pod

import matplotlib.pyplot as plt


##################################################################################

FID='c013'
DATE='20170517'
SEARCH_PATH='/home/axel/gdrive/core_processing/2017/'
NC_REVISION='0'
WRITE_NC=False
OUTPATH='/home/axel/gdrive/core_processing/2017/c013-may-17/'

##################################################################################



def find_file(pattern):
    matches = []
    for root, dirnames, filenames in os.walk(SEARCH_PATH):
        for filename in fnmatch.filter(filenames, pattern):
            matches.append(os.path.join(root, filename))
    matches.sort(key=os.path.basename)
    return matches[-1]


rawdlu_file=find_file('core_faam_%s*%s_rawdlu.zip' % (DATE, FID))
fltcst_file=find_file('flight-cst_faam_%s*%s.txt' % (DATE, FID))

if not OUTPATH:
    OUTPATH=os.path.dirname(rawdlu_file)


d = decades_dataset()
d.add_file(rawdlu_file)
d.add_file(fltcst_file)

# Deiced temperature probe broken
mods=['RIO_TEMPS',]
for m in mods:
    d.modules[m].run()
for k in d.modules.keys():
    if k != 'RIO_TEMPS':
        d.modules[k].runstate='ready'

tat_di_r_data=np.array(d['TAT_DI_R'].data[:])
tat_di_r_flag=np.array(d['TAT_DI_R'].flag[:])

# copy the deiced data over for the general processing
d['TAT_DI_R'].data[:]=np.array(d['TAT_ND_R'].data[:])
d['TAT_DI_R'].flag[:]=np.array(d['TAT_ND_R'].flag[:])


d.process()

d['TAT_DI_R'].data[:] = tat_di_r_data
d['TAT_DI_R'].flag[:] = 3



writer=d.write_nc


PARAMS_TO_BE_REMOVED = ['EXX_ZEUS', 'NV_LWC_U', 'NV_TWC_U', 'NV_LWC_C', 'NV_TWC_C',
                        'VMR_CR2',  'VMR_C_U', 'TDEW_CR2', 'TDEW_C_U', 'TDEWCR2C',
                        'RED_DN_C', 'RED_UP_C', 'LWC_JW_U']
PARAMS_TO_BE_ADDED = []

for p in PARAMS_TO_BE_REMOVED:
    if p in writer.input_names:
        writer.input_names.pop(writer.input_names.index(p))

for p in PARAMS_TO_BE_ADDED:
    if p not in writer.input_names:
        writer.input_names+=[p,]

ncfilename=os.path.join(OUTPATH, 'core_faam_%s_v004_r%s_%s.nc' % (DATE, NC_REVISION, FID))
if WRITE_NC:
    writer.process(ncfilename)
    writer.process(ncfilename[:-3]+'_1hz.nc', onehz=True)


import report

report.process(decades_dataset=d)