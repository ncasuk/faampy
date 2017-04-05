# -*- coding: utf-8 -*-

import itertools
import rdp             #  Ramer-Douglas-Peucker algorithm (RDP)
import netCDF4
import numpy as np
import datetime
import os
import osgeo.ogr
import pandas as pd
import re
import sys


DEBUG = True


NETCDF_VARIABLE_IDS = """515,Time
516,IAS_RVSM
517,TAS_RVSM
520,TAT_DI_R
525,TAT_ND_R
529,TDEW_GE
535,LWC_JW_U
537,BTHEIM_U
538,INU_ACLF
539,INU_ACLS
540,INU_ACLU
548,AOA
549,AOSS
557,INU_VZ
560,INU_ROLL
561,INU_PTCH
562,INU_HDG
563,INU_GSPD
564,INU_DRFT
565,INU_PITR
566,INU_HDGR
567,INU_ROLR
568,CPC_CONC
572,TWC_EVAP
574,O3_TECO
575,HGT_RADR
576,PS_RVSM
577,Q_RVSM
578,PALT_RVS
579,CAB_PRES
580,LAT_GPS
581,LON_GPS
582,GPS_ALT
583,GPS_VELN
584,GPS_VELE
585,GPS_VELZ
602,NV_LWC_U
605,NV_TCW_U
616,ROLL_GIN
617,PTCH_GIN
618,HDG_GIN
620,TRCK_GIN
621,GSPD_GIN
622,ROLR_GIN
623,PITR_GIN
624,HDGR_GIN
625,ACLF_GIN
626,ACLS_GIN
627,ACLD_GIN
642,SOL_AZIM
643,SOL_ZEN
648,PSAP_LIN
649,PSAP_LOG
660,CAB_TEMP
664,TWC_DET
666,TWC_TSAM
674,UPP_VIS_RED_SIG
673,UPP_VIS_CLR_SIG
675,UPP_I/R_SIGNAL
676,UPP_VIS_CLR_ZERO
677,UPP_VIS_RED_ZERO
678,UPP_I/R_ZERO
679,UPP_VIS_CLR_TEMP
680,UPP_VIS_RED_TEMP
681,UPP_I/R_TEMP
682,LWR_VIS_CLR_SIG
683,LWR_VIS_RED_SIG
684,LWR_I/R_SIGNAL
685,LWR_VIS_CLR_ZERO
686,LWR_VIS_RED_ZERO
687,LWR_I/R_ZERO
688,LWR_VIS_CLR_TEMP
689,LWR_VIS_RED_TEMP
690,LWR_I/R_TEMP
714,V_C
715,U_C
716,W_C
723,BTHEIM_C
724,LWC_JW_U
725,TWC_TDEW
730,LAT_INUC
731,LON_INUC
735,VN_INUC
736,VE_INUC
610,LAT_GIN
611,LON_GIN
612,ALT_GIN
613,VELN_GIN
614,VELE_GIN
615,VELD_GIN
760,NEPH_PR
761,NEPH_T
762,TSC_BLUU
763,TSC_GRNU
764,TSC_REDU
765,BSC_BLUU
766,BSC_GRNU
767,BSC_REDU
770,NO_TECO
771,NO2_TECO
772,NOX_TECO
773,P0_S10
774,PA_TURB
775,PB_TURB
778,P9_STAT
779,TAS
781,PSP_TURB
782,CO_AERO
1019,SW_DN_C
1020,RED_DN_C
1021,IR_DN_C
1022,SW_UP_C
1023,RED_UP_C
1024,IR_UP_C"""


def flatten(l):
    """
    flattens a list
    """
    return [item for sublist in l for item in sublist]


class Translator(dict):
    """
    Dictionary for translating old variable names like 'PARA0515' to more 
    meaningful names as they have been in us more recently. This nomination was
    used for early FAAM flights and was inherited from MRF days.

    """
    def __init__(self):
        keys = ['PARA%.4i' % int(i.split(',')[0]) for i in NETCDF_VARIABLE_IDS.split('\n')]
        keys += ['PARA%.4iFLAG' % int(i.split(',')[0]) for i in NETCDF_VARIABLE_IDS.split('\n')]
        vals = [i.split(',')[1].strip() for i in NETCDF_VARIABLE_IDS.split('\n')]
        vals += [i.split(',')[1].strip()+'_FLAG' for i in NETCDF_VARIABLE_IDS.split('\n')]
        for k,v in zip(keys, vals):
            self[k] = v


