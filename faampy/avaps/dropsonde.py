#!/usr/bin/python

"""
Creates a kmz file from dropsonde data, that can be opened in google-earth.

The falling path is shown as a profile in google earth and the profiles of
temperature, humidity, wind speed and wind direction are visible in a ballon,
when clicked on the Sonde icon.

"""

import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import netCDF4
import numpy as np
import os
import re
import shutil
import sys
import tempfile
import zipfile
import time

import faampy
from faampy._3rdparty.haversine import points2distance


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
    """
    Class that processes the dropsonde files. Its main purpose
    at the moment is to create a kmz-file, that is viewable in googleearth.
    """

    def __init__(self):
        self.kmz_filename = None
        self.kmz_path = None
        # creates directory structure for the kmz
        self.kmz_tmp_directory = tempfile.mkdtemp()
        os.mkdir(os.path.join(self.kmz_tmp_directory, 'icons'))
        os.mkdir(os.path.join(self.kmz_tmp_directory, 'figures'))
        # copy the dropsonde icon
        src = os.path.join(os.path.dirname(faampy.__file__), '..',
                           'files', 'icons', 'dropsonde_32x32.png')
        dst = os.path.join(self.kmz_tmp_directory, 'icons',
                           'dropsonde_32x32.png')
        shutil.copy(src, dst)

    def __decdeg2dms__(self, dd):
        """
        converts degree representation of lon/lat to decimal
        """
        mnt, sec = divmod(dd * 3600, 60)
        deg, mnt = divmod(mnt, 60)
        return deg, mnt, sec

    def __zip__(self):
        files4zipping = []
        for root, subFolders, files in os.walk(self.kmz_tmp_directory):
            for f in files:
                files4zipping.append(os.path.join(root, f))
        outfile = os.path.join(self.kmz_path, self.kmz_filename)
        zip = zipfile.ZipFile(outfile, mode='w')
        for f in files4zipping:
            zipname = f[len(self.kmz_tmp_directory) + (len(os.sep)):]
            zip.write(f, zipname)

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
        """
        Read the data from the txt data files.
        """
        # open the text data file
        f = open(txtfile, 'r')
        data = f.readlines()
        self.lat_raw = []
        self.lon_raw = []
        self.alt_raw = []
        self.alt = []
        self.press = []
        self.rh_raw = []
        self.wspd_raw = []
        self.wdir_raw = []
        self.dz = []
        self.sat_num = []
        self.temp_raw = []
        self.theta_raw = []
        self.gps_alt = []
        self.id = ''
        self.launch_time = ''
        self.project_name = ''
        self.mission_id = ''

        for line in data:
            if line.startswith('AVAPS-T'):
                if 'LAU' in line:
                    self.id = line.split()[2]
                elif 'Launch Time' in line:
                    self.launch_time = line[45:].strip()
                elif 'Project Name' in line:
                    self.project_name = line.split(':')[1].split(',')[0].strip()
                    self.mission_id = line.split(':')[1].split(',')[1].strip()
                elif ((self.id == '') and (line.split()[1] == 'END')):
                    self.id = line.split()[2]
            elif line.startswith('AVAPS-D'):
                self.lon_raw.append(float(line.split()[11]))
                self.lat_raw.append(float(line.split()[12]))
                self.alt_raw.append(float(line.split()[19]))

                R = 8.3114472  # gas constant
                T = float(line.split()[5]) + 273.15  # current temperature in K
                cp = 1.0038    # heat capacity of air
                P = float(line.split()[5])
                P_0 = 1000.0
                self.theta_raw.append(T * (P/P_0)**(R/cp))
                self.press.append(float(line.split()[5]))
                self.temp_raw.append(float(line.split()[6]))
                self.rh_raw.append(float(line.split()[7]))
                self.wspd_raw.append(float(line.split()[9]))
                self.wdir_raw.append(float(line.split()[8]))
                self.dz.append(float(line.split()[10]))
                self.sat_num.append(float(line.split()[14]))
                self.alt.append(float(line.split()[12]))

        # create empty lists for latitude, longitude, altitude
        self.lat = []
        self.lon = []
        self.alt = []

        for i in range(len(self.lat_raw)):
            if not (-999 in [self.lat_raw[i],self.lon_raw[i], self.alt_raw[i]]):
                if not (99999 in [self.lat_raw[i],self.lon_raw[i], self.alt_raw[i]]):
                    if not (99 in [self.lat_raw[i],self.lon_raw[i], self.alt_raw[i]]):
                        self.lat.append(self.lat_raw[i])
                        self.lon.append(self.lon_raw[i])
                        self.alt.append(self.alt_raw[i])

    def __read_netcdf__(self, ncfile):
        """
        Read in data from the netCDF.

        :param str ncfile: netCDF filename to be red
        """
        # open the netcdf file
        self.ds = netCDF4.Dataset(ncfile, 'r')

        self.id = self.ds.SoundingDescription.split()[1]
        self.launch_time = datetime.datetime.strptime(self.ds.variables['base_time'].string, '%a %b %d %H:%M:%S %Y')

        # create empty lists for latitude, longitude, alitude
        self.lat = []
        self.lon = []
        self.alt =[]

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
        """
        Get the flight number from the netcdf global attributes.
        """
        fid = None
        # check several attributes to make sure that we get the fid
        vars = [self.ds.SoundingDescription,]

        for var in vars:
            fid = re.search('[bBcC]\d{3}', var)
            if fid:
                result = fid.group().lower()
                return result

    def create_kml(self):
        kml = ""
        fall_time = max(self.ds.variables['time'][:]) - min(self.ds.variables['time'][:])

        self.kml_name = '%s-%s' % (self.__get_fid__(),
                                   re.split('[_,.]', self.ds.SoundingDescription)[1])

        description = "<![CDATA[<h4>" + self.launch_time.strftime('%Y-%m-%d %H:%M:%SZ')+"</h4><h3>Summary</h3>" + \
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
        pt_lat = float(self.lat[-1])
        pt_lon = float(self.lon[-1])
        pt_alt = float(self.alt[-1])

        kml += _KML_PLACEMARK % (self.kml_name, description)
        kml += _KML_POINT % (pt_lon, pt_lat, pt_alt)
        kml += _KML_LINESTRING % (lat_lon_alt)
        self.kml = kml

    def create_figure(self):

        params = {'axes.labelsize': 9,
                  'font.size': 9,
                  'xtick.labelsize': 8,
                  'ytick.labelsize': 8,
                  'figure.subplot.wspace': 0.05,
                  'text.usetex': False}

        plt.clf()
        plt.rcParams.update(params)

        fig = plt.figure(1, figsize=(10,8))

        alt = self.ds.variables['alt'][:].data / 1000.0   # convert height to km
        theta = self.ds.variables['theta'][:].data - 273.15
        dp = self.ds.variables['dp'][:].data
        tdry = self.ds.variables['tdry'][:].data
        wspd = self.ds.variables['wspd'][:].data
        wdir = self.ds.variables['wdir'][:].data
        u = self.ds.variables['u_wind'][:].data
        v = self.ds.variables['v_wind'][:].data

        fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)

        # --- 1st plot ---
        ix = np.where((tdry != -999) & (alt > 0))
        ax1.plot(tdry[ix], alt[ix], '-', lw=3, label='tdry')
        ix = np.where((dp != -999) & (alt > 0))
        ax1.plot(dp[ix], alt[ix], '-', lw=3, label='dp')
        ix = np.where((theta > -100) & (alt > 0))
        ax1.plot(theta[ix], alt[ix], '-', lw=3, label='theta')
        ax1.grid(True)
        ax1.set_xlabel('temperature (C)')
        ax1.legend(loc='upper right')
        ax1.set_ylabel('height (km)')

        # --- 2nd plot ---
        ix = np.where((wspd[:] > 0) & (alt > 0))
        p1, = ax2.plot(wspd[:][ix], alt[ix],
                       '-', color='blue', lw=3, label='wspd')
        ax2.set_xlabel('wspd (ms-1)')
        ax2.yaxis.grid(True)
        ax2_b = ax2.twiny()

        # The below snipped is necessary to avoid ugly vertical lines
        # in the figures when the wdir crosses the 360 deg mark
        _wdir = [float(wdir[ix[0][0]]), ]
        _alt = [float(alt[ix[0][0]]), ]
        for i in ix[0][1:]:
            _wdir.append(wdir[i])
            _alt.append(alt[i])
            delta = np.abs(_wdir[-1]-_wdir[-2])
            if delta > 180:
                _wdir.insert(-1, None)
                _alt.insert(-1, None)

        p2, = ax2_b.plot(_wdir, _alt, '-',
                         color='green', lw=3, label='wdir')
        ax2_b.set_xlim(0, 360)
        ax2_b.set_xlabel('wdir (deg)')
        ax2_b.set_ylabel('altitude (m)')

        lines = [p1, p2]
        labs = [l.get_label() for l in lines]
        ax2_b.legend(lines, labs, loc='upper right')

        self.fig_filename = os.path.join(self.kmz_tmp_directory,
                                         'figures', self.id + '.png')
        plt.savefig(self.fig_filename)
        fig_label = '%s: %s' % (self.__get_fid__(),
                                self.launch_time.strftime('%Y-%m-%d %H:%M:%SZ'))
        fig.text(0.05, 0.96, fig_label, va='top', ha='left', transform=fig.transFigure)
        fig.canvas.draw()
        return fig

    def write_kml(self):
        f = open(os.path.join(self.kmz_tmp_directory, 'doc.kml'), 'w')
        f.write(self.kml)
        f.close()

    def calc_drift(self):
        start_point = (self.__decdeg2dms__(self.lon[-1]),
                       self.__decdeg2dms__(self.lat[-1]))
        end_point = (self.__decdeg2dms__(self.lon[0]),
                     self.__decdeg2dms__(self.lat[0]))
        # calculate north-south drift
        self.drift_ns = points2distance((self.__decdeg2dms__(self.lon[-1]),
                                         self.__decdeg2dms__(self.lat[-1])),
                                        (self.__decdeg2dms__(self.lon[-1]),
                                         self.__decdeg2dms__(self.lat[0])))
        # calculate east-west drift
        self.drift_ew = points2distance((self.__decdeg2dms__(self.lon[-1]),
                                         self.__decdeg2dms__(self.lat[-1])),
                                        (self.__decdeg2dms__(self.lon[0]),
                                         self.__decdeg2dms__(self.lat[-1])))
        # calculate total drift
        self.drift_tot = points2distance(start_point, end_point)


def process(iput, opath):
    if os.path.isdir(iput):
        iput_file_list = []
        for root, subFolders, files in os.walk(iput):
            for f in files:
                if re.match('faam-dropsonde.*proc.nc', f):
                    iput_file_list.append(os.path.join(root, f))
        iput_file_list.sort()
    else:
        iput_file_list = [iput,]

    for ifile in iput_file_list:
        sys.stdout.write('Working on %s ...\n' % (os.path.basename(ifile),))
        try:
            d = Dropsonde()
            d.read(ifile)
            d.set_outpath(opath)
            try:
                d.calc_drift()
            except:
                pass
            d.create_figure()
            d.create_kml()
            d.write_kml()
            d.__zip__()
        except:
            pass


def _argparser():
    import argparse
    #sys.argv.insert(0, 'faampy ge_avaps')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outpath',
                        action="store", type=str,
                        default=os.path.expanduser('~'),
                        help='Directory where the kmz file will be saved to. Default: $HOME.')
    parser.add_argument('faam_dropsonde_file',
                        action="store",
                        type=str,
                        help='Individual dropsonde file or directory name which contains dropsonde data.')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()
    process(args.input, args.outpath)
    sys.stdout.write('Done ...\n')


if __name__ == '__main__':
    main()
