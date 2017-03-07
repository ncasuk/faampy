#! /usr/bin/env python
"""
More satellite track information can be found at:
  
  http://www.n2yo.com/

Popular platforms:
    
=========== ======  ====== 
Platform    Sensor  ID
=========== ======  ====== 
CALIPSO             29108
ISS         CATS    25544
TERRA       MODIS   25994
LANDSAT8            39084
SENTINEL-2A         40697
SENTINEL-3A         41335
=========== ======  ====== 

Example::

  faampy sat_tracker track --show_map "-38 35 -20 43" 39084 13-02-2017 17-02-2017 60

"""

import datetime
import ephem
import errno
import math
import numpy as np
import os
import re
import sys
import texttable
import urllib2 as urllib

import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap



def __parse_time__(date_string):
    fmt='%d-%m-%YT%H:%M:%S'
    time_datetime = None
    try:      
        time_datetime = datetime.datetime.strptime(date_string.strip(), fmt)        
    except:        
        time_datetime = datetime.datetime.strptime(date_string.strip()+'T00:00:00', fmt)
    finally:
        pass
    return time_datetime


#http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

      
class TLE(dict):
 
    def __init__(self, no_internet=False):
        self.urls = ['http://www.celestrak.com/NORAD/elements/science.txt',
                     'http://www.celestrak.com/NORAD/elements/resource.txt',
                     'http://www.celestrak.com/NORAD/elements/weather.txt',
                     'http://www.celestrak.com/NORAD/elements/stations.txt']    
        
        self.tle_dir=os.path.join(os.getenv('HOME'), '.faampy', 'tle')
        #create hidden tle directory in $HOME if it does not exist
        if not os.path.exists(self.tle_dir):
            mkdir_p(self.tle_dir)
        self.read_tle(no_internet)            
                               
    def __read_tle_from_file__(self):
        """reads the TLE information from locally stored files in $HOME/.tle"""       
        self.tle_txt = ''
        #get latest directory
        d=os.listdir(self.tle_dir)[-1]
        #read all tle files
        for infile in d:
            if not infile.endswith('~'):
                infi = open( os.path.join( self.tle_dir, infile ), 'r' )
                self.tle_txt += infi.read()
                self.tle_txt+='\r\n'
                infi.close()

    def __read_tle_from_url__(self):
        self.tle_txt=''
        #fetch the tle from the urls
        utcnow=datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        os.mkdir(os.path.join(self.tle_dir, utcnow))
        content=[]
        for url in self.urls:
            c=urllib.urlopen( url ).read()
            content.append(c)
            outfile=os.path.join(self.tle_dir, utcnow, os.path.split(url)[1])
            out = open(outfile, 'w' )
            out.write(c)
            out.close()
        self.tle_txt+='\r\n'.join(content)
            
    def read_tle(self, no_internet):
        """reads the tle information either from a url or a text file
           first of all the script tries to get the most recent info from an url.
           Failing that it uses the local tle files stored in $HOME/.tle """
        if no_internet:
            try:
                self.__read_tle_from_file__()
                self.__parse_tle__()
            except:
                pass
        else:
            try:
                self.__read_tle_from_url__()
                self.__parse_tle__()
            except:
                pass
                    
    def __parse_tle__( self ):
        """parse and feed everything in a dictionary"""
        #split tle at linebreaks
        tle_txt = self.tle_txt.split('\r\n')    
        #loop over tle_txt and put everything in a dictionary 
        for i in range(len(tle_txt)):
            if tle_txt[i].startswith('1'):
                key=tle_txt[i].split()[1].strip('U')
                #every tle entry is three lines long
                val=tle_txt[i-1:i+2]
                self[key]=val
       
    def get(self, sat_id):
        """get the tle for a specific satellite"""     
        sat_tle=self[sat_id]
        result=ephem.readtle(sat_tle[0], sat_tle[1], sat_tle[2])    
        return result

    def __str__(self):
        output=''
        table=[(self[k][0], k) for k in self.keys()]
        table.sort()
        for i in table:
	    output+='%s %s\n' % i
	return output


