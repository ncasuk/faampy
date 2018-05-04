'''
Created on 3 Nov 2011

@author: axel
'''

import os
import subprocess

import FAAMy

OUTFOLDER = '/home/axel/tmp_fltlog/'

def pdf2txt(file):
    """converts the flight-logs from pdf into txt format, so that 
they can be parsed by usual linux tools

    """ 
    fid = getFlightNumberFromFilename(file)
    outfile = os.path.join(OUTFOLDER, 'b%.3i_flightlog_crew_list.txt' % fid)
    cmd = """pdftotext -f 1 -l 1 %s %s """ % (file, outfile)    
    proc = subprocess.Popen(cmd, shell=True)        
    proc.wait()
    

