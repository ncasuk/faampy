# -*- coding: utf-8 -*-

"""
This script converts the NIMROD weather radar data format into a netCDF with
the dimensions:

  * Timestamp
  * Longitude
  * Latitude

The original array in the NIMROD data fits the OSGB 1936 spatial reference
system. However, to make the results work with for example cis it is necessary
to warp the array to EPSG:4326 so that longitude and latitude are available as
dimensions.

The created netCDF results were tested with the cistools_. If the netCDF
stores more than one timestamp it is necessary to extract one layer using the
subset command like this::

   cis subset rain_intensity:nimrod.nc timestamp=['2012-03-04T00:50'] \
-o nimrod_20120304T0050.nc

The above command extracts the data for the timestamp '2012-03-04T00:50' and
writes a new netCDF with the filename "nimrod_20120304T0050.nc".

Now it is possible to plot the data as a heatmap using cis::

    cis plot rain_intensity:nimrod_20120304T0050.nc

Maybe there is a way to skip the subset step but so far I have not found it.

.. _cistools: http://www.cistools.net/

"""


import array
import datetime
import gzip
import netCDF4
from multiprocessing import Pool
import numpy as np
import os
from osgeo import osr, gdal
import shutil
import struct
import sys
import tarfile
import tempfile
import time


_TEMP_FOLDER=tempfile.mkdtemp()

# taken from: http://badc.nerc.ac.uk/browse/badc/ukmo-nimrod/software/python/read_nimrod.py
def read_nimrod(pathed_file, quite=True):

    file_id=open(pathed_file,"rb")
    record_length,=struct.unpack(">l", file_id.read(4))
    if record_length != 512:
        sys.stdout.write("Unexpected record length: %i" % record_length)
        sys.exit(1)

    gen_ints=array.array("h")
    gen_reals=array.array("f")
    spec_reals=array.array("f")
    characters=array.array("c")
    spec_ints=array.array("h")

    gen_ints.read(file_id, 31)
    gen_ints.byteswap()

    gen_reals.read(file_id, 28)
    gen_reals.byteswap()

    spec_reals.read(file_id, 45)
    spec_reals.byteswap()
    characters.read(file_id, 56)
    spec_ints.read(file_id, 51)
    spec_ints.byteswap()

    record_length,=struct.unpack(">l", file_id.read(4))
    if record_length != 512:
        raise ("Unexpected record length", record_length)

    chars=characters.tostring()

    if not quite:
        sys.stdout.write("\nDate %4.4d%2.2d%2.2d Time %2.2d:%2.2d Grid %d x %d\n" %(gen_ints[0], gen_ints[1], gen_ints[2], gen_ints[3], gen_ints[4], gen_ints[15], gen_ints[16]))
        sys.stdout.write("start northing %.1f, row interval %.1f, start easting %.1f, column interval %.1f\n"  %(gen_reals[2], gen_reals[3], gen_reals[4], gen_reals[5]))
        sys.stdout.write("Units are %s\n" % chars[0:8])
        sys.stdout.write("Data source is %s\n" % chars[8:32])
        sys.stdout.write("Parameter is %s\n" % chars[32:55])
        for i in range(gen_ints[22]):
            print (i+108, spec_ints[i])
        for i in gen_reals:
            print(i)
        for i in spec_reals:
            print(i)
    #Read data
    cols=gen_ints[15]
    rows=gen_ints[16]
    array_size=cols*rows

    record_length,=struct.unpack(">l", file_id.read(4))
    if record_length != array_size*2:
        raise ("Unexpected record length", record_length)

    data=array.array("h")
    try:
        data.read(file_id, array_size)
        record_length,=struct.unpack(">l", file_id.read(4))
        if record_length != array_size*2:
            raise ("Unexpected record length", record_length)
        data.byteswap()
    except:
        sys.stdout.write("Read failed\n")
    file_id.close()
    result={'data':             np.array(data),
            'cols':             cols,
            'rows':             rows,
            'start_northing':   gen_reals[2],
            'row_interval':     gen_reals[3],
            'start_easting':    gen_reals[4],
            'column_interval':  gen_reals[5],
            'year':             gen_ints[0],
            'month':            gen_ints[1],
            'day':              gen_ints[2],
            'hour':             gen_ints[3],
            'min':              gen_ints[4]}
    return result