class Map(object):
  
    def __init__(self, llcrnrlon=-180,llcrnrlat=-80,urcrnrlon=180,urcrnrlat=80):
        lat_0=(llcrnrlat+urcrnrlat)/2.
        lon_0=(llcrnrlon+urcrnrlon)/2.
        self.m=Basemap(llcrnrlon=llcrnrlon,llcrnrlat=llcrnrlat,urcrnrlon=urcrnrlon,urcrnrlat=urcrnrlat,projection='merc', lat_0=lat_0, lon_0=lon_0, resolution='h')
        lat_range=urcrnrlat-llcrnrlat
        lon_range=urcrnrlon-llcrnrlon
        for lat_interval in [30,15,10,5,3,2,1]:
            if float(lat_range)/float(lat_interval) >= 5.0: break
        for lon_interval in [30,15,10,5,3,2,1]:
            if float(lon_range)/float(lon_interval) >= 5.0: break
        
        self.m.drawmeridians(range(-180, 180, lon_interval), labels=[1,0,0,1], fontsize=12)
        self.m.drawparallels(range( -90,  90, lat_interval), labels=[1,1,0,1], fontsize=12)
        self.m.drawcoastlines()
        self.m.drawcountries()
        self.m.drawmapboundary()

    def oplot_sattrack(self, trkpts):
        label, lons, lats = zip(*trkpts)

        # The following section takes care of the occassions when the satellite
        # goes over the edge form -180 to 180 or vice versa.
        # This section is not very nice and needs improvement
        _label, _lons, _lats = [label[0],], [lons[0],], [lats[0],]
        for i in range(1, len(trkpts)):
            if ((lons[i] > 0) and (lons[i-1] < 0) and (np.abs(lons[i] > 120))):
                _label.append(None)
                _label.append(label[i])
                _lons.append(np.nan)
                _lons.append(lons[i])
                _lats.append(np.nan)
                _lats.append(lats[i])
            elif ((lons[i] < 0) and (lons[i-1] > 0) and (np.abs(lons[i] > 120))):                
                _label.append(None)
                _label.append(label[i])
                _lons.append(np.nan)
                _lons.append(lons[i])
                _lats.append(np.nan)
                _lats.append(lats[i])
            else:
                _label.append(label[i])
                _lons.append(lons[i])
                _lats.append(lats[i])
        label = _label[:]
        lons = _lons[:]
        lats = _lats[:]

        x, y=self.m(lons, lats)
        x = np.array(x)        
        ix = np.where(~np.isfinite(x))[0]
        x = list(x)
        if len(ix) > 0:
            for i in ix:
                x[i] = None
                y[i] = None



        self.m.plot(x, y, lw=1.5)
        self.m.plot(x, y, 'o', color='orange')
        for i in range(len(label)):
            if label[i]:
                plt.annotate(label[i], xy=(x[i], y[i]), fontsize=8)        
        plt.annotate('Created: %sZ' % (datetime.datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')), xy=(0.02, 0.02), xycoords='figure fraction', fontsize=8)


class SatTrack(object):

    def __init__(self, sat_id, start_time, end_time, timestep):
        self.trkpts=[]
        self.sat_id=sat_id
        self.start_time=start_time
        self.end_time=end_time
        self.timestep=timestep

    def create_table(self):
        tab=texttable.Texttable()
        tab.set_chars(['-','|','+','-'])
        tab.set_deco(tab.HEADER | tab.VLINES | tab.BORDER)
        tab.set_cols_align(['r','r','r'])
        tab.set_cols_width([19, 7, 6])
        tab.set_precision(2)    
        tab.add_rows(self.trkpts)    
        tab.header(['time (utc)',  'lon', 'lat'])
        return tab

    def get_tles(self):
        self.tle_dict=TLE()        

    def calc(self):
        #tle=tles[satellite_name]
        sat_id=self.sat_id
        start_time=self.start_time
        end_time=self.end_time
        timestep=self.timestep

        self.sat=ephem.readtle(self.tle_dict[sat_id][0], 
                               self.tle_dict[sat_id][1],
                               self.tle_dict[sat_id][2]) 

 
        start_time_datetime=__parse_time__(start_time)
        end_time_datetime=__parse_time__(end_time)
        timestamp=start_time_datetime
               
        while True:
            if timestamp > end_time_datetime:
                break
            obs.date=timestamp
            self.sat.compute(obs)
            self.trkpts.append([timestamp.strftime('%d-%m-%YT%H:%M:%S'),
                                math.degrees(self.sat.sublong),
                                math.degrees(self.sat.sublat)])
            timestamp+=datetime.timedelta(seconds=timestep)        

    def __str__(self):
        output=''
        ttable=self.create_table()
        #Output table to the screen
        output+='\n'
        output+='\n'.join(self.tle_dict[self.sat_id])
        output+='\n'*2
        output+=ttable.draw()
        output+='\n'
        #return (data, satellite_name, tle, ttable.draw())
        return output



obs=ephem.Observer()
obs.lat='14.9429'
obs.lon='-23.4839'

def _argparser():
    import argparse
    sys.argv.insert(0, 'faampy sat_tracker')
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(
        title='subcommands', description='valid subcommands',
        help='additional help')
    parser_tle = subparsers.add_parser('tle')
    parser_tle.add_argument('sat_name', action="store", nargs='?', type=str, default='all',
                        help='shows list of available satellites and their IDs')
    parser_track=subparsers.add_parser('track')
    parser_track.add_argument('sat_id', nargs="*", action='store', type=str,
                        help="Satellite ID(s)")
    parser_track.add_argument('start_time', action='store', type=str,
                        help="date in the format dd-mm-YYYY or dd-mm-YYYYTHH:MM:SS")
    parser_track.add_argument('end_time', action='store', type=str,
                        help="date in the format dd-mm-YYYY or dd-mm-YYYYTHH:MM:SS")
    parser_track.add_argument('timestep',
                        action='store',
                        type=int,
                        help="Timestep in seconds")    
    parser_track.add_argument('-w', '--write_to_file', action="store_true", required=False, default=False,
                        help='If flag is set the output is stored to a file in the $HOME directory. Default: False')
    parser_track.add_argument('-m', '--show_map', nargs='?', required=False, const='-180 -80 180 80',
                        help='Boundary for the map in the form "left_longitude bottom_latitude right_longitude top_latitude". The input has ')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()
    FINISHED=False
    #print(args)
    tle_dict=TLE()
    
    try:
        if args.sat_name:
            if args.sat_name == 'all':
	         print(tle_dict)
	    else:
	        for k in tle_dict.keys():
	            if args.sat_name.lower() in tle_dict[k][0].lower():		  
		        print('%s %s\n' % (tle_dict[k][0], k))        
        FINISHED=True
    except:
        pass
    
    # TODO: there must be a better way to get out
    if FINISHED:
        sys.exit()
           
    for s in args.sat_id:
        s = SatTrack(s, args.start_time, args.end_time, args.timestep)
        s.tle_dict = tle_dict
        s.calc()
        print(s)
    
        sat_name = s.sat.name
        sat_name = re.sub(' ', '_', s.sat.name)
        sat_name = re.sub('\(', '', s.sat.name)
        sat_name = re.sub('\)', '', s.sat.name)
    
        if args.write_to_file == True:
            ofname = os.path.join(os.environ['HOME'], '%s_%s.txt' % (sat_name.lower(), __parse_time__(args.start_time).strftime('%Y%m%d_%H%M%S')))
            outfile = open(ofname, 'w')
            outfile.write(s.__str__())
            outfile.close()
        if args.show_map:            
            llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat = args.show_map.split()  
            m = Map(llcrnrlon=float(llcrnrlon),
                    llcrnrlat=float(llcrnrlat),
                    urcrnrlon=float(urcrnrlon),
                    urcrnrlat=float(urcrnrlat))
            m.oplot_sattrack(s.trkpts)
            title = '%s\n%s to %s' % (sat_name,
				      __parse_time__(args.start_time).strftime('%Y-%m-%dT%H:%M:%S'),
				      __parse_time__(args.end_time).strftime('%Y-%m-%dT%H:%M:%S'))
            plt.title(title)
            imgfilename = os.path.join(os.environ['HOME'],
                                     'sat_track_%s_%s_to_%s' % (sat_name.replace(' ', '_'),
                                                                __parse_time__(args.start_time).strftime('%Y%m%dT%H%M%S'),
                                                                __parse_time__(args.end_time).strftime('%Y%m%dT%H%M%S')))
            plt.savefig(imgfilename)
            sys.stdout.write('Map saved as: \n  %s\n\n' % (imgfilename,))
            plt.clf()


if __name__ == '__main__':
    main()

TESTING = False

if TESTING:
    today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    tomorrow = (datetime.datetime.utcnow()+datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    tle = TLE()
    s = SatTrack('39084', today, tomorrow, 60)
    s.tle_dict = tle
    s.calc()
    llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat = -38, 35, 3, 53
    m = Map(llcrnrlon=float(llcrnrlon),
            llcrnrlat=float(llcrnrlat),
            urcrnrlon=float(urcrnrlon),
            urcrnrlat=float(urcrnrlat))
    m.oplot_sattrack(s.trkpts)
