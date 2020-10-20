#!/usr/bin/python

'''
FlightSummary module for processing the Flight Managers flight summary.
The class parses the original text file and extract all entries. The module
works with both the "old" (Horace) format and the "new" (DECADES) one.

All event entries are in a list.



In [1]: import matplotlib.pyplot as plt

In [2]: import netCDF4

In [3]: import faampy.fltsumm.FlightSummary as flsum

In [4]: fltsummfile='/home/axel/Dropbox/cast2014/fltsums/edited/flight-sum_faam_20140124_r0_b825.csv'
In [5]: ncfile='/home/axel/Dropbox/cast2014/b825-jan-24/core_processed/core_faam_20140124_v004_r2_b825.nc'

In [6]: outpath='/home/axel/'

In [7]: fs=flsum.FlightSummary(fltsummfile)

In [8]: ds=netCDF4.Dataset(ncfile, 'r')

In [9]: #Print a summary of the flight summary to stdout

In [10]: print(fs)
Name:       taxy
Start Time: 2014-01-24 22:54:50
End Time:
Comment:

##############################
Name:       Profile 1
Start Time: 2014-01-24 23:01:33
End Time:   2014-01-24 23:35:02
Comment:

##############################
Name:       T/O
Start Time: 2014-01-24 23:01:33
End Time:
Comment:    Guam

##############################
Name:       Run 1
Start Time: 2014-01-24 23:10:13
End Time:   2014-01-24 23:28:36
Comment:

##############################
Name:       Run 2
Start Time: 2014-01-24 23:35:10
End Time:   2014-01-24 23:56:42
Comment:

##############################
Name:       !
Start Time: 2014-01-24 23:42:41
End Time:
Comment:    slight climb

...

In [11]: print('Number of FS Entries: %i' % len(fs.Entries))
Number of FS Entries: 9

In [12]:

In [12]: #get the 4th event from the

In [13]: e04=fs.Entries[3]

In [14]: print(e04)
Name:       Run 1
Start Time: 2014-01-24 23:10:13
End Time:   2014-01-24 23:28:36
Comment:

In [15]: #get the indeces that correspond to the netCDF

In [16]: e04.set_index(ds)

In [17]: #pull the non deiced temperature from the netCDF

In [18]: data=ds.variables['TAT_ND_R'][e04.Index,:]

In [19]: plt.plot(data.ravel())
Out[19]: [<matplotlib.lines.Line2D at 0x7fb6718db490>]

In [20]: plt.title('%s\n%s to %s' % (e04.Name, e04.Start_time[-8:], e04.Stop_time[-8:]))
Out[20]: <matplotlib.text.Text at 0x7fb6718a6310>

In [21]: plt.show()

In [22]: #create html and kml files

In [23]: fs=flsum.process(fltsummfile, ncfile, outpath)

In [24]:

'''

import os
import re
import sys
import datetime
import lxml.html
import netCDF4
import numpy as np
import types

import faampy.core.utils


def __two_point_event_as_kml__(self):
    TEMPLATE="""<Placemark>
  <name>%s</name>
  <styleUrl>#line</styleUrl>
  <description>&lt;![CDATA[]]&gt;</description>
    <MultiGeometry>
      <Point>
        <altitudeMode>absolute</altitudeMode>
          <coordinates>
            %s
          </coordinates>
      </Point>
      <Point>
        <altitudeMode>absolute</altitudeMode>
          <coordinates>
            %s
          </coordinates>
      </Point>
        <LineString>
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

    pt1_coord_string='%f,%f,%f\n' % (self.Coords[0][0],
                                     self.Coords[0][1],
                                     self.Coords[0][2])
    pt2_coord_string='%f,%f,%f\n' % (self.Coords[-1][0],
                                     self.Coords[-1][1],
                                     self.Coords[-1][2])
    ls_coord_string=''
    for c in self.Coords[::15]:
        ls_coord_string+='%f,%f,%f\n' % (c[0], c[1], c[2])

    result=TEMPLATE % (self.Name,
		       pt1_coord_string,
		       pt2_coord_string,
		       ls_coord_string)
    self.kml=result
    return result


def __one_point_event_as_kml__(self):
    TEMPLATE="""<Placemark>
  <name>%s</name>
    <description>&lt;![CDATA[]]&gt;</description>
    <Point>
    <altitudeMode>absolute</altitudeMode>
       <coordinates>
         %s
       </coordinates>
    </Point>