def unzip(gzip_fname):
    """
    uncompression of gzip file
    """
    with gzip.open(gzip_fname, 'rb') as in_file:
        s = in_file.read()
    # Now store the uncompressed data
    path_to_store = gzip_fname[:-3]  # remove the '.gz' from the filename
    # store uncompressed file data from 's' variable
    with open(path_to_store, 'w') as f:
        f.write(s)


def untar(fname):
    """
    extracting files from tar
    """
    tar = tarfile.open(fname)
    tar.extractall(path=_TEMP_FOLDER)
    tar.close()


def extract(tar_file):
    """
    extract all data files from the tar-file into a temporary directory and unzip them

    """
    untar(tar_file)
    for i in [os.path.join(_TEMP_FOLDER, gzip_file) for gzip_file in os.listdir(_TEMP_FOLDER)]:
        if i.endswith('.gz'):
            unzip(i)


def warp(nimrod_dataset):
    """
    Warps the data array into one that has longitude/latitude as axes an fits
    the EPSG:4326 spatial reference system. The original array has the srs
    EPSG:27700 (OSGB 1936).
    :param nimrod_dataset: dictionary containing the data from the NIMROD file
    """

    # http://gis.stackexchange.com/questions/139906/replicating-result-of-gdalwarp-using-gdal-python-bindings
    # Create synthetic data
    gtiff_drv = gdal.GetDriverByName('MEM')
    cols, rows = nimrod_dataset['cols'], nimrod_dataset['rows']
    raster = np.reshape(nimrod_dataset['data'], (cols, rows))
    raster = np.int16(raster)
    top_left = (nimrod_dataset['start_easting'], nimrod_dataset['start_northing'])
    pixel_height = nimrod_dataset['column_interval']
    pixel_width = nimrod_dataset['row_interval']

    src_srs = osr.SpatialReference()
    src_srs.ImportFromEPSG(27700)

    src_geotran = [top_left[0], pixel_width,           0,
                   top_left[1],     0,      -pixel_height]

    rows, cols = raster.shape
    src_ds = gtiff_drv.Create(
        'test_epsg3413.tif',
        cols, rows, 1,
        gdal.GDT_Byte)
    src_ds.SetGeoTransform(src_geotran)
    src_ds.SetProjection(src_srs.ExportToWkt())
    src_ds.GetRasterBand(1).WriteArray(raster)

    # Transform to EPSG: 4326
    dest_srs = osr.SpatialReference()
    dest_srs.ImportFromEPSG(4326)

    int_ds = gdal.AutoCreateWarpedVRT(src_ds, src_srs.ExportToWkt(), dest_srs.ExportToWkt())
    nimrod_dataset['data_warped'] = int_ds.GetRasterBand(1).ReadAsArray()
    nimrod_dataset['GeoTransform'] = int_ds.GetGeoTransform()

    src_ds = None
    int_ds = None

    return nimrod_dataset