class Coords(list):

    def __init__(self, epsilon=0.01):
        self.Simple_mask = []
        self.Epsilon = epsilon

    def as_wkt(self, simplified=False, as_type='MULTIPOINT'):
        """
        Returns the coordinates in well-known text format

        :param boolean simplified: If set returns a geometry with a reduced
        number of points

        """
        if simplified:
            xyz = self.simplified()
        else:
            xyz = self

        if as_type.upper().startswith('LINESTRING'):
            return "LINESTRINGZ(" + ','.join(['%f %f %f' % tuple(item) for item in xyz]) + ")"
        elif as_type.upper() == 'MULTIPOINT':
            return "MULTIPOINT(" + ','.join(['%f %f %f' % tuple(item) for item in xyz]) + ")"
        elif as_type.upper() == 'POINT':
            return ["POINT(%f %f %f)" % tuple(item) for item in xyz]


    def as_kml(self, simplified=True, extrude=1, tessellate=1):
        """
        Return kml formatted string
        
        """
        if simplified:
            xyz = self.simplified()
        else:
            xyz=self
        kml = "<LineString>"
        kml += "<extrude>"
        kml += str(extrude)
        kml += "</extrude>"
        kml += "<tessellate>"
        kml += str(tessellate)
        kml += "</tessellate>"
        kml +="<coordinates>"
        kml += '\n'.join(['%f,%f,%f' % tuple(item) for item in xyz])
        kml +="</coordinates>"
        kml += "</LineString>"
        return kml

    def get_bbox(self):
        """
        Returns boundary box for the coordinates. Useful for setting up
        the map extent for plotting on a map.
        :return tuple:  corner coordinates (llcrnrlat, urcrnrlat, llcrnrlon,
          urcrnrlon)
        """
        x, y, z = zip(self)
        llcrnrlat = np.nanmin(y)
        urcrnrlat = np.nanmax(y)
        llcrnrlon = np.nanmin(x)
        urcrnrlon = np.nanmax(x)
        return (llcrnrlat,
                urcrnrlat,
                llcrnrlon,
                urcrnrlon)

    def _simplify_(self, step=10):
        """
        Simplifies the coordinates by reducing the number using the
        Ramer-Douglas-Peucker algorithm (RDP). The list of coordinates
        itself is not shrinked, but rather a mask array is produced. If
        *self.simplified* is called the mask is used as an index.

        :param int step: step size for array slices. Using only every
          10th value for example speeds things up considerably.
        """

        xyz = [list(i) for i in self]  # copy the coordinates into a list
        # in the case that the first and the last coordinate are identical the
        # rdp algorithmen fails; a quick pop fixes that
        while xyz[0] == xyz[-1]:
            xyz.pop()
            self.pop()
        # use only every 10th value to speed things up
        # TODO: impact should be checked at some point
        m = rdp.rdp(xyz[::step], epsilon=self.Epsilon, return_mask=True)
        # flatten = lambda l: [item for sublist in l for item in sublist]
        m = flatten([[m, ]+(step-1)*[False] for i in m])
        while len(m) < self.__len__():
            m.append(False)
        self.Simple_mask = m
        return

    def simplified(self):
        """
        Returns the reduced number of coordinates
        """
        if not self.Simple_mask:
            self._simplify_()
        return list(itertools.compress(self, self.Simple_mask))


