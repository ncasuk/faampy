'''
Created on 1 Apr 2012

@author: axel
'''


import matplotlib.pyplot as plt
import netCDF4
import numpy as np
import os
import random
from scipy.interpolate import griddata

from read_ch4 import *

def flux_calculator(ch4_conc, temp, wspd, p, Z, MOLECULAR_MASS):
    #see: http://en.wikipedia.org/wiki/Air_pollutant_concentrations

    #ppbV to mass per volume units, adjust for altitude effect
    mass = (ch4_conc *  MOLECULAR_MASS * p/10.) / (8.3144 * temp)
    flux = mass * wspd
    #convert to kg/m**3
    flux = flux / (1000. * 1000. * 1000.)
    return flux
                                         

def calc_wspd_profile(u_star, d, z_0, Z):    
    """logarithmic wind speed formula"""
    KARMAN_CONSTANT = 0.41
    result = u_star/KARMAN_CONSTANT * np.log((Z-d) / z_0)
    return result


def calc_pressure_profile(p_0, temp, Z):
    a = 0.0342 
    result = p_0 * np.exp(-(a/temp)*Z)
    return result


def calc_temperature_profile(t_0, Z):
    lapse_rate = 0.0065
    result = t_0 - Z * lapse_rate
    return result


def profile2array(arr, x_size):
    """convert profile to array by repeating profile"""
    result = np.empty((x_size, len(arr)))
    for i in range(x_size):
        result[i,:] = arr[:]    
    return result


