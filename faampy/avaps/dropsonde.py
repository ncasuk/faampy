#!/usr/bin/python

'''
Created on 19 May 2010

@author: axel
'''

import datetime
import matplotlib
import matplotlib.pyplot as plt
import netCDF4
import numpy as np
import os
import re
import sys
import tempfile
import zipfile
import time

#from faampy._3rdparty.haversine import points2distance, recalculate_coordinate

from haversine import points2distance, recalculate_coordinate

_DROPSONDE_ICON = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\x00\x00 \x08\x03\x00\x00\x00D\xa4\x8a\xc6\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00\x00\x003PLTE@\x00\x00\t\x06\x03I\x17\x182.*{&)bICFPc\xa99=\xcd28wP7\xe5_`\xaa{Zt\x97\xc8\xa1\x92\x93\xd7\x86\x82\xf7\xb2\xae\xd8\xcf\xd0o\x99\xb5\xad\x00\x00\x00\x01tRNS\x00@\xe6\xd8f\x00\x00\x00\x01bKGD\x00\x88\x05\x1dH\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x07tIME\x07\xda\n\x05\t\x0e \xa8#K\xb3\x00\x00\x00\xe5IDAT8\xcb\xa5\x92\xc1b\xc4 \x08D\x1d\x81\x88\xa4\xa8\xff\xff\xb5\x8b\xb9\xb4\xdb\x86\xf4\xb0\x1c\xbc\xccs\x98I,\xe5m\x18\x95[\xab(w#\x8a\xc6\x18\xc3\xcc\x82\xf9\x03\xd5\xb5\xe2r \xd56\x81\xfe\x8e\x88\xa9\x1a+W\xe6\xc6\x9b0\x0e\xb39\xe7\x0f\x07SkZyg\x08*\x0e\xc4\x1e\xf9\x06\x94Uu\xef\x0e9|b~\xa7\x08\xddj\xd5\x06\xde\x0c\xdf4\xc1\x0eo\xd0\xba\xe7\xbe\xe8\x1c\x83m\xb4L\x8ei\x91{"\x95K!\x9b\xfa _A\xcag\xfa\xbf\xc0\xfa\xc4`\x01 B\xde\x91B~\x04.\xfd\x198\x8e\r\xa4\xba\xf4.TS\x00\xd4\xcfM +Jr\x06@\x90L\xef}\x03\xe9\x02\xa1K\x17Pjp\x06 O\x0f\xa1x\x17\x81g_\xf9\xab,\x97\xa8\x90U\\\xcb\x9d\x8e\xb5\x8e\xfb\xeb\x0e\x12w\xc0\xb3\x84\x88\x8aN\xf9\x82\xb0p\xd9?)\x01^\xa0$\x07L\x0c\x13\x1c\x17\x00\x00\x00\x00IEND\xaeB`\x82'

_KML_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
      <kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/
kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
      <Folder>
          <name>Dropsonde</name>
            <open>0</open>
"""

_KML_PLACEMARK = """<Placemark>
    <name>%s</name>
    <description>%s</description>
    <Style id="dropsonde">
      <IconStyle>
        <Icon>
          <href>icons/dropsonde_32x32.png</href>
        </Icon>
      </IconStyle>
      <LineStyle>
        <color>5f3f3f3f</color>
        <width>3</width>
      </LineStyle>
      <PolyStyle>
        <color>5f3f3f3f</color>
        <fill>1</fill>
        <outline>0</outline>
      </PolyStyle>
    </Style>
    <MultiGeometry>
"""

_KML_POINT = """<Point>
        <altitudeMode>absolute</altitudeMode>
        <coordinates>
          %f,%f,%f
        </coordinates>
      </Point>"""

_KML_LINESTRING = """<LineString>
        <extrude>1</extrude>
        <tessellate>1</tessellate>
        <altitudeMode>absolute</altitudeMode>
        <coordinates>
          %s
        </coordinates>
        </LineString>
    </MultiGeometry>
  </Placemark>
"""


_KML_FOOTER = """
</Folder>
</kml>
"""


class Dropsonde(object):
    """Class that processes the dropsonde files. It's main purpose
    at the moment is to create a kmz-file, that is viewable in googleearth."""

    def __init__(self):
        self.kmz_filename = None
        self.kmz_path = None
        #creates directory structure for the kmz
        self.kmz_tmp_directory = tempfile.mkdtemp()
        os.mkdir(os.path.join(self.kmz_tmp_directory, 'icons'))
        os.mkdir(os.path.join(self.kmz_tmp_directory, 'figures'))
        icon = open(os.path.join(self.kmz_tmp_directory, 'icons', 'dropsonde_32x32.png'), 'wb')
        icon.write(_DROPSONDE_ICON)
        icon.close()

    def __decdeg2dms__(self, dd):
        """converts degree representation of lon/lat to decimal"""
        mnt,sec = divmod(dd * 3600, 60)
        deg,mnt = divmod(mnt, 60)
        return deg,mnt,sec

    def __zip__(self):
        files4zipping = []
        for root, subFolders, files in os.walk(self.kmz_tmp_directory):
            for file in files:
                files4zipping.append(os.path.join(root,file))
        #if not self.kmz_file:
        #    self.setOutputfile()
        outfile = os.path.join(self.kmz_path, self.kmz_filename)
        zip = zipfile.ZipFile(outfile, mode='w')
        for file in files4zipping:
            zipname = file[len(self.kmz_tmp_directory) + (len(os.sep)):]
            zip.write(file, zipname)

    def close(self):
        self.ds.close()

    def set_outpath(self, path):
        if os.path.exists(path):
            self.kmz_path = path
        else:
            os.mkdir(path)
            self.kmz_path = path

    def process(self):
        self.kml = _KML_HEADER
        for ncfile in self.FileList:
            self.read(ncfile)
            self.calc_drift()
            self.create_figure()
            self.create_kml()
            self.close()
        self.kml += _KML_FOOTER
        self.write_kmz()
        self.__zip__()

    def read(self, file):
        """Wrapper for the netcdf or text file read functions"""
        self.kmz_filename = os.path.splitext(os.path.basename(file))[0] + '.kmz'
        if os.path.splitext(file)[1] == '.nc':
            self.__read_netcdf__(file)
        else:
            self.__read_txt__(file)

    def __read_txt__(self, txtfile):
        #open the netcdf file
        f = open(txtfile, 'r')
        data = f.readlines()
        self.lat_raw, self.lon_raw, self.alt_raw = [],[], []
        self.alt = []
        self.press, self.rh_raw,  self.wspd_raw,  self.wdir_raw,  self.dz,  self.sat_num = [], [], [], [], [], []
        self.theta_raw,  self.gps_alt = [], []
        self.id=''
        self.launch_time=''
        self.project_name=''
        self.mission_id=''

        for line in data:
            if line.startswith('AVAPS-T'):
                if 'LAU' in line:
                    self.id = line.split()[2]
                elif 'Launch Time' in line:
                    self.launch_time = line[45:].strip()
                elif 'Project Name' in line:
                    self.project_name=line.split(':')[1].split(',')[0].strip()
                    self.mission_id=line.split(':')[1].split(',')[1].strip()
                elif ((self.id == '') and (line.split()[1] == 'END')):
                    self.id = line.split()[2]
            elif line.startswith('AVAPS-D'):
                self.lon_raw.append(float(line.split()[11]))
                self.lat_raw.append(float(line.split()[12]))
                self.alt_raw.append(float(line.split()[19]))

                R = 8.3114472 # gas constant
                T = float(line.split()[5]) + 273.15# current temperature in K
                cp = 1.0038 # heat capacity of air
                P = float(line.split()[5])
                P_0 = 1000.0
                self.theta_raw.append(T * (P/P_0)**(R/cp))
                self.press.append(float(line.split()[5]))
                self.rh_raw.append(float(line.split()[7]))
                self.wspd_raw.append(float(line.split()[9]))
                self.wdir_raw.append(float(line.split()[8]))
                self.dz.append(float(line.split()[10]))
                self.sat_num.append(float(line.split()[14]))
                self.alt.append(float(line.split()[12]))

        # create empty lists for latitude, longitude, altitude
        self.lat = []; self.lon = []; self.alt =[]

        for i in range(len(self.lat_raw)):
            if not (-999 in [self.lat_raw[i],self.lon_raw[i], self.alt_raw[i]]):
                if not (99999 in [self.lat_raw[i],self.lon_raw[i], self.alt_raw[i]]):
                    if not (99 in [self.lat_raw[i],self.lon_raw[i], self.alt_raw[i]]):
                        self.lat.append(self.lat_raw[i])
                        self.lon.append(self.lon_raw[i])
                        self.alt.append(self.alt_raw[i])

    def __read_netcdf__(self, ncfile):

        # open the netcdf file
        self.ds = netCDF4.Dataset(ncfile, 'r')

        self.id = self.ds.SoundingDescription.split()[1]
        self.launch_time = datetime.datetime.strptime(self.ds.variables['base_time'].string, '%a %b %d %H:%M:%S %Y')

        # create empty lists for latitude, longitude, alitude
        self.lat = []; self.lon = []; self.alt =[]

        self.lat_raw = list(self.ds.variables['lat'][:])
        self.lon_raw = list(self.ds.variables['lon'][:])
        self.alt_raw = list(self.ds.variables['alt'][:])
        self.theta_raw = list(self.ds.variables['theta'][:])
        self.rh_raw = list(self.ds.variables['rh'][:])
        wspd_raw = list(self.ds.variables['wspd'][:])
        wdir_raw = list(self.ds.variables['wdir'][:])

        for i in range(len(self.lat_raw)):
            if self.lat_raw[i] != -999 and self.lon_raw[i] != -999 and self.alt_raw[i] != -999:
                self.lat.append(self.lat_raw[i])
                self.lon.append(self.lon_raw[i])
                self.alt.append(self.alt_raw[i])

    def __get_fid__(self):
        """get the flight number from the netcdf global attributes"""
        fid = None
        pattern = '[b,B]\d{3}'
        #check several attributes to make sure that we get the fid
        vars = [self.ds.SoundingDescription,]

        for var in vars:
            fid = re.search('[b,B]\d{3}', var)
            if fid:
                result = fid.group().lower()
                return result

    def create_kml(self):
        kml = ""
        fall_time = max(self.ds.variables['time'][:]) - min(self.ds.variables['time'][:])

        self.kml_name = '%s-%s' % (self.__get_fid__(),
                                   re.split('[_,.]', self.ds.SoundingDescription)[1])

        description = "<![CDATA[<h4>" +self.launch_time.strftime('%Y-%m-%d %H:%M:%S')+"</h4><h3>Summary</h3>" + \
                      """<p><b>First time stamp:</b> """ + \
                      time.strftime('%H:%M:%S', time.gmtime(min(self.ds.variables['time'][:]))) + \
                      """<br><b>Last time stamp:</b> """ + \
                      time.strftime('%H:%M:%S', time.gmtime(max(self.ds.variables['time'][:]))) + \
                      """<br><b>Fall time:</b> """ + \
                      '%im%is (%isecs)' % (fall_time//60, fall_time%60, fall_time) + \
                      "<br><b>Drift:</b>  " + str(int(round(self.drift_tot * 1000))) + "m " + \
                      "(NS: " + str(int(round(self.drift_ns * 1000))) + "m, EW: " + str(int(round(self.drift_ew * 1000))) + "m)" + \
                      "</p> <h3>Profiles</h3>" + \
                      "<img src=" + \
                      '"' + 'figures/' + os.path.basename(self.fig_filename) + '">]]>'
        lat_lon_alt = ""
        for i in range(len(self.lat)):
            lat_lon_alt += '%f,%f,%f\n' % (float(self.lon[i]),
                                           float(self.lat[i]),
                                           float(self.alt[i]))

        # point feature; location of the icon
        pt_lat, pt_lon, pt_alt = float(self.lat[-1]), float(self.lon[-1]), float(self.alt[-1])

        kml += _KML_PLACEMARK % (self.kml_name, description)
        kml += _KML_POINT % (pt_lon, pt_lat, pt_alt)
        kml += _KML_LINESTRING % (lat_lon_alt)
        self.kml = kml

    def create_figure(self):

        params = {'axes.labelsize': 9,
                  'font.size': 9,
                  'xtick.labelsize': 8,
                  'ytick.labelsize': 8,
                  'text.usetex': False}

        plt.clf()
        plt.rcParams.update(params)

        ymin = 0; ymax = 10

        line_style = 'b-'
        line_width = '2'

        plt.figure(1, figsize=(5,4), dpi=120)

        font = matplotlib.font_manager.FontProperties()
        #font.set_size(7)

        alt = self.ds.variables['alt'][:].data / 1000.0   #convert height to km
        theta = self.ds.variables['theta'][:].data - 273.15
        dp = self.ds.variables['dp'][:].data
        tdry = self.ds.variables['tdry'][:].data
        wspd = self.ds.variables['wspd'][:].data
        wdir = self.ds.variables['wdir'][:].data
        u = self.ds.variables['u_wind'][:].data
        v = self.ds.variables['v_wind'][:].data

        plt.subplots_adjust(hspace = 0.25, wspace = 0.15)


        # --- 1st plot ---

        plt.subplot(1,2,1)
        ix = np.where((tdry != -999) & (alt > 0))
        plt.plot(tdry[ix], alt[ix], '-', lw=3, label='tdry')
        ix = np.where((dp != -999) & (alt > 0))
        plt.plot(dp[ix], alt[ix], '-', lw=3, label='dp')
        ix = np.where((theta > -100) & (alt > 0))
        plt.plot(theta[ix], alt[ix], '-', lw=3, label='theta')
        plt.grid()
        plt.xlabel('temperature (C)')
        plt.legend(loc='upper right')
        plt.ylabel('height (km)')

        # --- 2nd plot ---

        plt.subplot(1,2,2)
        ix = np.where((wspd[:] > 0) & (alt > 0))
        p1, = plt.plot(wspd[:][ix], alt[ix], '-', color='blue', lw=3, label='wspd')
        plt.xlabel('wspd (ms-1)')
        plt.twiny()
        plt.plot(wdir[:][ix], alt[ix], '-', color='green', lw=3, label='wdir')
        plt.xlim(0,360)
        plt.xlabel('wdir (deg)')
        plt.ylabel('altitude (m)')
        plt.legend()
        #plt.tight_layout()
        self.fig_filename = os.path.join(self.kmz_tmp_directory, 'figures', self.id + '.png')
        plt.savefig(self.fig_filename)
        plt.close()

    def write_kml(self):
        f = open(os.path.join(self.kmz_tmp_directory, 'doc.kml'), 'w')
        f.write(self.kml)
        f.close()

    def calc_drift(self):
        start_point = (self.__decdeg2dms__(self.lon[-1]), self.__decdeg2dms__(self.lat[-1]))
        end_point = (self.__decdeg2dms__(self.lon[0]), self.__decdeg2dms__(self.lat[0]))
        #calculate north-south drift
        self.drift_ns = points2distance((self.__decdeg2dms__(self.lon[-1]), self.__decdeg2dms__(self.lat[-1])),
                                    (self.__decdeg2dms__(self.lon[-1]), self.__decdeg2dms__(self.lat[ 0])))
        #calculate east-west drift
        self.drift_ew = points2distance((self.__decdeg2dms__(self.lon[-1]), self.__decdeg2dms__(self.lat[-1])),
                                    (self.__decdeg2dms__(self.lon[ 0]), self.__decdeg2dms__(self.lat[-1])))
        #calculate total drift
        self.drift_tot = points2distance(start_point, end_point)


def process(iput, opath):
    if os.path.isdir(iput):
        iput_file_list = []
        for root, subFolders, files in os.walk(iput):
            for f in files:
                #print(f)
                #if f.startswith('faam-dropsonde'):
                if re.match('faam-dropsonde.*proc.nc', f):
                    iput_file_list.append(os.path.join(root, f))
    else:
        iput_file_list = [iput,]

    for ifile in iput_file_list:
        try:
            d = Dropsonde()
            d.read(ifile)
            d.set_outpath(opath)
            d.calc_drift()
            d.create_figure()
            d.create_kml()
            d.write_kml()
            d.__zip__()
        except:
            pass

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Creates a kmz file from dropsonde data.")
    parser.add_argument('--outpath', action="store", type=str, default=os.environ['HOME'], help='Directory where the kmz file will be stored. Default: $HOME.')
    parser.add_argument('input', action="store", type=str, help='Individual dropsonde file or folder which contains dropsonde data.')
    args = parser.parse_args()
    process(args.input, args.outpath)
    sys.stdout.write('Done ...\n')


#ifile = '/home/axel/Dropbox/campaigns/wintex2016/b949-mar-09/faam-dropsonde_faam_20160309125648_r0_b949_raw.nc'
#ifile = '/home/axel/b949_avaps/D20160309_125648QC.nc'
#d = Dropsonde()
#d.read(ifile)
#d.set_outpath('/home/axel/')
#d.calc_drift()
#d.create_figure()
#d.create_kml()
#d.write_kml()
#d.__zip__()