class FAAM_Dataset(object):
    """
    Dataset class which has much in common with the netCDF4.Dataset. The class
    has methods that helps to perform common tasks.

    """

    def __init__(self, filename):
        """
        :param filename: FAAM core filename to read in
        """

        translate = Translator()
        self.coords = Coords()
        self.variables = {}
        self.ds = netCDF4.Dataset(filename, 'r')
        self.ds.set_auto_mask(False)

        self.ncattr = {}
        self.ncattr['Conventions'] = 'NCAR-RAF/nimbus'
        self.ncattr['Version'] = '1.5'
        # Get all the variables and copy them over
        for var_name in self.ds.variables.keys():
            # Fix and oddity where the variables was named altitude
            if var_name == 'altitude':
                self.variables['ALT_GIN'] = self.ds.variables[var_name]
            # Make sure that time variable is always
            # called Time and not TIME or time
            elif var_name.lower() == 'time':
                self.variables['Time'] = self.ds.variables[var_name]
            elif var_name.startswith('PARA'):
                self.variables[translate[var_name]] = self.ds.variables[var_name]
                nan_ix = np.isnan(self.variables[translate[var_name]])
                self.variables[translate[var_name]][:][nan_ix] = -9999.0
            else:
                self.variables[var_name] = self.ds.variables[var_name]
                nan_ix = np.isnan(self.variables[var_name])
                self.variables[var_name][:][nan_ix] = -9999.
            # make sure that there are no nan's in the data

        # Copy all the global attributes
        for attr in self.ds.ncattrs():
            self.ncattr[attr] = self.ds.__getattribute__(attr)

        # make sure that FLIGHT and DATE are set as global attributes
        if 'FLIGHT' in self.ncattr.keys():
            if 'TITLE' in self.ncattr.keys():
                self.ncattr['FLIGHT'] = self.TITLE.split()[2].lower()
            elif 'FLIGHT_NUMBER' in self.ncattr.keys():
                self.ncattr['FLIGHT'] = self.FLIGHT_NUMBER.lower()

        if 'Time' in self.ds.variables.keys():
            dt = datetime.datetime.strptime(str(self.ds.variables['Time'].units).strip(), 'seconds since %Y-%m-%d 00:00:00 +0000')
        elif 'TIME' in self.ds.variables.keys():
            dt = datetime.datetime.strptime(str(self.ds.variables['TIME'].units).strip(), 'seconds since %Y-%m-%d 00:00:00 +0000')
        elif 'time' in self.ds.variables.keys():
            dt = datetime.datetime.strptime(re.findall('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', self.ds.variables['time'].units)[0], '%Y-%m-%d 00:00:00')
        elif hasattr(self.ds, 'Flight_Date'):
            dt = datetime.datetime.strptime(self.ds.Flight_Date, '%d-%b-%y')
        elif 'PARA0515' in self.ds.variables.keys():
            dt = datetime.datetime.strptime(self.ds.title.split()[-1], '%d-%b-%y')
        else:
            dt = datetime.datetime(self.ds.DATE[2], self.ds.DATE[1], self.ds.DATE[0])
        self.ncattr['DATE'] = [dt.day, dt.month, dt.year]

        if 'WOW_IND' not in self.variables.keys():
            # Estimate the WOW_IND using indicated air speed
            wow = np.array([1]*self.variables['Time'].size)
            if len(self.variables['IAS_RVSM'].shape) == 1:
                ias_rvsm=self.variables['IAS_RVSM'][:]
            else:
                ias_rvsm=self.variables['IAS_RVSM'][:,0]
            ix = np.where((ias_rvsm > 60) & (ias_rvsm < 300))[0]
            wow[ix] = 0
            self.variables['WOW_IND'] = wow[:]

        # using the more sophisticated np.datetime64 data type
        base_time = np.datetime64('%i-%0.2i-%0.2iT00:00:00' % (self.ncattr['DATE'][2], self.ncattr['DATE'][1], self.ncattr['DATE'][0]))

        self.index = base_time + np.array(self.variables['Time'][:].ravel(), dtype=np.int)

        self._set_coordinates_()

        self.Geometry=osgeo.ogr.CreateGeometryFromWkt("LINESTRING (" + ','.join(['%f %f %f' % tuple(i) for i in self.coords.simplified()])+ ")")

    def _set_coordinates_(self):
        lon_var_name = None
        if 'LAT_GIN' in self.variables.keys():
            lon_var_name = 'LON_GIN'
            lat_var_name = 'LAT_GIN'
            alt_var_name = 'ALT_GIN'
            self.ncattr['Coordinates'] = 'LON_GIN LAT_GIN ALT_GIN Time'
        elif 'LAT_GPS' in self.variables.keys():
            lon_var_name = 'LON_GPS'
            lat_var_name = 'LAT_GPS'
            alt_var_name = 'GPS_ALT'
            self.ncattr['Coordinates'] = 'LON_GPS LAT_GPS GPS_ALT Time'
        if not lon_var_name:
            return
        if self.variables[lon_var_name].size == 0:
            return

        if len(self.variables[lon_var_name][:].shape) > 1:
            x = self.variables[lon_var_name][:, 0].ravel()
            y = self.variables[lat_var_name][:, 0].ravel()
            z = self.variables[alt_var_name][:, 0].ravel()
        else:
            x = self.variables[lon_var_name][:].ravel()
            y = self.variables[lat_var_name][:].ravel()
            z = self.variables[alt_var_name][:].ravel()

        wow = self.variables['WOW_IND']

        # filter good values
        ix = np.where((x > -180) & (x < 180) & (y > -90) & (y < 90) & (z != -9999.0) & (x != 0.0) & (wow != 1))[0]
        for i in zip(list(x[ix]), list(y[ix]), list(z[ix])):
            self.coords.append(i)
        return

    def merge(self, recarray, index='', varnames=[], delay=0):
        """
        Merges in a numpy recarray with the FAAM_Dataset using concurring
        timestamps

        :param recarray: A numpy numpy.recarray with named data
        :type recarray: numpy.recarray
        :param index: Name of the column/field that contains the timestamp.
          Note that the merging only works on timestamps. The maximum time
          resolution is 1sec.
        :type index: str
        :param varnames: List of varnames that
        :type varnames: list of strings
        :param int delay: instruments have a time offset compared to the core
          data. For example the FGGA is 4 seconds slow the delay keyword takes
          this delay into account in seconds
        """
        BASE_TIME = self.index[0]

        if not varnames:
            other_var_names = list(recarray.dtype.names)

        if not index:
            # This needs testing
            # guess field name for index by loopin through some common names
            recarray_keys = recarray.dtype.fields.keys()
            index_name_list = ['timestamp', 'time', 'datetime']
            for i, name in enumerate(index_name_list):
                if name in [item.lower() for item in recarray_keys]:
                    index = recarray_keys[i]
                    break

            # if we made it that far we don't have a proper index name
            sys.stdout.write('No index for merging found ... Leaving ...\n')
            return

        else:

            other_index = recarray[index]
            # Need to make sure that the datatype is datetime64[s] otherwise
            # the merging does not work
            #other_index = np.int32(other_index.astype('datetime64[s]'))
            if index in other_var_names:
                other_var_names.remove(index)

        # The following stuff does what reverse_indices in idl does,
        # does not work with the datetime64 data type. We simplify
        # things by converting it to secs since BASE_TIME
        # so that we can work with two integer numbers
        own_index = np.array(self.index-BASE_TIME, dtype=np.int32)
        other_index = np.int32((recarray['timestamp']-BASE_TIME).astype('timedelta64[s]'))
        bins = np.linspace(own_index[0]-0.5, own_index[-1]+0.5, (len(own_index)+1))
        ind = np.digitize(other_index, bins)-1
        ind_mask = np.select([ind < 0, ind >= len(bins)-1], [0, 0], default=1)

        for other_var_name in other_var_names:
            #Make sure that the data are numbers and not string or object type
            if recarray[other_var_name].dtype in [np.dtype(np.object), np.dtype(np.str)]:
                continue
            new_array = np.array([np.nan, ]*len(own_index))
            new_array[ind[ind_mask == 1]] = recarray[other_var_name][ind_mask == 1]
            if delay:
                new_array = np.roll(new_array, delay)
                new_array[-delay] = np.nan
            self.variables[other_var_name] = np.copy(new_array)

    def as_dataframe(self, varnames=[]):
        """
        Returns the Dataset as a pandas.Dataframe using the timestamp as index,
        which opens the world of pandas to you. Only the first column of two
        dimensional data sets is grabbed, because pandas does not handle
        multidimensional data very well.

        :param varnames: list of variable names that should be exported as
          DataFrame. By default all are exported
        :type varnames: list
        :return: returns a pandas Dataframe with the Timestamp as index
        :type return: pandas.Dataframe
        """
        if not varnames:
            varnames = sorted(self.variables.keys())
            varnames.remove('Time')
        else:
            varnames = list(set(self.variables.keys()).intersection(varnames))

        df = pd.DataFrame(index=self.index)
        for v in varnames:
            shp = self.variables[v].shape
            if len(shp) == 2:
                data = np.copy(self.variables[v][:, 0])
            else:
                data = np.copy(self.variables[v][:])
            df_tmp = pd.DataFrame(data[:], index=self.index, columns=[v, ])
            df = pd.concat([df, df_tmp], axis=1)
        #set all missing values to nan
        df[df == -9999.0] = np.nan
        #set timezone to None otherwise there might be issues merging the data
        #frame with others
        #df.index.tz=None
        return df

    def as_kml(self, extrude=1, tessellate=1):
        """
        Returns a kml linestring which represents the flight track of the current
        dataset

        :param extrude: whether the linestring is extruded
        :type extrude: boolean
        :param tessellate: whether the linestring is extruded
        :type tessellate: boolean
        :return: kml string
        """
        template = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Folder>
    <name>%s-%s-Flight-Track</name>
        <open>0</open>
        <Placemark>
          <name>%s</name>
        %s
        </Placemark>
        </Folder>
