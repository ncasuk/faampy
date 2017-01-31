'''
Created on 6 Aug 2012

@author: axel
'''

import os

import re
import subprocess
import sys

SRTM_ROOT_FOLDER = '/home/data/mapdata/srtm'
#SRTM_ROOT_FOLDER = '/home/data/mapdata/srtm/xftp.jrc.it/pub/srtmV4/tiff'


def get_srtm_files(directory=None):
    result = []
    if not directory:
        directory = SRTM_ROOT_FOLDER
    file_list = os.listdir(directory)
    for f in file_list:
        if os.path.splitext(f)[1] == '.tif':
            result.append(os.path.join(directory, f))
    return result


def get_tif_boundaries(tif_filename, quite=None):
    if not quite:
        quite = False
    else:
        quite = True
    cmd = """gdalinfo %s""" % (tif_filename)
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out = proc.stdout.read().splitlines()
    boundaries = {}
    for line in out:
        if line.startswith('Upper Left'):
            boundaries['ul'] = [float(e) for e in re.split('\(|\)|,', line)[1:3]]
        elif line.startswith('Lower Left'):
            boundaries['ll'] = [float(e) for e in re.split('\(|\)|,', line)[1:3]]
        elif line.startswith('Upper Right'):
            boundaries['ur'] = [float(e) for e in re.split('\(|\)|,', line)[1:3]]
        elif line.startswith('Lower Right'):
            boundaries['lr'] = [float(e) for e in re.split('\(|\)|,', line)[1:3]]
        else:
            pass
    if not quite:
        #print(boundaries)
        pass
        #sys.stdout.write(os.path.basename(tif_filename))
        #sys.stdout.write(boundaries)
    return boundaries


def find_srtm_file(file_list, lon, lat):
    result = None
    for f in file_list:
        boundary = get_tif_boundaries(f)
        try:
            if (lon > boundary['ul'][0]) and (lat < boundary['ul'][1]) and (lon < boundary['lr'][0]) and (lat > boundary['lr'][1]):
                result = f
        except:
            pass
    return result


def get_elevation(tif_filename, lon, lat):
    result = None
    cmd = """gdallocationinfo %s -wgs84 %f %f""" % (tif_filename, lon, lat)
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out = proc.stdout.read().splitlines()
    for line in out:
        if line.strip().startswith('Value'):
            result = float(line.split(':')[1])
    return result


srtm_file_list = get_srtm_files()
for f in srtm_file_list:
    get_tif_boundaries(f, quite=True)


#for s in sondes:
#    lon, lat = (s[1], s[2])
#    f = find_srtm_file(srtm_file_list, lon, lat)
#    if f:
#        elev = get_elevation(f, lon, lat)
#        print(s[0] + ' ' + str(elev))
#    else:
#        print(s[0] + ' ' + 'unknown')




#cmd1 = """gdal_translate -of GTiff %s "%s" "%s" """ % (gcps, img_filename, tif_tmp_filename)
#cmd2 = """gdalwarp -t_srs EPSG:4326 -order -tps -co COMPRESS=NONE  "%s" "%s" """ % (tif_tmp_filename, tif_filename)


#tif_filename = '/home/data/mapdata/srtm/srtm_06_09.tif'
#cmd = """gdalinfo "%s" """ % (tif_filename)
#print(cmd)
#proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
#process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
