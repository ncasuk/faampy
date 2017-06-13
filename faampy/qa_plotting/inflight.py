import datetime
import os
import sys

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

from ppodd.core import *
import ppodd.pod

import subprocess


import errno
import os

#http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def find_file(search_path, pattern):
    matches = []
    for root, dirnames, filenames in os.walk(search_path):
        for filename in fnmatch.filter(filenames, pattern):
            matches.append(os.path.join(root, filename))
    matches.sort(key=os.path.basename)
    return matches

import tempfile
import zipfile
def create_zip(file_list):
    zipfilename=tempfile.mktemp(suffix='.zip')

    #zipfilename='/home/axel/core_faam_20160317_r99_b952_rawdlu.zip'
    zf = zipfile.ZipFile(zipfilename, "w")
    for f in file_list:
        zf.write(f)
    zf.close()
    return zipfilename


TCP_DEF_PATH='./tcpdefinition/'
ROOT_DATA_DIR='/home/axel/qa_data/'

today = datetime.datetime.utcnow()
year, month, day = (today.year, today.month, today.day)
DATA_DIR=os.path.join(ROOT_DATA_DIR, str(year), str(month), str(day))
if not os.path.exists(DATA_DIR):
    mkdir_p(DATA_DIR)

cmd='rsync --inplace -a axel@192.168.101.108:/opt/decades/output/%i/%.2i/%.2i/ %s' % (year, month, day, DATA_DIR)
print(cmd)
#rsync --inplace -a --progress user@server:/<destination_file_or_folder> <destination_on_cli2>

fltcst_file='/home/axel/Dropbox/campaigns/wintex2016/b952-mar-17/flight-cst_faam_20160317_r0_b952.txt'
d=decades_dataset()
file_list=find_file(TCP_DEF_PATH, '*') +find_file(DATA_DIR, '*')

rawdlu_file=create_zip(file_list)
d.add_file(rawdlu_file)
d.add_file(fltcst_file)

d.process()


plt.close('all')

import temperature
import buck
import cabin_pressure
import nephelometer
import psap
import nevzorov
import flags
import humidity
import co
import turbulence
import twc

from style import *

for instr in [temperature, nevzorov, buck, nephelometer, psap, cabin_pressure, co, humidity, twc]:
    try:
        instr.main(d)
        plt.pause(0.05)
        sys.stdout.write('Success %s ...\n' % (instr.__name__,))
    except:
        sys.stdout.write('Trouble processing %s ...\n' % (instr.__name__,))
        plt.close()