</kml>
"""
        linestring = "<LineString>"
        linestring += "<extrude>%s</extrude><tessellate>%s</tessellate>" % (str(extrude), str(tessellate))
        linestring += (''.join(self.Geometry.ExportToKML().split('<LineString>')))
        kml = template % (self.FLIGHT,
                          datetime.datetime(self.DATE[2], self.DATE[1], self.DATE[0]).strftime('%Y-%m-%d'),
                          self.FLIGHT,
                          linestring)
        return kml

    def close(self):
        """
        Closing the Dataset
        """
        self.ds.close()

    def write(self, outfilename, v_name_list=[], as_1Hz=True, clobber=False):
        """
        Writing the dataset out as netCDF

        :param outfilename: path for the new netCDF
        :type outfilename: str
        :param v_name_list: list of variables names that should be written. By
          default all variables are added to the netCDF
        :type v_name_list: list  
        :param as_1Hz: Writes only 1Hz data out. If the variable
          is avaiable in higher frequency only the first value within the
          second is used rather than the average from the number of data
          points
        :type as_1Hz: boolean
        :param clobber: Overwrites the files if it exists  
        :type clobber: boolean
        """

        if os.path.exists(outfilename) :
            if not clobber:
                sys.stdout.write('File exists ... Leaving ...\n')
                return
            else:
                sys.stdout.write('File exists ... Will overwrite it ...\n')

        # create the netCDF4 output dataset        
        dsout = netCDF4.Dataset(outfilename, 'w', clobber=clobber)

        # Write the global attributes
        for k, v in self.ncattr.items():
            dsout.setncattr(k ,v)

        # Now the dimensions
        for dname, the_dim in self.ds.dimensions.iteritems():
            dsout.createDimension(dname, len(the_dim) if not the_dim.isunlimited() else None)
        #dsout.createDimension('Time', None)
        if not v_name_list:
            self.variables.keys()
        # Writing the variables
        for v_name in v_name_list:
            varin = self.variables[v_name]

            if hasattr(varin, 'datatype'):
                datatype = varin.datatype
                dimensions = varin.dimensions
            else:
                datatype='f8'
                dimensions = ('Time', 'sps01')

            if as_1Hz:
                outVar = dsout.createVariable(v_name, datatype, ('Time',), fill_value=-9999.)
                if hasattr(varin, 'getncattr'):
                    outVar.setncatts({k: varin.getncattr(k) for k in varin.ncattrs()})
                if len(self.variables[v_name].shape) == 2:
                    outVar_data = self.variables[v_name][:,0]
                else:
                    outVar_data = self.variables[v_name][:]
            else:
                outVar = dsout.createVariable(v_name, datatype, dimensions)
                if hasattr(varin, 'getncattr'):
                    outVar.setncatts({k: varin.getncattr(k) for k in varin.ncattrs()})
                outVar_data = self.variables[v_name][:]
            outVar_data[np.isnan(outVar_data)] = -9999.
            outVar[:] = outVar_data
        dsout.close()
