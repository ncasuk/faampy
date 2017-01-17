import numpy as np


def is_slr(ds, s_ix, e_ix):
    """Checks if a time interval is a straight and level run using
    the ROLL_GIN and P9_STAT variables from the FAAM core netcdf.
    
    """
    criteria = {'ROLL_GIN': 3, 'P9_STAT': 2}
    roll_gin = ds.variables['ROLL_GIN'][s_ix:e_ix, :]
    p9_stat = ds.variables['P9_STAT'][s_ix:e_ix, :]
    ix1 = (np.where(np.abs(roll_gin ) > criteria['ROLL_GIN']))[0].size
    ix2 = (np.max(p9_stat) - np.min(p9_stat)) > criteria['P9_STAT']
    if ix1 or ix2:
        result = False
    else:
        result = True
    return result


def calc_flight_level(pressure):
    """https://www.brisbanehotairballooning.com.au/faqs/education/113-pressure-altitude-conversion.html
    
    """
    fl = (10**((np.log10(np.array(pressure) / 1013.25))/5.2558797) -1) / (-6.8755856 * 10**-6*100)
    return fl.astype(int)
    

def calc_qnh(pressure, height_amsl):
    """pressure in mb
    and height_amsl: height above mean sea level in meters
    
    http://en.wikipedia.org/wiki/Barometric_formula
    
    """
    L = 0.0065     # temperature lapse rate [K/m]
    T_0 = 288.15   # sea level standard temperature [K]
    R = 8.31447    # universal gas constant [J/(mol*K)]
    M = 0.0289644  # molar mass of dry air [kg/mol]
    g = 9.80665    # Earth-surface gravitational acceleration [m/s^2]
    qnh = pressure / ((1.0 - (L * (height_amsl)/T_0))**((g*M)/(R*L)))
    return qnh


testing = False
if testing:
    print(calc_flight_level(np.array([1000, 900, 800, 700, 400])))
    print(calc_qnh(900., 3200., 40))
    print(calc_qnh(1015., 107., 0.))

