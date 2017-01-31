'''
Created on 16 Nov 2011

@author: axel
'''

import netCDF4

def get_sonde_id(ifile):    
    sonde_id=None

    if ifile.endswith('.nc'):
        ds=netCDF4.Dataset(ifile, 'r')
        sonde_id=str.split(str(ds.SoundingDescription))[1]
        ds.close()
        return sonde_id
        
    
    f=open(ifile, 'r')
    lines=f.readlines()
    f.close()
    for line in lines:
        try:
            if line.split()[1] == 'STA' or line.split()[1] == 'LAU':
                sonde_id = line.split()[2]
            elif line.startswith('Sonde ID'):
                sonde_id = line.split()[2][:-1]
            else:
                pass
        except:
            pass
    return sonde_id


def conv_height_to_pressure(gps_alt, p_0=None):
    """Calculates pressure from height using the barometric formula.

    see: http://en.wikipedia.org/wiki/Atmospheric_pressure
    """
    if not p_0:
        p_0 = 1013.25   # sea level standard atmospheric pressure [Pa]
    L=0.0065     # temperature lapse rate [K/m]
    T_0=288.15   # sea level standard temperature [K]
    R=8.31447    # universal gas constant [J/(mol*K)]
    M=0.0289644  # molar mass of dry air [kg/mol]
    g=9.80665    # Earth-surface gravitational acceleration [m/s^2]
    p=p_0 * (1. - (L*gps_alt)/T_0)**((g*M)/(R*L))
    return p


def conv_pressure_to_height(pressure, p_0=None):
    """Calculates height from pressure using the barometric formula.

    see: http://en.wikipedia.org/wiki/Atmospheric_pressure
    """
    if not p_0:
        p_0=1013.25   # sea level standard atmospheric pressure [Pa]
    L=0.0065     # temperature lapse rate [K/m]
    T_0=288.15   # sea level standard temperature [K]
    R=8.31447    # universal gas constant [J/(mol*K)]
    M=0.0289644  # molar mass of dry air [kg/mol]
    g=9.80665    # Earth-surface gravitational acceleration [m/s^2]
    alt=((pressure/p_0)**((R*L)/(g*M)) - 1.0) * (-T_0/L)
    return alt