</Placemark>
"""

    pt_cor_string='%f,%f,%f\n' % (self.Coords[0],
                                  self.Coords[1],
                                  self.Coords[2])

    result=TEMPLATE % (self.Name, pt_cor_string)
    self.kml=result
    return result


class Event(object):

    Start_time, Start_time_48, Stop_time, Stop_time_48, Coords, format=None, None, None, None, None, None
    Name, Start_height, Stop_height, Hdg, Comment='','','','',''

    def __init__(self):
        pass

    def fix_time(self, ds):
        if self.format == 'decades':
            basetime=faampy.core.utils.get_base_time(ds)
            td=datetime.datetime.strptime(self.Start_time, '%Y-%m-%d %H:%M:%S')-basetime
            #self.Start_time_48=datetime.datetime.strptime("%02d:%02d:%02d" % (td.seconds/3600, td.seconds%3600/60, (td.seconds%3600)%60), '%H:%M:%S')
            seconds=td.total_seconds()
            self.Start_time_48="%02d%02d%02d" % (seconds/3600, seconds%3600/60, (seconds%3600)%60)
            #self.Start_time_48=basetime.strftime('%Y-%m-%d')+' '+self.Start_time.strftime('%H:%M:%S')
            if self.Stop_time:
                td=datetime.datetime.strptime(self.Stop_time, '%Y-%m-%d %H:%M:%S')-basetime
                seconds=td.total_seconds()
                self.Stop_time_48="%02d%02d%02d" % (seconds/3600, seconds%3600/60, (seconds%3600)%60)
                #self.Stop_time_48=basetime.strftime('%Y-%m-%d')+' '+self.Stop_time
        else:
            self.Start_time_48=self.Start_time
            self.Stop_time_48=self.Stop_time

    def set_index(self, ds):
        if self.format == 'decades':
            start_time=datetime.datetime.strptime(self.Start_time, '%Y-%m-%d %H:%M:%S').strftime('%H%M%S')
            if self.Stop_time:
                stop_time=datetime.datetime.strptime(self.Stop_time, '%Y-%m-%d %H:%M:%S').strftime('%H%M%S')
            td=datetime.datetime.strptime(self.Start_time, '%Y-%m-%d %H:%M:%S')-faampy.core.utils.get_base_time(ds)
            if td.total_seconds() > 86400:
                start_time='%02d' % (int(start_time[0:2])+24)+start_time[2:]

            if self.Stop_time:
                td=datetime.datetime.strptime(self.Stop_time, '%Y-%m-%d %H:%M:%S')-faampy.core.utils.get_base_time(ds)
                if td.total_seconds() > 86400:
                    stop_time='%02d' % (int(stop_time[0:2])+24)+stop_time[2:]
        elif self.format == 'horace':
            start_time=self.Start_time
            if self.Stop_time:
                stop_time=self.Stop_time
        if self.Stop_time:
            self.Index=range(faampy.core.utils.get_index_from_hhmmss(ds, start_time),
                             faampy.core.utils.get_index_from_hhmmss(ds, stop_time))
        else:
            self.Index=faampy.core.utils.get_index_from_hhmmss(ds, start_time)

    def set_coords(self, ds):
        lon_gin=ds.variables['LON_GIN'][self.Index, 0]
        lat_gin=ds.variables['LAT_GIN'][self.Index, 0]
        alt_gin=ds.variables['ALT_GIN'][self.Index, 0]
        if lon_gin.size > 1:
            self.Coords=zip(lon_gin.tolist(),
                            lat_gin.tolist(),
                            alt_gin.tolist())
        else:
            self.Coords=(float(lon_gin),
                         float(lat_gin),
                         float(alt_gin))
            if np.all(np.isnan(self.Coords)):
                self.Coords=None

    def as_kml(self):
        if self.Stop_time:
            self.as_kml=types.MethodType(__two_point_event_as_kml__, self)
        else:
            self.as_kml=types.MethodType(__one_point_event_as_kml__, self)
        self.as_kml()
        return self.kml

    def as_txt(self):
        fmt="%-6s  %-6s   %-19s %-17s %3s %s"
        vals=[]
        #vals.append(datetime.datetime.strptime(self.Start_time, '%Y-%m-%d %H:%M:%S').strftime('%H%M%S'))
        vals.append(self.Start_time_48)
        if self.Stop_time:
            #vals.append(datetime.datetime.strptime(self.Stop_time, '%Y-%m-%d %H:%M:%S').strftime('%H%M%S'))
            vals.append(self.Stop_time_48)
        else:
            vals.append('')
        if len(self.Name) > 19:
            spl=self.Name.split()
            self.Name=spl[0]
            self.Comment=' '.join(spl[1:]+[self.Comment])
        vals.append(self.Name)
        if self.Stop_height:
            vals.append('%.2f - %.2f kft' % (float(self.Start_height), float(self.Stop_height)))
        else:
            vals.append('%.2f kft' % (float(self.Start_height),))
        vals.append(self.Hdg)
        vals.append(self.Comment)
        result=fmt % tuple(vals)
        return result

    def __str__(self):
        result=''
        result+='Name:       %s\n' % (self.Name)
        result+='Start Time: %s\n' % (self.Start_time)
        result+='End Time:   %s\n' % (self.Stop_time)
        result+='Comment:    %s\n' % (self.Comment)
        return result


class FlightSummary(object):
    """from FlightSummary import *
    fs=FlightSummary(fltsummfile)

    """

    def __init__(self, fltsumm_file):
        self.format=None
        self.fid=None
        self.date=None
        self.basetime=None
        self.filename=fltsumm_file
        self.revision=None
        self.Entries=[]

        if not os.path.exists(fltsumm_file):
            sys.stdout.write("File does not exist!\n")
        else:
            self.__read__()
            self.parse()
            try:
                self.date=datetime.datetime.strptime(os.path.basename(self.filename).split('_faam_')[1][0:8],'%Y%m%d')
            except:
                pass


    def __read__(self):
        f=open(self.filename, 'r')
        self.txt=f.readlines()
        f.close()

    def parse(self):

        if '<!DOCTYPE html PUBLIC' in ''.join(self.txt):
            def remove_non_ascii(s): return "".join(i for i in s if ord(i)<128)
            txt=''.join(self.txt)

            txt=re.sub('<td colspan="5" class="ghost">&nbsp;</td>', '<td>&nbsp;</td>'*5, txt)

            ix_s=re.search('<table summary="Flight Summary Events" id="summary">', txt).start(0)
            ix_e=re.search('</table>', txt).end(0)
            s=txt[ix_s:ix_e]

            html=lxml.html.fromstring(s)

            tbl = []
            rows = html.cssselect("tr")
            for row in rows:
                tbl.append([])
                for td in row.cssselect("td"):
                    #tbl[-1].append(unicode(td.text_content()))
                    tbl[-1].append(remove_non_ascii(td.text_content()))

            for line in tbl:
                if not line:
                    continue
                e=Event()
                if self.basetime:
                    e.basetime=self.basetime
                e.Start_time=re.sub(':', '', line[1])
                e.Stop_time=re.sub(':', '', line[6])
                e.Name=line[0]

                tmp=re.sub('kft', '', line[3]).strip()
                tmp=re.findall('[+-]?\d+.\d+', tmp)
                if tmp: e.Start_height=tmp[0]
                tmp=re.sub('kft', '', line[8]).strip()
                tmp=re.findall('[+-]?\d+.\d+', tmp)
                if tmp: e.Stop_height=tmp[0]
                e.Hdg=line[2]
                if len(line) > 11:
                    e.Comment=','.join(line[12:])
                else:
                    e.Comment=''
                e.format='decades'
                e.format='horace'
                self.Entries.append(e)
            self.Entries.sort(key= lambda x: x.Start_time)
            return

        for line in self.txt:
            if not line.strip():
                continue
            elif line[0:6].isdigit():
                e=Event()
                e.Start_time=line[0:6]
                if line[8:14].strip():
                    e.Stop_time=line[8:14]
                e.Name = line[17:37].strip()
                tmp=line[37:52].strip()
                tmp=re.sub('kft', '', tmp).strip()
                heights=re.findall('[+-]?\d+.\d+', tmp)
                #heights=re.findall('[+-]?[\d+]?.\d+', tmp)
                e.Start_height=heights[0]
                if len(heights) > 1:
                    e.Stop_height=heights[1]
                e.Hdg=line[55:58].strip()
                e.Comment=line[59:].strip()
                e.format='horace'
                self.Entries.append(e)
            elif len(line.split(',')) > 2:
                line=line.split(',')
                #skip header line
                if ('Event' in line[0]):
                    continue
                e=Event()
                if self.basetime:
                    e.basetime=self.basetime
                e.Start_time=line[1]
                e.Stop_time=line[6]
                e.Name=line[0]
                e.Start_height=line[3]
                e.Stop_height=line[8]
                e.Hdg=line[2]
                if len(line) > 11:
                    e.Comment=line[11]
                else:
                    e.Comment=''
                e.format='decades'
                self.Entries.append(e)
        self.Entries.sort(key=lambda x: x.Start_time)

    def as_kml(self, ofile=None, fid='', date=''):
        kml=''
        header = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Folder>
    <name>%s-Flight-Summary</name>
        <Style id="line">
		<LineStyle>
			<color>ff0000ff</color>
		</LineStyle>
		<PolyStyle>
			<color>ff0000aa</color>
		</PolyStyle>
	</Style>
        <description>%s-%s</description>
        <open>1</open>
""" % (fid, fid, date)
        kml+=header
        for e in self.Entries:
            if e.Coords:
                try:
                    kml+=e.as_kml()
                except:
                    pass
        kml+="</Folder>\n</kml>\n"
        if ofile:
            f=open(ofile, 'w')
            f.write(kml)
            f.close()
        return kml

    def __str__(self, ofile=None):
        result=''
        for e in self.Entries:
            result+=e.__str__()
            result+=30*'#'+'\n'
        return result

    def as_txt(self, ofile=None, fid='', date=''):
        """Format Flight Summary as text file
        """
        result="""                     FLIGHT SUMMARY
Flight No %s
Date: %s
Project:
Location:

Start   End
Time    Time     Event               Height (s)        Hdg Comments
----    ----     -----               ----------        --- --------
""" % (fid, date)
        for e in self.Entries:
            result+=e.as_txt().strip()+'\n'
        if ofile:
            f=open(ofile, 'w')
            f.write(result)
            f.close()
        return result


    def as_html(self, ofile=None):
        """format Flight Summary as html table

        """
        html='<table border=1>\n'
        row=['Name', 'Start Time', 'Start Height<br>(kft)',  'Stop Time', 'Stop Height<br>(kft)', 'Comment']
        html+='<tr>\n<td>'+'</td><td>'.join(row)+'</td>\n</tr>\n'
        for e in self.Entries:
            row=[e.Name, e.Start_time, e.Start_height, e.Stop_time, e.Stop_height, e.Comment]
            row2=[]
            for i in row:
                if i == None:
                    row2.append('')
                else:
                    row2.append(i)
            row=row2
            html+='<tr>\n<td>'+'</td><td>'.join(row)+'</td>\n</tr>\n'
        html+='</table>\n'
        if ofile:
            f=open(ofile, 'w')
            f.write(html)
            f.close()
        return html


