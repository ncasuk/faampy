# -*- coding:utf-8 -*-
"""
Plots skewT-lnP-diagram from WRF-output file.
@author Geir Arne Waagbø
@see http://code.google.com/p/pywrfplot/
 
 Formulas taken from Rogers&Yau: A short course in cloud physics (Third edition)
 Some inspiration from:
 http://www.atmos.washington.edu/~lmadaus/pyscript/plot_wrf_skewt.txt
"""

import math
import netCDF4
import numpy as np
import matplotlib.pyplot as plt

#from pywrfplotParams import T_zero,T_base,kappa,barb_increments,P_bot
#from pywrfplotUtils import gamma_s,td,e,openWRF,getDimensions

# P_top must be the same as what is used in the WRF simulation
P_top = 10**4
P_bot = 10**5

T_base = 300.0
T_zero = 273.15
L = 2.501e6 # latent heat of vaporization
R = 287.04  # gas constant air
Rv = 461.5  # gas constant vapor
eps = R/Rv
cp = 1005.
cv = 718.
kappa = (cp-cv)/cp
g = 9.81

barb_increments = {'half': 2.5,'full':5.0,'flag':25.0}


skewness = 37.5
# Defines the ranges of the plot, do not confuse with P_bot and P_top
P_b = 105000.
P_t = 25000. 
dp = 100.
plevs = np.arange(P_b,P_t-1,-dp)


# See formula 3.16 in Rogers&Yau
a = 2./7.
b = eps*L*L/(R*cp)
c = a*L/R


def calc_flight_level(pres):
    result=(10**((np.log10(np.array(pres)/1013.25))/5.2558797) -1) / (-6.8755856 * 10**-6*100)
    return result

def gamma_s(T,p):
    """Calculates moist adiabatic lapse rate for T (Celsius) and p (Pa)
    Note: We calculate dT/dp, not dT/dz
    See formula 3.16 in Rogers&Yau for dT/dz, but this must be combined with
    the dry adiabatic lapse rate (gamma = g/cp) and the 
    inverse of the hydrostatic equation (dz/dp = -RT/pg)
    
    """
    esat = es(T)
    wsat = eps*esat/(p-esat) # Rogers&Yau 2.18
    numer = a*(T+T_zero) + c*wsat
    denom = p * (1 + b*wsat/((T+T_zero)**2)) 
    return numer/denom # Rogers&Yau 3.16

def es(T):
    """Returns saturation vapor pressure (Pascal) at temperature T (Celsius)
    Formula 2.17 in Rogers&Yau
    
    """
    return 611.2*np.exp(17.67*T/(T+243.5))

def e(w,p):
    """Returns vapor pressure (Pa) at mixing ratio w (kg/kg) and pressure p (Pa)
    Formula 2.18 in Rogers&Yau
    
    taken from: pywrfplotUtils.py
    https://code.google.com/p/pywrfplot/source/checkout
    """
    return w*p/(w+eps)

def td(e):
    """Returns dew point temperature (C) at vapor pressure e (Pa)
    Insert Td in 2.17 in Rogers&Yau and solve for Td
    
    taken from: pywrfplotUtils.py
    https://code.google.com/p/pywrfplot/source/checkout
    """
    return 243.5 * np.log(e/611.2)/(17.67-np.log(e/611.2))



