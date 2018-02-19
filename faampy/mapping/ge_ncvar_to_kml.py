#!/usr/bin/env python

"""
Creates a profile plot for a specfic netCDF variable that is viewable in google-earth.

"""

import datetime
import netCDF4
import numpy as np
import os
import re
import sys

from faampy.core.utils import conv_time_to_secs, conv_secs_to_time, \
                              get_index_from_secs, get_fid


KML_HEADER="""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengi
s.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Folder>
    <name>%s</name>
        <open>1</open>
"""

KML_FOOTER="""</Folder></kml>"""

KML_PLACEMARK_TEMPLATE="""
<Placemark>
        <name>%s@%im</name>
        <open>0</open>
        <Style>
        <LineStyle>
      <color>4b000000</color>
      <width>3</width>
    </LineStyle>
    <PolyStyle>
      <color>32000000</color>
      <fill>1</fill>
      <outline>1</outline>
    </PolyStyle>
  </Style>
  <MultiGeometry>
    <Point>
      <altitudeMode>absolute</altitudeMode>
      <coordinates>
       %.5f,%.5f,%.5f
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


def get_run_kml(run_data, ds, var, offset, scale_factor, time_lag):
    """extracts the data for the specific run
    """
    s_index=get_index_from_secs(ds, conv_time_to_secs(run_data[1]))
    e_index=get_index_from_secs(ds, conv_time_to_secs(run_data[2]))

    lon=ds.variables['LON_GIN'][:]
    if len(lon.shape) > 1:
        lon=lon[s_index:e_index,0]
    else:
        lon=lon[s_index:e_index]
    lon=list(lon)

    lat=ds.variables['LAT_GIN'][:]
    if len(lat.shape) > 1:
        lat=lat[s_index:e_index,0]
    else:
        lat=lat[s_index:e_index]
    lat=list(lat)

    gin_alt=ds.variables['ALT_GIN'][:]
    if len(gin_alt.shape) > 1:
        gin_alt=gin_alt[s_index:e_index,0]
    else:
        gin_alt=gin_alt[s_index:e_index]
    gin_alt=list(gin_alt)

    if len(ds.variables[var][:].shape) > 1:
        alt=(ds.variables[var][:][int(s_index+time_lag):int(e_index+time_lag), 0]+offset)*scale_factor
    else:
        alt=(ds.variables[var][:][int(s_index+time_lag):int(e_index+time_lag)]+offset)*scale_factor

    if var+'_FLAG' in ds.variables.keys():
        alt_flag=ds.variables[var+'_FLAG'][:]
        if len(alt_flag.shape) > 1:
            alt_flag=alt_flag[s_index+time_lag:e_index+time_lag, 0]
        else:
            alt_flag=alt_flag[s_index+time_lag:e_index+time_lag]
        #alt_flag=list(alt_flag)

        alt[alt_flag != 0]=0

    alt=list(alt)

    lon2, lat2, alt2 = [], [], []
    for i in range(len(lon)):
        if np.isfinite([lon[i], lat[i], alt[i]]).all():
            if lon[i] == 0.0:
                continue
            if lat[i] == 0.0:
                continue
            lon2.append(lon[i])
            lat2.append(lat[i])
            alt2.append(alt[i])
    lon = lon2
    lat = lat2
    alt = alt2
    linestring_txt = ['%.5f,%.5f,%.5f' % (lon[i], lat[i], alt[i]) for i in range(len(lon))]
    linestring_txt = '\n'.join(linestring_txt)
    try:
        result = KML_PLACEMARK_TEMPLATE % (run_data[0], gin_alt[0], lon[0], lat[0], alt[0], linestring_txt)
    except:
        result = None
    return result


def process(ncfile, ncvar, time_lag, offset, scale_factor, outpath, *fltsumm):
    ds = netCDF4.Dataset(ncfile, 'r')
    fid = get_fid(ds)
    
    datestring = ''
    
    for v in os.path.basename(ncfile).split('_'):
        try:
            _date = datetime.datetime.strptime(v, '%Y%m%d')
            datestring = _date.strftime('%Y%m%d')
        except:
            pass


    if fltsumm:
        from faampy.core.flight_summary import FlightSummary
        fs = FlightSummary(fltsumm[0])
        _RUNS = []
        for e in fs.Entries:
            if re.findall('run|leg|box', e.Name.lower()):
                _RUNS.append((e.Name, e.Start_time, e.Stop_time))
    else:
        ds = netCDF4.Dataset(ncfile, 'r')
        if 'IAS_RVSM' in ds.variables.keys():
            if len(ds.variables['IAS_RVSM'][:].shape) == 2:
                ias = ds.variables['IAS_RVSM'][:, 0].ravel()
            else:
                ias = ds.variables['IAS_RVSM'][:].ravel()
            if not isinstance(ias, np.ndarray):
                ias = ias.data
                # filter for indicated airspeed greater 60
            ix = np.where(ias > 60)
            ix_min, ix_max = np.min(ix), np.max(ix)
        else:
            ix_min = 60
            v = ds.variables[ds.variables.keys()[0]][:]
            ix_max = v.shape[0]-60

        _RUNS = [('Full flight',
                 conv_secs_to_time(ds.variables['Time'][ix_min], no_colons=True),
                 conv_secs_to_time(ds.variables['Time'][ix_max], no_colons=True)),]

    if datestring:
        kml_filename = os.path.join(outpath, fid+'-'+datestring+'_'+ncvar.lower()+'.kml')
    else:
        kml_filename = os.path.join(outpath, fid+'_'+ncvar.lower()+'.kml')
    kml = open(kml_filename, 'w')
    kml.write(KML_HEADER % (fid + '-' +datetime.datetime(ds.DATE[2], ds.DATE[1], ds.DATE[0]).strftime('%d-%m-%Y') + '-' + ncvar))

    for run in _RUNS:
        run_kml = get_run_kml(run, ds, ncvar, offset, scale_factor, time_lag)
        if not run_kml:
            continue
        kml.write(run_kml)
    kml.write(KML_FOOTER)
    kml.close()
    ds.close()
    return


def _argparser():
    import argparse
    sys.argv.insert(0, 'faampy ge_ncvar_to_kml')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offset', action='store', type=float, default=0.0,
                        help='Offset value. Value is removed from variable before profiles are created')
    parser.add_argument('--scale_factor', action='store', type=float, default=45,
                        help='Scaling factor, mulitplier for the netCDF variable.')
    parser.add_argument('--time_lag', action='store', type=float, default=0.0,
                        help='time lag between variable and GIN measurement caused by inlets')
    parser.add_argument('--fltsumm', action='store', type=str,
                        help='Path to flight summary file for the specific flight')
    parser.add_argument('ncvar', action='store', type=str,
                        help="FAAM core netCDF variable name used for the profile.")
    parser.add_argument('faam_core_netcdf', action='store', type=str,
                        help="FAAM core netCDF data file")
    parser.add_argument('outpath', action='store', type=str,
                        help='Path to where the kml file is written to.')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()

    process(args.faam_core_netcdf,
            args.ncvar,
            args.time_lag,
            args.offset,
            args.scale_factor,
            args.outpath,
            args.fltsumm)


if __name__ == '__main__':
    main()