def process(fltsummfile, ncfile, *outpath):
    ds=netCDF4.Dataset(ncfile, 'r')
    basetime=faampy.core.utils.get_base_time(ds)
    fid=faampy.core.utils.get_fid(ds)
    fs=FlightSummary(fltsummfile)
    #for i in range(len(fs.Entries)):
    for ent in fs.Entries:
        try:
            ent.fix_time(ds)
            ent.set_index(ds)
            ent.set_coords(ds)
        except:
            pass
    basename='flight-sum_faam_%s_r0_%s' % (basetime.strftime('%Y%m%d'), fid)
    if outpath:
        outpath = outpath[0]
        fs.as_kml(ofile=os.path.join(outpath, basename+'.kml'), fid=fid, date=basetime.strftime('%d/%m/%Y'))
        fs.as_html(ofile=os.path.join(outpath, basename+'.html'))
        fs.as_txt(ofile=os.path.join(outpath, basename+'.txt'), fid=fid, date=basetime.strftime('%d/%m/%Y'))
    ds.close()
    return fs


def _argparser():
    import argparse
    from argparse import RawTextHelpFormatter
    sys.argv.insert(0, 'faampy flight_summary')
    parser=argparse.ArgumentParser(prog='faampy flight_summary',
                                   description=__doc__,
                                   formatter_class=RawTextHelpFormatter)
    parser.add_argument('fltsummfile', action="store",
                        type=str, help='Flight Summary file')
    parser.add_argument('ncfile', action="store",
                        type=str, help='core_faam netCDF')
    parser.add_argument('outpath', action="store",
                        type=str,
                        help='outpath where the newly formatted flight summaries will be saved')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()
    process(args.fltsummfile, args.ncfile, args.outpath)
    sys.stdout.write('Done ...\n')


if __name__ == '__main__':
    main()
