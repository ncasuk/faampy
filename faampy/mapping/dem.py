'''
Created on 6 Aug 2012

@author: axel
'''

import os

import re
import subprocess
import sys

import faampy



def get_srtm_files(path):
    result = []
    file_list = os.listdir(path)
    for f in file_list:
        if os.path.splitext(f)[1] == '.tif':
            result.append(os.path.join(path, f))
    return result


def get_tif_boundaries(tif_filename):
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
    return boundaries


class DEM(object):
    """Uses gdal and the srtm files that can be downloaded for free from the 
    internet.
    """
    def __init__(self, srtm_data_path=None):
        if not srtm_data_path:
            self.SRTM_DATA_PATH = faampy.SRTM_DATA_PATH
            if not os.path.exists(self.SRTM_DATA_PATH):
                sys.stdout.write('SRTM data path: %s does not exists.\n' % (self.SRTM_DATA_PATH))        
        self.SRTM_Files = {}  # initialize an empty dictionary
        # fill-up the dictionary using the srtm basename as key and add
        # the four boundaries as values
        for f in get_srtm_files(self.SRTM_DATA_PATH):
            self.SRTM_Files[os.path.basename(f)] = {'bounds': get_tif_boundaries(f)}

    def find_srtm_file(self, lon, lat):
        for k, v in self.SRTM_Files.items():
            boundary = v['bounds']
            # check if coordinates are inside boundary box
            if (lon >= boundary['ul'][0]) and (lat <= boundary['ul'][1]) and \
               (lon <= boundary['lr'][0]) and (lat >= boundary['lr'][1]):
                return k
        return
    
    def get_elevation(self, lon, lat):
        """
        gives the elevation for a given coordinate
        :param lon: longitude WGS84
        :param lat: latitude WGS84
        """
        tif_filename = self.find_srtm_file(lon, lat)
        if not tif_filename:
            return
        cmd = """gdallocationinfo %s -wgs84 %f %f""" % (os.path.join(self.SRTM_DATA_PATH, tif_filename), lon, lat)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        out = proc.stdout.read().splitlines()
        for line in out:
            if line.strip().startswith('Value'):
                return float(line.split(':')[1])
        return

#faampy.SRTM_DATA_PATH = '/home/axel/srtm'
#dem=DEM()
#eprint(dem.get_elevation(3, 50))