def translate_coord(lon, lat, ORIGIN):
    """coordinate translation to a global origin"""
    start_long = lon*0 + np.radians(ORIGIN[0])
    start_latt = lat*0 + np.radians(ORIGIN[1])
    end_long = np.radians(lon)
    end_latt = np.radians(lat)

    d_latt = end_latt - start_latt
    d_long = end_long - start_long
    d_latt = d_latt * 0.0
    a = np.sin(d_latt/2)**2 + np.cos(start_latt) * np.cos(end_latt) * np.sin(d_long/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    x = 6371.0 * c * 1000.0
    ix = np.where(end_long < start_long)
    x[ix] = x[ix] * -1.0
    
    d_latt = end_latt - start_latt
    d_long = end_long - start_long
    d_long = d_long * 0.0
    a = np.sin(d_latt/2)**2 + np.cos(start_latt) * np.cos(end_latt) * np.sin(d_long/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    y = 6371.0 * c * 1000.0
    ix = np.where(end_latt < start_latt)
    y[ix] = y[ix] * -1.0
    
    return(x,y)


def rotate_coord(x, y, angle):
    """coordinate system rotation"""
    x_rot = x * np.cos(np.deg2rad(angle)) + y * np.sin(np.deg2rad(angle))
    y_rot = -x * np.sin(np.deg2rad(angle)) + y * np.cos(np.deg2rad(angle))
    return(x_rot, y_rot)
                       

def t2s(s):
    """converts time string to seconds past midnight"""
    s = str.strip(s)
    result = int(s[0:2]) * 3600 + int(s[2:4]) * 60 + int(s[4:6])
    return result


def get_index(ds, secs):
    """get index for time_stamp in core netcdf file"""
    ix = np.where(ds.variables['Time'][:] == secs)
    return ix[0]


def run_model(ncfile, fgga_file, PARAMS, quiet=False):

    #unwrap PARAMS dictionary
    for k in PARAMS.keys():
        cmd = "%s = PARAMS['%s']" % (k, k)
        exec(cmd)

    ds = netCDF4.Dataset(ncfile, 'r')
    ch4_data = read_fgga(fgga_file, time_lag=20.8)

    s_ix = get_index(ds, t2s(S_TIME))
    e_ix = get_index(ds, t2s(E_TIME))
    #lon,lat,hgt from core netcdf
    lon = ds.variables['LON_GIN'][:][s_ix:e_ix]
    lat = ds.variables['LAT_GIN'][:][s_ix:e_ix]
    hgt = ds.variables['HGT_RADR'][:][s_ix:e_ix]
    x, y = translate_coord(lon, lat, ORIGIN)
    x, y = rotate_coord(x, y, ROT_ANGLE)
    
    
    s_ch4_ix = np.argmin(np.abs(ch4_data[:,0] - t2s(S_TIME)))
    e_ch4_ix = np.argmin(np.abs(ch4_data[:,0] - t2s(E_TIME)))
    ch4_conc = ch4_data[s_ch4_ix:e_ch4_ix,3]
    
    grid_x, grid_y = np.mgrid[X_DIM[0]:X_DIM[1], Z_DIM[0]:Z_DIM[1]]


    #not nice
    #A FIX fix to get values down below the lowest flight track
    #copying all values that were measured belos MIN_HGT to 0 altitude
    #extrapolation would probably be a better solution 
    hgt_ix = np.where(hgt < MIN_HGT)[0]   
    x = np.concatenate((x, x[hgt_ix]))
    hgt = np.concatenate((hgt, hgt[hgt_ix]*0.0))
    ch4_conc = np.concatenate((ch4_conc, ch4_conc[hgt_ix]))

    pairs = (( 48.0,    5.21),
             (151.0,  421.78),
             (243.0, -332.33),
             (305.0, -312.20))

    for p in pairs:
        ix = np.where(np.abs(hgt - p[0]) < 20)[0]
        x[ix] = x[ix] - p[1]


    data = np.vstack((x.ravel(), hgt.ravel(), ch4_conc)).T
    
    ch4_conc = griddata((x.ravel(), hgt.ravel()), ch4_conc.ravel(), (grid_x, grid_y), method='linear')
    ch4_conc = ch4_conc - CH4_BACKGROUND   

    wspd_profile = calc_wspd_profile(U_STAR, D, Z_0, Z)
    wspd_array = profile2array(wspd_profile, len(X))

    temp_profile = calc_temperature_profile(T_0, Z)
    temp_array = profile2array(temp_profile, len(X))

    press_profile = calc_pressure_profile(QNH, temp_profile, Z)
    press_array = profile2array(press_profile, len(X))

    flux = flux_calculator(ch4_conc, temp_array, wspd_array, press_array, Z, CH4_MOLECULAR_MASS)
    total_flux = np.nansum(flux)
    if not quiet:
        print('TOTAL CH4-flux (kg/s): %6.3f' % (total_flux))
    ds.close()
    return (total_flux, flux, ch4_conc, data)


def plot_concentration(X, Z, ch4_conc,fid, plume_id, fig_path, title):    
    plt.clf()
    max_level = int(np.ceil(np.nanmax(ch4_conc)/50.) * 50.) 
    step_level = int(np.floor(max_level)/100.) 
    levels = range(0, max_level, step_level)
    cs = plt.contourf(X, Z, ch4_conc.T, levels, linewidth=0)
    plt.xlabel('distance from origin (m)')
    plt.ylabel('height a.s.l. (m)')
    cbar = plt.colorbar()
    cbar.ax.set_ylabel(r'$\mathrm{CH_4}$ concentration above background (ppb)')
    plt.title(title)
    for c in cs.collections:
        c.set_antialiased(False)
        plt.draw()        
        #plt.savefig(os.path.join(fig_path, ('%s_%s_ch4conc.png') % (fid, plume_id)), dpi=100)
    return plt.gcf()


def plot_flux(X, Z, flux, fid, plume_id, fig_path, title):
    plt.clf()
    max_level = int(np.ceil(np.nanmax(flux*1000*1000.)))
    step_level = 0.05 
    levels = np.array(range(0, max_level*20, 1)) * step_level    
    cs = plt.contourf(X, Z, flux.T*1000*1000, levels)
    plt.xlabel('distance from origin (m)')
    plt.ylabel('height a.s.l. (m)')
    cbar = plt.colorbar()
    cbar.ax.set_ylabel(r'$\mathrm{CH_4 flux (mg \cdot m^2 \cdot s))}$')
    plt.title(title)
    for c in cs.collections:
        c.set_antialiased(False)
        plt.draw()
    plt.savefig(os.path.join(fig_path, ('%s_%s_ch4flux.png') % (fid, plume_id)), dpi=100)
    return plt.gcf()


def calc_uncertainties(n, PARAMS):

    #unwrap PARAMS dictionary
    for k in PARAMS.keys():
        cmd = "%s = PARAMS['%s']" % (k, k)
        exec(cmd)

    result = []
    for i in range(n):
        tmp_params = PARAMS
        tmp_params['CH4_BACKGROUND'] = random.gauss(CH4_BACKGROUND, CH4_BACKGROUND_UNC)
        tmp_params['T_0'] = random.gauss(T_0, T_0_UNC)
        tmp_params['U_STAR'] = random.gauss(U_STAR, U_STAR_UNC)
        tmp_params['D'] = random.gauss(D, D_UNC)
        tmp_params['Z_0'] = random.gauss(Z_0, Z_0_UNC)
        tmp_params['QNH'] = random.gauss(QNH, QNH_UNC)

        total_flux, flux, ch4_conc = run_model(ncfile, fgga_file, tmp_params, quiet=True)
        result.append(total_flux)
    return result