class SkewT(object):
    """
         This is the method to use from the outside
         
    """  
               
    def __init__(self):
        self.zoom = False
    
    def set_data(self, pres, theta, dewp, u, v):    
        self.P = pres * 100
        self.theta = theta
        self.dewp = dewp
        self.u = u
        self.v = v
        
        
    def plot(self):
        plt.clf()
        fig = plt.figure()

        _isotherms()
        #
        _dry_adiabats()
        _moist_adiabats()        
        
        x1 = _temperature(self.theta, self.P)
        x2 = _dewpoint(self.dewp, self.P)
        
        #plt.axis([xlim0, xlim1, ylim1, ylim0])
        #plt.xlabel('Temperature ($^{\circ}\! C$) at 1000hPa')
        xticks = np.arange(-40,51,5)
        plt.xticks(xticks,['' if tick%10!=0 else str(tick) for tick in xticks])
        plt.ylabel('Pressure (mb)')
        yticks = np.arange(P_bot,P_t-1,-10**4)
        
        #format labels
        #plt.yticks(yticks, ['%4.0i' % (yt/100) for yt in yticks])   
        
        #sfcT = nc.variables['T2'][time,y,x]-T_zero
        #sfcT = 7.6307006835937727
        #sfcP = nc.variables['PSFC'][time,y,x]
        #sfcP = 100000.
        #sfcW = nc.variables['Q2'][time,y,x]
        #sfcW = 0.0063032461
        #sfcTd = td(e(sfcW,sfcP))
        #plt.suptitle('Bakketemp: %4.1f$^{\circ}\! C$  Duggpunkt: %3.1f$^{\circ}\! C$  Trykk: %5.1f hPa' % (sfcT,sfcTd,0.01*sfcP), \
        #             fontsize=10, x = 0.5, y = 0.03)        
    
        #plt.show()
        #plt.close()
        
        #zoom into area that is covered
        if self.zoom:
            xlim0=np.min(x2) // 5.0 * 5.0
            xlim1=((np.max(x1) // 5.0) + 2) * 5.0            
            ylim0=np.min(self.P) // 50 * 50
            ylim1=(np.max(self.P) // 50 + 1) * 50
            
            if np.abs(ylim1-ylim0) < 6000:
                yticks=np.arange(P_bot,P_t-1,(-10**4)/20.)
                _isobars(step_size=(-10**4)/20.)
                #format labels
                plt.yticks(yticks, ['%4.0i' % (yt/100) for yt in yticks])
                delta=500
            elif np.abs(ylim1-ylim0) < 9000:
                yticks=np.arange(P_bot,P_t-1,(-10**4)/10.)
                _isobars(step_size=(-10**4)/10.)
                #format labels
                plt.yticks(yticks, ['%4.0i' % (yt/100) for yt in yticks])
                delta=1000
            elif np.abs(ylim1-ylim0) < 20000:
                yticks=np.arange(P_bot,P_t-1,(-10**4)/5.)
                _isobars(step_size=(-10**4)/5.)                
                #format labels
                plt.yticks(yticks, ['%4.0i' % (yt/100) for yt in yticks])
                delta=2000
            else:
                yticks=np.arange(P_bot,P_t-1,(-10**4)/2.)
                _isobars(step_size=(-10**4)/2.)                
                #format labels
                plt.yticks(yticks, ['%4.0i' % (yt/100) for yt in yticks])
                delta=5000                    
            ax = plt.gca()
            ax.set_xlim((xlim0, xlim1))
            ax.set_ylim((ylim1, ylim0))
        else:
            _isobars(step_size=(-10**4)/4.)
            plt.axis([-40,50,P_b,P_t])        
            yticks = np.arange(P_bot,P_t-1,-10**4)
            #format labels
            plt.yticks(yticks, ['%4.0i' % (yt/100) for yt in yticks])
            delta=2500
                
        _windbarbs(self.u, self.v, self.P, delta)
        
        # add 2nd axis showing the flight level
        ylim_left=plt.gca().get_ylim()
        ax2=plt.twinx()        
        ax2.set_ylim((calc_flight_level(ylim_left[0]/100.), 
                      calc_flight_level(ylim_left[1]/100.)))
        ax2.yaxis.set_label_text('Flight Level')
        plt.setp(ax2.yaxis.get_label(), visible=True)
        plt.subplots_adjust(left=0.12, right=0.88, top=0.9, bottom=0.1)
        self.fig=plt.gcf()

    def get_figure(self):
        return self.fig


def _skewnessTerm(P):
    return skewness * np.log(P_bot/P)

def _isotherms():
    for temp in np.arange(-140,50,10):
        plt.semilogy(temp + _skewnessTerm(plevs), plevs,  basey=math.e, \
                     color = ('blue' if temp <= 0 else 'red'), \
                     linestyle=('solid' if temp == 0 else 'dashed'), linewidth = .5)

def _isobars(step_size=None):
    if not step_size:
        step_size = -10**4
    press_ticks = np.arange(P_bot,P_t-1,step_size)
    for n in press_ticks:
        plt.plot([-40,50], [n,n], color = 'black', linewidth = .5)
    
        
def _dry_adiabats():
    for tk in T_zero+np.arange(-30,210,10):
        dry_adiabat = tk * (plevs/P_bot)**kappa - T_zero + _skewnessTerm(plevs)
        plt.semilogy(dry_adiabat, plevs, basey=math.e, color = 'brown', \
                     linestyle='dashed', linewidth = .5)

def _moist_adiabats():
    ps = [p for p in plevs if p<=P_bot]
    for temp in np.concatenate((np.arange(-40.,10.1,5.),np.arange(12.5,45.1,2.5))):
        moist_adiabat = []
        for p in ps:
            temp -= dp*gamma_s(temp,p)
            moist_adiabat.append(temp + _skewnessTerm(p))
        plt.semilogy(moist_adiabat, ps, basey=math.e, color = 'green', \
                     linestyle = 'dotted', linewidth = .5)




def _windbarbs_org(nc,time,y,x,P):
    uwind = 0.5*(nc.variables['U'][time,:,y,x]+nc.variables['U'][time,:,y,x+1])
    vwind = 0.5*(nc.variables['V'][time,:,y,x]+nc.variables['V'][time,:,y+1,x])
    zmax = len(uwind)
    delta = 4
    baraxis = [45. for _j in range(0,zmax,delta)]
    plt.barbs(baraxis,P[0:zmax:delta],uwind[0:zmax:delta],vwind[0:zmax:delta], \
              barb_increments=barb_increments, linewidth = .75, norm=norm)

def _windbarbs(u, v, press, delta):
    #delta = 2500 # equals 25mb
    p_bin_min = int((np.min(press) // delta) * delta)
    p_bin_max = int(((np.max(press) // delta)+1) * delta)
    p_bins = np.array(range(p_bin_min, p_bin_max, delta))
    
    ixs = np.digitize(press, p_bins)
    uwind = [np.mean(u[ixs == ix]) for ix in list(set(ixs))]
    vwind = [np.mean(v[ixs == ix]) for ix in list(set(ixs))]
    
    ax = plt.gca()
    inv = ax.transLimits.inverted()
    #x_pos, _none = inv.transform((0.92, 0))
    x_pos = inv.transform(np.array([[0.92,0]]))[0, 0]
    baraxis = [x_pos] * len(p_bins) 
    plt.barbs(baraxis, p_bins, uwind, vwind, \
              barb_increments=barb_increments, linewidth = .75)#, transform=ax.transAxes)


def _temperature_org(nc,time,y,x,P):
    theta = nc.variables['T'][time,:,y,x] + T_base 
    T = theta*(P/P_bot)**kappa - T_zero # Temperatur i halvflatene (C)
    plt.semilogy(T + _skewnessTerm(P), P, basey=math.e, color = 'black', \
                 linestyle='solid', linewidth = 1.5)

def _temperature(theta, P):
    T = theta*(P/P_bot)**kappa - T_zero # Temperatur i halvflatene (C)
    plt.semilogy(T + _skewnessTerm(P), P, basey=math.e, color = 'black', \
                 linestyle='solid', linewidth = 1.5)
    return T + _skewnessTerm(P)


def _dewpoint_org(nc,time,y,x,P):
    w = nc.variables['QVAPOR'][time,:,y,x]
    plt.semilogy(td(e(w,P)) + _skewnessTerm(P), P, basey=math.e, color = 'red', \
                 linestyle='solid', linewidth = 1.5)


def _dewpoint(dp, P):
    #w = nc.variables['QVAPOR'][time,:,y,x]
    plt.semilogy(dp + _skewnessTerm(P), P, basey=math.e, color = 'red', \
                 linestyle='solid', linewidth = 1.5)
    return dp + _skewnessTerm(P)


