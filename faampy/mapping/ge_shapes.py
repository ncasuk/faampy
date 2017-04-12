import numpy as np
from numpy import arcsin, sin, cos, arctan2

ELGIN = (1.8362333333, 57.0110555556, 0)
WDIR = 90.

LENGTH = 65.0
WIDTH = 1.0


KML_LINESTRING_TEMPLATE = """
<Placemark>
<name>%s</name>
<description>%s</description>
<visibility>1</visibility>
<Style>
  <LineStyle>  
    <color>#64ffffff</color>
    <width>3</width>
  </LineStyle> 
</Style>
<LineString>
  <coordinates>
    %s
  </coordinates>
</LineString>
</Placemark>
"""

KML_HEADER_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Document>
<Folder>
"""

KML_FOOTER_TEMPLATE = """
</Folder>
</Document>
</kml>
"""



def point_from_distance_and_bearing(origin, bearing, distance):
    #see http://www.movable-type.co.uk/scripts/latlong.html
    R = 6137.0
    d = distance
    theta = np.deg2rad(bearing)    
    lat1 = np.deg2rad(origin[1])
    lon1 = np.deg2rad(origin[0])
    lat2 = arcsin(sin(lat1)*cos(d/R) + cos(lat1)*sin(d/R)*cos(theta))
    lon2 = lon1 + arctan2(sin(theta) * sin(d/R)*cos(lat1), cos(d/R)-sin(lat1)*sin(lat2))    
    return(np.rad2deg(lon2), np.rad2deg(lat2))


#def create_kml(name, lon, lat, bearing, distance):
def create_kml(name, origin, bearing, distance):
    lon, lat = [], []
    for org in origin:
       lon.append(org[0])
       lat.append(org[1])
    linestring_txt = ""
    for i in range(len(name)):
        desc = 'Bearing: %6.2f' % bearing[i]
        lon2, lat2 = point_from_distance_and_bearing((lon[i], lat[i]), bearing[i], distance[i])
        linestring_coord = '%.5f,%.5f,%.5f\n' % (lon[i], lat[i], 0)
        linestring_coord += '%.5f,%.5f,%.5f\n' % (lon2, lat2, 0)
        linestring_txt += KML_LINESTRING_TEMPLATE % (name[i], desc, linestring_coord)
    kml = KML_HEADER_TEMPLATE + linestring_txt + KML_FOOTER_TEMPLATE
    return kml
        

