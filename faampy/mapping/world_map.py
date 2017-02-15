# -*- coding: utf-8 -*-

import datetime
import itertools
import Image
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
import os
import sys
import tempfile

import faampy
from faampy.core.faam_spatial import FAAM_Spatial_DB
import json


##### SETTINGS #######################################

PAPER_SIZE='A4'
DPI=100

FLIGHT_TRACK_DATA_PATH='/home/axel/faam_kml/flight_track_data'

OUTPATH='/home/axel/Dropbox/poster_map/'

DAFT_FLIGHT_TRACKS=['b364', 'b358', 'b403', 'b657', 'b810', 'b811', 'b813', 'b815', 'b817', 'b818', 'b819', 'b820']

#BACKGROUND_IMAGE='/home/axel/Dropbox/poster_map/world_4326_10476x5238.png'

BACKGROUND_IMAGE=True
BACKGROUND_IMAGE_PATH='/home/axel/Dropbox/poster_map/'
BACKGROUND_IMAGE_PATH = os.path.join(faampy.__path__[0], '..', 'files', 'img')
os.path.exists(BACKGROUND_IMAGE_PATH)
BACKGROUND_IMAGE_OVERWRITE=False
BACKGROUND_IMAGE_FILENAME=''
BACKGROUND_WARP=False
BACKGROUND_SCALE=1.0

PLOT_FLIGHT_TRACKS=True
PLOT_AIRPORTS=True

RELOAD_FLIGHT_TRACKS=False

#BoundaryBox
LLCRNRLON=-180.0
LLCRNRLAT=-90
URCRNRLON=180.0
URCRNRLAT=90.0

######################################################


plt.close('all')

din_dict = {'a0': [(46.8, 33.1), int(12.0*1.41**4)],
            'a1': [(33.1, 23.4), int(12.0*1.41**3)],
            'a2': [(23.4, 16.5), int(12.0*1.41**2)],
            'a3': [(16.5, 11.7), int(12.0*1.41**1)],
            'a4': [(11.7, 8.27), int(12.0*1.41**0)]}


mpl.rc('text.usetex', True)
mpl.rc('figure.figsize', din_dict[str.lower(PAPER_SIZE)][0])
mpl.rc('font.size', din_dict[str.lower(PAPER_SIZE)][1])


#http://gis.stackexchange.com/questions/99672/mapnik-rendering-with-osm-carto-style#


def create_background_img(imgx, imgy, outfile):
    import mapnik
    robin=mapnik.Projection('+proj=robin +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs ')
    #  Change this to the bounding box you want
    longlat = mapnik.Projection('+init=epsg:4326')
    bounds = (LLCRNRLON, LLCRNRLAT, URCRNRLON, URCRNRLAT)

    map_uri=outfile
    mapfile='osm.xml'
    m = mapnik.Map(imgx,imgy)
    mapnik.load_map(m,mapfile)

    # ensure the target map projection is mercator
    m.srs = robin.params()

    bbox = mapnik.Envelope(*bounds)

    # Our bounds above are in long/lat, but our map
    # is in spherical mercator, so we need to transform
    # the bounding box to mercator to properly position
    # the Map when we call `zoom_to_box()`
    transform = mapnik.ProjTransform(longlat,robin)
    robin_bbox = transform.forward(bbox)
    #print(robin_bbox)
    # Mapnik internally will fix the aspect ratio of the bounding box
    # to match the aspect ratio of the target image width and height
    # This behavior is controlled by setting the `m.aspect_fix_mode`
    # and defaults to GROW_BBOX, but you can also change it to alter
    # the target image size by setting aspect_fix_mode to GROW_CANVAS
    #m.aspect_fix_mode = mapnik.GROW_CANVAS
    # Note: aspect_fix_mode is only available in Mapnik >= 0.6.0
    m.zoom_to_box(robin_bbox)

    # render the map to an image
    im = mapnik.Image(imgx,imgy)
    mapnik.render_to_file(m, map_uri, 'png')

    sys.stdout.write('output image to %s!\n' % map_uri)

    # Note: instead of creating an image, rendering to it, and then
    # saving, we can also do this in one step like:
    # mapnik.render_to_file(m, map_uri,'png')

    # And in Mapnik >= 0.7.0 you can also use `render_to_file()` to output
    # to Cairo supported formats if you have Mapnik built with Cairo support
    # For example, to render to pdf or svg do:
    # mapnik.render_to_file(m, "image.pdf")
    #mapnik.render_to_file(m, "image.svg")


def get_ax_size():
    ax=plt.gca()
    fig=plt.gcf()
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width, height = bbox.width, bbox.height
    width*=float(DPI)
    height*=float(DPI)
    return int(width), int(height)


def plot_airports(m):
    airports_file = os.path.join(faampy.__path__[0], '..', 'files', 'other', 'airports.txt')
    data=np.genfromtxt(airports_file, delimiter=',', dtype=None, names='id,lats,lons')
    x, y=m(data['lons'], data['lats'])
    # the zorder setting makes sure that the airport locations are plotted on top of the flight tracks
    m.scatter(x, y, c='orange', zorder=3, alpha=0.5)


def plot_flight_tracks(m, x, y):
    m.plot(x, y, linewidth=1.0, color='0.4', alpha=0.7)


