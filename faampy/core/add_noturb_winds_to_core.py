#!/usr/bin/python

import ctypes
import netCDF4
import numpy as np


def add_hdg_offset(hdg, hdg_offset):
    """function takes care of angle calculations and substracts 360 if
    hdg is greater than 360 and adds 360 if angle is smaller than 0.
    """
    result = hdg + hdg_offset
    result[np.where(result > 360)] += -360.
    result[np.where(result < 0)] += 360.
    return result


def correct_tas_rvsm(tas_rvsm, dit, tas_scale_factor=None):
    """Correcting true airspeed measurement for temperature effect.
       dit is the deiced temperature measurements.
       
       see: http://en.wikipedia.org/wiki/Airspeed
       
    """
    if not tas_scale_factor:
        tas_scale_factor = 0.9984
    mach = tas_rvsm / (661.4788 * 0.514444) / np.sqrt(dit/288.15)
    delta_tas = 4.0739 - (32.1681 * mach) + (52.7136 * (mach**2))
    tas = (tas_rvsm - delta_tas) * tas_scale_factor
    return tas


def calc_noturb_wspd(tas_rvsm, hdg_gin, gspd_north, gspd_east, dit, hdg_offset=None, tas_scale_factor=None):                                                   
                     
    """calculates u and v as the aircraft does it                                                                                           
                                                                                                                                            
       see: http://delphiforfun.org/programs/Math_Topics/WindTriangle.htm
            http://www.pilotfriend.com/training/flight_training/nav/calcs.htm
 
    """   
    if hdg_offset:
        hdg = add_hdg_offset(hdg_gin, hdg_offset)
    else:
        hdg = hdg_gin
    if not tas_scale_factor:
        tas_scale_factor = 0.9984

    #adjust tas_rvsm for temperature effects
    tas = correct_tas_rvsm(tas_rvsm, dit, tas_scale_factor=tas_scale_factor)
    air_spd_east = np.cos(np.deg2rad(hdg - 90.)) * tas
    air_spd_north = np.sin(np.deg2rad(hdg - 90.)) * tas
    u = gspd_east - air_spd_east
    v = air_spd_north + gspd_north      
    return (u, v)


def calc_noturb_flag(ds, roll_threshold=None):
    """uses the flags for the variables that are used to calculate the 
    noturb winds. noturb wind speeds are invalid in turns. This is taken care of
    by flagging those values using a roll_threshold (default=1.5)
    
    """    
    if not roll_threshold:
        roll_threshold = 1.5
    tas_rvsm_flag = np.max(ds.variables['TAS_RVSM_FLAG'][:], axis=1)
    hdg_gin_flag = np.max(ds.variables['HDG_GIN_FLAG'][:], axis=1)
    gspd_north_flag = np.max(ds.variables['VELN_GIN_FLAG'][:], axis=1)
    gspd_east_flag = np.max(ds.variables['VELE_GIN_FLAG'], axis=1)
    dit_flag = np.max(ds.variables['TAT_DI_R_FLAG'][:], axis=1)

    #flag all data points 3, that exceed roll_threshold
    roll_gin = ds.variables['ROLL_GIN'][:]
    roll_flag = np.where(np.abs(roll_gin) < roll_threshold,
                         roll_gin*0, 
                         roll_gin*0+3)

    flag_data = np.column_stack((tas_rvsm_flag,
                            hdg_gin_flag,
                            gspd_north_flag,
                            gspd_east_flag,
                            dit_flag,
                            roll_flag))
    flag_data = np.max(flag_data, axis=1)
    flag_data[flag_data < 0] = 3
    flag_data[flag_data > 3] = 3
    return flag_data


def add_var_to_core(ds, u_noturb_data, v_noturb_data, flag_data):
    
    freq = 1
    for var_name in ['U_NOTURB', 'V_NOTURB']:
        long_name_templ = "%s wind component derived from aircraft instruments and GIN" 
        if var_name == 'U_NOTURB':
            long_name = long_name_templ % ('Eastward')
            standard_name = "eastward_wind"
            data = u_noturb_data
        else:
            long_name = long_name_templ % ('Northward')
            standard_name = "northward_wind"
            data = v_noturb_data
        
        if not var_name in ds.variables.keys():
            ds.createVariable(var_name, 'f4', dimensions=('data_point', 'sps01'), fill_value=-9999.)
            ds.createVariable(var_name+'_FLAG', 'b', dimensions=('data_point', 'sps01'), fill_value=-1)

        var = ds.variables[var_name]
        var.long_name = long_name
        var.units =  "m s-1         "
        var.frequency = ctypes.c_short(freq)
        #var.standard_name = standard_name
        var = ds.variables[var_name]
        var[:] = data
               
        flag = ds.variables[var_name+'_FLAG']
        flag.long_name = "Flag for %s" % (var.long_name)
        flag.units = "1"
        flag.frequency = ctypes.c_short(freq)
        flag[:] = flag_data
    ds.sync()


def process(ncfile, hdg_offset, tas_scale_factor):
    ds = netCDF4.Dataset(ncfile, 'a')    
    u_noturb, v_noturb = calc_noturb_wspd(ds.variables['TAS_RVSM'][:],
                                  ds.variables['HDG_GIN'][:],
                                  ds.variables['VELN_GIN'][:],
                                  ds.variables['VELE_GIN'][:],
                                  ds.variables['TAT_DI_R'][:],
                                  hdg_offset=hdg_offset,
                                  tas_scale_factor=tas_scale_factor)
    u_noturb = np.mean(u_noturb, axis=1)
    v_noturb = np.mean(v_noturb, axis=1)
    flag_data = calc_noturb_flag(ds)
    add_var_to_core(ds, u_noturb, v_noturb, flag_data)
    ds.close()
    
    
    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Add aircraft derived wind speeds (U_NOTURB, V_NOTURB) to the FAAM core netCDF file.')
    parser.add_argument('ncfile', action="store", type=str,
                        help='core netcdf file')
    parser.add_argument('-t', '--tas_scale_factor', type=float, required=False, 
                        help='tas', default=0.9984)
    parser.add_argument('-o','--hdg_offset', help='Heading offset correction', type=float, required=False, default=0.0)
    args = parser.parse_args()
    process(args.ncfile, args.hdg_offset, args.tas_scale_factor)


#ncfile = '/home/axel/netcdf4_noturb_test.nc'
#process(ncfile, hdg_offset=0, tas_scale_factor=0.9984)