def nimrod_to_nc(nimrod_file_list, ncoutfilename):
    """
    Converts the nimrod data into netCDF. The output netCDF has the dimensions
      * Timestamp
      * Longitude
      * Latitude

    :param list nimrod_file_list: list of files that should be added to the netCDF.
      These are the extracted and unzipped data files from the tar-file. The tar
      file contains all the files for one day in five minute timestamps (288 files).
    :param string ncoutfilename: name of the new netCDF that will be created
    """

    # check that nimrod_file_list is not a string or unicode and convert to
    # list if so
    if isinstance(nimrod_file_list, (str, unicode)):
        nimrod_file_list = [nimrod_file_list,]

    nimrod_list = []
    for f in nimrod_file_list:
        # Only work with the uncompressed files
        if ((os.path.exists(f)) and (f.endswith('.dat'))):
            nimrod_list.append(read_nimrod(f))

    ds = netCDF4.Dataset(ncoutfilename, 'w', clobber=True)

    #GeoTransformInfo = None

    pool = Pool(processes=_NUM_PROCESSES)
    nimrod_list = pool.map(warp, nimrod_list)

    nimrod_list.sort(key=lambda x: datetime.datetime(x['year'], x['month'], x['day'], x['hour'], x['min']))

    GeoTransformInfo = nimrod_list[0]['GeoTransform']

    rows, cols = nimrod_list[0]['data_warped'].shape

    ds.Conventions = "CF-1.6"

    # Create the dimensions
    ds.createDimension('lon', int(cols))
    ds.createDimension('lat', int(rows))
    ds.createDimension('timestamp', None)

    lat = ds.createVariable('lat', np.float32, ('lat',))
    lat.units = 'degrees_north'
    lat.standard_name = 'latitude'
    lat.valid_range = [-90.0, 90.0]

    lon = ds.createVariable('lon', np.float32, ('lon',))
    lon.units = 'degrees_east'
    lon.standard_name = 'longitude'
    lon.valid_range = [-180.0, 180.0]

    times = ds.createVariable('timestamp', np.float64, ('timestamp',))
    times.units = 'hours since 0001-01-01 00:00:00'
    times.calendar = 'gregorian'

    # The zlib option is awesome. The compression makes the result much smaller
    rain = ds.createVariable('rain_intensity', np.float32, ('lat', 'lon', 'timestamp'), fill_value=-9999., zlib=True)
    rain.units = 'mm/hr'

    lon[:] = GeoTransformInfo[0] + np.arange(cols, dtype=np.float32) * GeoTransformInfo[1]
    lat[:] = GeoTransformInfo[3] + np.arange(rows, dtype=np.float32) * GeoTransformInfo[5]

    times[:] = netCDF4.date2num([datetime.datetime(nimrod['year'],
                                                   nimrod['month'],
                                                   nimrod['day'],
                                                   nimrod['hour'],
                                                   nimrod['min']) for nimrod in nimrod_list], units = times.units, calendar = times.calendar)

    data = np.zeros((rows, cols, len(nimrod_list)), dtype=np.float32)
    for i in range(len(nimrod_list)):
        data[:,:,i] = np.array(nimrod_list[i]['data_warped'], dtype=np.float32)/32.

    data[data <= 0] = -9999.
    rain[:] = data

    ds.sync()
    ds.close()
    return


def _argparser():
    import argparse
    from argparse import RawTextHelpFormatter
    sys.argv.insert(0, 'faampy nimrod_to_nc')
    parser=argparse.ArgumentParser(description=__doc__,
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('rain_radar_tar_file', action="store", type=str, help='MetOffice compressed rain radar file')
    parser.add_argument('-n', '--number_of_processes', action="store", type=int, required=False,
                        default=2,
                        help='Number of processes that can be used.')
    parser.add_argument('-o', '--outpath', action="store", type=str, required=False,
                        default=os.path.expanduser('~'),
                        help='Directory where the netCDF file will be stored. Default: $HOME.')
    return parser    

    
def main():    
    global _NUM_PROCESSES
    start_time = time.time()
    parser = _argparser()
    args = parser.parse_args()
    _NUM_PROCESSES = args.number_of_processes
    extract(args.rain_radar_tar_file)
    nimrod_file_list = [os.path.join(_TEMP_FOLDER, f) for f in os.listdir(_TEMP_FOLDER)]
    ncoutfilename = os.path.join(args.outpath, os.path.basename(args.rain_radar_tar_file).split('.')[0]+'.nc')
    nimrod_to_nc(nimrod_file_list, ncoutfilename)
    # Delete the _TEMP_FOLDER where we kept all the unzipped files
    shutil.rmtree(_TEMP_FOLDER)
    sys.stdout.write('Done ... ')
    sys.stdout.write('Processing time %i seconds ... \n' % (time.time()-start_time))
    sys.stdout.write('netCDF written to\n    %s.\n' % ncoutfilename)


if __name__ == '__main__':
    main()