def get_flight_tracks(m):
    db = FAAM_Spatial_DB(os.path.join(os.environ['HOME'], 'db', 'faam_spatial_db.sqlite'))
    sql = """SELECT fid from flight_tracks;"""
    cur = db.conn.cursor()
    cur.execute(sql)
    fids = [fid[0] for fid in cur.fetchall()]
    fids.sort()
    # tidy up flight tracks
    for daft in DAFT_FLIGHT_TRACKS:
        if daft in fids:
            fids.remove(daft)
        
    sql = """SELECT AsGeojson(Simplify(FT.the_geom, 0.01)) from flight_tracks FT where FT.fid in (%s);""" % (','.join(["'%s'" % fid for fid in fids]))
    cur = db.conn.cursor()
    cur.execute(sql) 
    result = cur.fetchall()
       
    x, y, z = [], [], []
    for r in result:
        if not r:
            continue
        lon, lat, alt = zip(*(json.loads(r[0]))['coordinates'])
        _x, _y = m(lon, lat)        
        x.append(_x)
        x.append([None,])
        y.append(_y)
        y.append([None,])
        z.append(alt)
        z.append([None,])
    
    #now flatten the coordinates
    x = list(itertools.chain.from_iterable(x))
    y = list(itertools.chain.from_iterable(y))
    z = list(itertools.chain.from_iterable(z))
    return (x,y,z)
    

def _argparser():
    import argparse
    from argparse import RawTextHelpFormatter
    sys.argv.insert(0, 'faampy world_map')
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('--din', action="store", type=str, help='Paper size', default='a4')
    parser.add_argument('-o', '--outpath', action="store", type=str, required=False,
                        default=os.environ['HOME'], help='Directory where the images will be stored. Default: $HOME.')
    parser.add_argument('--dpi', action="store_true", required=False, default='300',
                        help='resolution dot per inch')
    parser.add_argument('--map_background', action="store_true", required=False, default=True,
                        help='whether background map is added or not')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()
        
    m = Basemap(projection='robin', lon_0=0, resolution='c')
    
    m.drawcoastlines(linewidth=0,zorder=0)
    plt.tight_layout()
    
    #Dodgy way to get the correct size for the mapnik osm image
    plt.savefig(os.path.join(tempfile.mkdtemp()+'.svg'), dpi=args.dpi)
    width, height=get_ax_size()
    
    #Determine size for the OSM background image in Robinson projection
    sys.stdout.write('Size: %i x %i\n' % get_ax_size())
    
    #Fix empty areas for the OSM background image
    ocean_color=tuple([rgb/255. for rgb in (180,209,206)])
    ice_color=tuple([rgb/255. for rgb in (241,240,230)])
    #Arctic: Fill everything north of 85 degrees with ocean color
    m.drawmapboundary(fill_color=ocean_color)
    
    #Antarctica: Fill everything south of -85 with ice_color using a Polygon
    from matplotlib.patches import Polygon
    coord=[m(x, y) for x,y in zip(range(-180, 181), [-85.,]*361)] + [m(x, y) for x,y in zip(range(180, -181,-1), [-90.,]*361)]
    p=Polygon(coord, facecolor=ice_color, edgecolor='none')
    plt.gca().add_patch(p)
    
    
    if args.map_background:        
        # TODO
        BACKGROUND_IMAGE_FILENAME=os.path.join(BACKGROUND_IMAGE_PATH, 'world_osm_54030_%ix%i.png' % (width, height))
        print(BACKGROUND_IMAGE_FILENAME)
        if (not os.path.exists(BACKGROUND_IMAGE_FILENAME) or BACKGROUND_IMAGE_OVERWRITE):
            create_background_img(width, height, BACKGROUND_IMAGE_FILENAME)
        img=Image.open(BACKGROUND_IMAGE_FILENAME)
        m.imshow(img, origin='upper')
        #m.drawcoastlines() #uncomment this for testing purposes, to see if image fits
    else:
        m.drawcoastlines()
        m.fillcontinents(color='coral',lake_color='aqua')
        m.drawmapboundary(fill_color='aqua')
        img=Image.open(BACKGROUND_IMAGE)
        m.imshow(img, origin='upper')
    
    m.drawparallels(np.arange(-90,90,30),labels=[0,0,0,0],fontsize=12)
    m.drawmeridians(np.arange(0,360,30),labels=[1,0,0,0],fontsize=12)
        
    x, y, z = get_flight_tracks(m)    
    plot_flight_tracks(m, x, y)
    
    if PLOT_AIRPORTS:
        plot_airports(m)

    plt.tight_layout()
    
    plt.figtext(0.94, 0.05, r'Status %s' % datetime.datetime.utcnow().strftime('%d-%m-%Y'), size='small', ha='right')
    #plt.figtext(0.02, 0.9, r"\textbf{\textit{FAAM}}" "\n" r"Facility for Airborne Atmospheric Measurements", size='x-large', color='blue')

    for fmt in ['png', 'pdf']:
        plt.savefig(os.path.join(args.outpath, 'poster_flight_map_%s_%sdpi.%s' % (args.din.lower(), str(args.dpi).lower(), fmt)), dpi=int(args.dpi), transparent=True)


if __name__ == '__main__':
    main()
