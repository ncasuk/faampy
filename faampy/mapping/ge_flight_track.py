#!/usr/bin/python

"""
Creates a kml-file viewable in google-earth from the core NetCDF data file.


"""

import datetime
import kmldom
import kmlbase
import netCDF4
import numpy as np
import os
import pickle
import re
import sys
import time

try:
    from rdp import rdp
except:
    from faampy._3rdparty.rdp import rdp


_KML_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Folder>
    <name>%s-Flight-Track</name>
        <description>Flight-Track</description>
        <open>0</open>
        <description>
           %s %s
        </description>
"""

def set_rawlatlonalt_from_netcdf_safire(self, ifile):
        """
        This function works for the Safire netcdf files.

        """

        if isinstance(ifile, netCDF4.Dataset):
            ds = ifile
        else:
            ds = netCDF4.Dataset(ifile, 'r')

        self.BaseTime = datetime.datetime.strptime(str.strip(str(ds.variables['time'].units)), 'seconds since %Y-%m-%d %H:%M:%S UTC')

        self.FlightID = (self.BaseTime+datetime.timedelta(seconds=ds.variables['time'][:][0])).strftime('%Y%m%d')

        lon_gin = ds.variables['pos_lon_aipov_1'][10:-10]
        lon_gin_flag = lon_gin*0
        lat_gin = ds.variables['pos_lat_aipov_1'][10:-10]
        lat_gin_flag = lat_gin*0
        alt_gin = ds.variables['alt_aipov_1'][10:-10]
        alt_gin_flag = alt_gin*0

        secs_past_BaseTime = list(ds.variables['time'][:].ravel())
        timestamp = [self.BaseTime+datetime.timedelta(seconds=int(sec)) for sec in secs_past_BaseTime]
        self.BaseTime = timestamp[0]

        self.raw_lon = lon_gin
        self.raw_lat = lat_gin
        self.raw_alt = alt_gin
        self.raw_time = timestamp
        self.lon = long_gin
        self.lat = lat_gin
        self.alt = alt_gin
        self.time = timestamp


class TrackPoint(object):

    def __init__(self, ts, lon, lat, alt):
        self.timestamp = ts
        self.longitude = lon
        self.latitude = lat
        self.altitude = alt


class FlightTrack(object):

    def __init__(self):
        self.lon = []
        self.lat = []
        self.alt = []
        self.timestamp = []
        self.FlightID = ''
        self.BaseTime = None
        self.TrackPoints = []

    def __extract_data__(self, ds, par1, par2):
        """Data extractor"""
        quality = 0.0
        if par1 in ds.variables.keys():
            par_name = par1
        elif par2 in ds.variables.keys():
            par_name = par2
        else:
            return(None, None, 0)
        if par_name + '_FLAG' in ds.variables.keys():
            flag_name = par_name + '_FLAG'
        elif par_name + 'FLAG' in ds.variables.keys():
            flag_name = par_name + 'FLAG'
        else:
            flag_name = None

        data = ds.variables[par_name][:,0].ravel()
        try:
            flag = ds.variables[flag_name][:,0].data.ravel()
        except:
            flag = ds.variables[flag_name][:,0].ravel()
        quality = float(len(np.where(flag == 0.0)[0])) / float(len(flag))
        return (data, flag, quality)

    def set_rawlatlonalt_from_netcdf(self, ifile):
        """
        The position of the aircraft is measured by two independent systems:

          (1) GIN, which produces 32Hz data
          (2) XR5 system which produces 1Hz data

        We are checking the quality of both systems looking at every parameter
        (lon, lat, alt, time_stamp) using the flag from the netCDF file and
        select the one parameter with better quality.
        """

        if isinstance(ifile, netCDF4.Dataset):
            ds = ifile
        else:
            ds = netCDF4.Dataset(ifile, 'r')

        try:
            self.FlightID = re.findall('[bBcC]\d{3}', ds.title)[0]
        except:
            self.FlightID = re.findall('[bBcC]\d{3}', ds.Title)[0]

        try:
            self.BaseTime = datetime.datetime.strptime(str.strip(str(ds.variables['Time'].long_name)), 'time of measurement since %Y-%m-%d %H:%M:%S +0000')
        except:
            self.BaseTime = datetime.datetime.strptime(str.strip(str(ds.variables['Time'].units)), 'seconds since %Y-%m-%d %H:%M:%S +0000')
        finally:
            pass
        lon_gps, lon_gps_flag, lat_gps, lat_gps_flag, alt_gps, alt_gps_flag = (None, None, None, None, None, None)
        lon_gin, lon_gin_flag, lat_gin, lat_gin_flag, alt_gin, alt_gin_flag = (None, None, None, None, None, None)
        secs_past_BaseTime = list(ds.variables['Time'][:].ravel())
        timestamp = []
        for sec in secs_past_BaseTime:
            timestamp.append(self.BaseTime+datetime.timedelta(seconds=int(sec)))

        # Data from the XR5 GPS-System
        lon_gps, lon_gps_flag, lon_gps_q = self.__extract_data__(ds, 'LON_GPS', 'PARA0581')
        lat_gps, lat_gps_flag, lat_gps_q = self.__extract_data__(ds, 'LAT_GPS', 'PARA0730')
        alt_gps, alt_gps_flag, alt_gps_q = self.__extract_data__(ds, 'GPS_ALT', 'PARA0582')

        # Data from the GIN-System
        lon_gin, lon_gin_flag, lon_gin_q = self.__extract_data__(ds, 'LON_GIN', 'PARA0611')
        lat_gin, lat_gin_flag, lat_gin_q = self.__extract_data__(ds, 'LAT_GIN', 'PARA0610')
        alt_gin, alt_gin_flag, alt_gin_q = self.__extract_data__(ds, 'ALT_GIN', 'PARA0612')

        if lon_gps_q > lon_gin_q:
            lons = lon_gps[:]
            lons_flag = lon_gps_flag[:]
        else:
            lons = lon_gin[:]
            lons_flag = lon_gin_flag[:]

        if lat_gps_q > lat_gin_q:
            lats = lat_gps[:]
            lats_flag = lat_gps_flag[:]
        else:
            lats = lat_gin[:]
            lats_flag = lat_gin_flag[:]

        if alt_gps_q > alt_gin_q:
            alts = alt_gps[:]
            alts_flag = alt_gps_flag[:]
        else:
            alts = alt_gin[:]
            alts_flag = alt_gin_flag[:]

        if list(lons) and list(lats):
            lons_diff = abs(abs(lons) - abs(np.median(lons)))
            lats_diff = abs(abs(lats) - abs(np.median(lats)))

            ix = np.concatenate((np.where(lons == 0.0)[0],
                                 np.where(lons == -9999.0)[0],
                                 np.where(lats == 0.0)[0],
                                 np.where(alts <= 0.0)[0],
                                 np.where(lats == -9999.0)[0],
                                 np.where(lons_flag != 0)[0],
                                 np.where(lats_flag != 0)[0],
                                 np.where(alts_flag != 0)[0]))
            ix = np.unique(ix)

            good_ix = set(range(len(lons))) - set(ix)
            good_ix = np.array(list(good_ix))

            if len(good_ix):
                lons = list(np.array(lons)[good_ix])
                lats = list(np.array(lats)[good_ix])
                alts = list(np.array(alts)[good_ix])
                timestamp = list(np.array(timestamp)[good_ix])

            self.raw_lon = lons
            self.raw_lat = lats
            self.raw_alt = alts
            self.raw_time = timestamp
            if not self.lon:
                self.lon, self.lat, self.alt, self.timestamp = (lons, lats, alts, timestamp)
            if not isinstance(file, netCDF4.Dataset):
                ds.close()

    def createFromDump(self, infile):
        if os.path.exists(infile):
            file = open(infile, 'r')
            obj = pickle.load(file)
            file.close()

            self.id = obj['id']
            self.timestamp = datetime.datetime.strptime(obj['timestamp'], '%a %b %d %H:%M:%S %Y')
            self.lon = obj['lons']
            self.lat = obj['lats']
            self.alt = obj['alts']
            self.time = obj['time']
            #self.source = obj['source']
        else:
            sys.stdout.write("File does not exist!")

    def simplifyOLD(self, error=None, distance=None, timestep=None):
        """uses the simplify options from gpsbabel"""
        if not error:
            error = '0.2k'
        if not distance:
            distance = '10k'
        if not timestep:
            timestep = 120
        # crosstracked track
        track_ct = gpsbabel.GPSBabel()
        track_ct.procRoutes = True
        track_ct.setInGpx(self.gpxd)
        track_ct.addFilter('simplify', {"crosstrack": None, 'error': error})
        track_ct.captureStdOut()
        (retcode, self.gpxd_crosstracked) = track_ct.execCmd()

        self.lon_tmp, self.lat_tmp, self.alt_tmp, self.timestamp_tmp = ([], [], [], [])
        for rte in self.gpxd_crosstracked.rtes:
            for pt in rte.rtepts:
                self.lon_tmp.append(pt.lon)
                self.lat_tmp.append(pt.lat)
                self.alt_tmp.append(pt.ele)
                self.timestamp_tmp.append(pt.time)

        track_ip = gpsbabel.GPSBabel()
        track_ip.procRoutes = True
        track_ip.setInGpx(self.gpxd)
        track_ip.addFilter('position', {'distance': '50m'})
        track_ip.captureStdOut()
        (retcode, self.gpxd_interpolated) = track_ip.execCmd()

        for rte in self.gpxd_interpolated.rtes:
            for pt in rte.rtepts:
                if (pt.time.hour * 3600 + pt.time.minute * 60 + pt.time.second) % timestep == 0:
                    self.lon_tmp.append(pt.lon)
                    self.lat_tmp.append(pt.lat)
                    self.alt_tmp.append(pt.ele)
                    self.timestamp_tmp.append(pt.time)

        timesort = []
        for tstamp in self.timestamp_tmp:
            timesort.append(time.mktime(tstamp.timetuple()))

        self.lon, self.lat, self.alt, self.timestamp = ([], [], [], [])
        ix = list(index for index, item in sorted(enumerate(timesort), key=lambda item: item[1]))

        for i in ix:
            self.lon.append(self.lon_tmp[i])
            self.lat.append(self.lat_tmp[i])
            self.alt.append(self.alt_tmp[i])
            self.timestamp.append(self.timestamp_tmp[i])
        return (self.lon, self.lat)

    def simplify(self, epsilon=0.1, timestep=120):
        """uses the simplify options from gpsbabel"""

        from rdp import rdp
        #coords = np.vstack((self.lon, self.lat, self.alt, self.timestamp))
        coords = np.vstack((self.lon, self.lat, self.alt)).T
        mask1 = rdp(coords, algo='iter', return_mask=True, epsilon=epsilon)

        unixtime = [int(time.mktime(ts.timetuple())) for ts in self.timestamp]
        rest = [u % timestep for u in unixtime]
        mask2 = []
        for r in rest:
            if r == 0:
                mask2.append(True)
            else:
                mask2.append(False)

        mask = mask1+mask2

        ix = np.where(mask == True)[0]
        print(len(ix))


        _lon = []
        _lat = []
        _alt = []
        _timestamp = []
        for i in ix:
            _lon.append(self.lon[i])
            _lat.append(self.lat[i])
            _alt.append(self.alt[i])
            _timestamp.append(self.timestamp[i])
        self.lon = _lon
        self.lat = _lat
        self.alt = _alt
        self.timestamp = _timestamp
        return (self.lon, self.lat)

    def dump(self, dumpfile=None):
        """Dumps the """

        if not dumpfile:
            dumpfile = 'flight_track_' + '%s.pydat' % (int(self.FlightID))
            f = open(os.path.join(os.environ['HOME'], dumpfile), 'w')
        else:
            f = open(dumpfile, 'w')

        obj4dump = {}
        obj4dump['timestamp'] = time.asctime()
        obj4dump['id'] = self.FlightID
        obj4dump['time'] = self.timestamp
        obj4dump['lons'] = self.lon
        obj4dump['lats'] = self.lat
        obj4dump['alts'] = self.alt
        #obj4dump['source'] = self.source

        pickle.dump(obj4dump, file)
        f.close()

    def create_kml_profile(self, color=None):

        if not color: color = 'black'

        factory = kmldom.KmlFactory_GetFactory()

        #coordinates object with dropsonde coordinates
        coordinates = factory.CreateCoordinates()

        for i in range(len(self.lat)):
            coordinates.add_latlngalt(float(self.lat[i]), float(self.lon[i]), float(self.alt[i]))

        # point feature
        n = coordinates.get_coordinates_array_size()-1
        pt_lat = coordinates.get_coordinates_array_at(n).get_latitude()
        pt_lon = coordinates.get_coordinates_array_at(n).get_longitude()
        pt_alt = coordinates.get_coordinates_array_at(n).get_altitude()
        pt_cor = factory.CreateCoordinates()
        pt_cor.add_latlngalt(pt_lat, pt_lon, pt_alt)
        pt = factory.CreatePoint()
        pt.set_coordinates(pt_cor)
        pt.set_altitudemode(2)    #set absolute mode

        # LineString which represents the flight track
        ls = factory.CreateLineString()
        ls.set_coordinates(coordinates)
        ls.set_extrude(True)
        ls.set_tessellate(True)
        ls.set_altitudemode(2)    #set absolute mode

        #c ombine point and linestring into a multi geometry
        mg = factory.CreateMultiGeometry()
        mg.add_geometry(pt)
        mg.add_geometry(ls)

        try:
            #coltup = webcolor.name_to_rgb(color)
            coltup = eval(color)
        except:
            pass

        try:
            coltup = webcolor.name_to_rgb(color)
        except:
            pass

        coltup = (0, 0, 0)
        line_color = kmlbase.Color32()

        # linestyle
        line_color.set_red(coltup[0])
        line_color.set_green(coltup[1])
        line_color.set_blue(coltup[2])
        line_color.set_alpha(75)
        # linestyle
        linestyle = factory.CreateLineStyle()
        linestyle.set_color(line_color)
        linestyle.set_width(3)
        # polystyle; necessary to make area between extrudes transparent
        polystyle = factory.CreatePolyStyle()
        polycolor = line_color
        polycolor.set_alpha(50)
        polystyle.set_color(polycolor)
        polystyle.set_fill(True)
        polystyle.set_outline(False)

        style = factory.CreateStyle()
        style.set_linestyle(linestyle)
        style.set_polystyle(polystyle)

        self.placemark = factory.CreatePlacemark()
        self.placemark.set_geometry(mg)
        self.placemark.set_name(str(self.FlightID))
        self.placemark.set_styleselector(style)

        self.kml_profile = kmldom.SerializePretty(self.placemark)

    def create_kml_points(self):
        factory = kmldom.KmlFactory_GetFactory()

        #coordinates object with dropsonde coordinates
        coordinates = factory.CreateCoordinates()

        self.points = []

        for i in range(len(self.lat)):
            pt_cor = factory.CreateCoordinates()
            pt_cor.add_latlngalt(float(self.lat[i]), float(self.lon[i]), float(self.alt[i]))
            pt = factory.CreatePoint()
            pt.set_coordinates(pt_cor)
            pt.set_altitudemode(2)    #set absolute mode

            point = factory.CreatePlacemark()
            point.set_geometry(pt)

            label = self.FlightID + ': ' + self.timestamp[i].strftime('%H:%M:%S')
            point.set_name(str(label))

            self.points.append(point)

        self.kml_points = ''
        for p in self.points:
            self.kml_points = self.kml_points + kmldom.SerializePretty(p)

    def write_kml(self, outfile=None):

        f = open(outfile, 'w')
        f.write(_KML_HEADER % (self.FlightID+'-'+self.BaseTime.strftime('%Y%m%d'),
                            self.BaseTime.strftime('%Y-%m-%d'),
                            self.FlightID))
        f.write(self.kml_profile)
        f.write("<Folder><open>0</open>")
        f.write("<name>Waypoints</name>")
        f.write(self.kml_points)
        f.write("</Folder>")
        f.write("</Folder></kml>")
        f.close()

    def process(self, infile, outfile=None):
        self.set_rawlatlonalt_from_netcdf(infile)
        #self.simplify()
        self.create_kml_profile()
        self.create_kml_points()
        self.write_kml(outfile)


def _argparser():
    import argparse
    sys.argv.insert(0, 'faampy ge_flight_track')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('infile',
                        action="store", type=str, help='FAAM core netCDF filename')
    parser.add_argument('outfile',
                        action="store",
                        type=str, help='output kml filename')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()
    ft = FlightTrack()
    if 'safire' in args.infile:
        from types import MethodType
        setattr(ft, 'set_rawlatlonalt_from_netcdf', MethodType(set_rawlatlonalt_from_netcdf_safire, ft, ft.__class__))
    ft.process(args.infile, args.outfile)

if __name__ == '__main__':
    main()
