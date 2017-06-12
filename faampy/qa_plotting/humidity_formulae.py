import numpy as np
            
def vp2vmr(vp,p):    
    vmr=vp/(p-vp)
    return vmr
    
def vp2uw(vp,p):
    uw=vp/p
    return uw

def vmr2vp(vmr,p):
    vp=p*(vmr/(1.0+vmr))
    return vp
    
def uw2vp(uw,p):
    vp=p*uw
    return vp

def mmr_vmr(mmr):
    VMR  =  mmr/622.0 
    return VMR


def vmr_mmr(vmr):
    MMR  =  622.0 * vmr 
    return MMR

def calc_L_K(P,T):
    T0=273.15
    P0=1013.2
    Uo=0.2095
    L=((0.304+0.351*(P/P0))*Uo*P*T0)/(P0*T)
    K=(427.0*P*T0)/(P0*T)
    return (L,K)

def ps_water(T):
    lnps=-6096.9385/T+21.2409642-2.711193e-2*T+1.673952e-5*T*T+2.433502*np.log(T)
    return np.exp(lnps)

def ps_ice(T):
    lnps=-6024.5282/T+29.32707+1.0613868e-2*T-1.3198825e-5*T*T-0.49382577*np.log(T)
    return np.exp(lnps)



def fp2vp(fp,p=[],temp=[],enhance=False):
    """
    Convert a frost point to a volume mixing ratio ( and vapour pressure )
    Using ITS-90 correction of Wexler's formula
    Optional enhancement factors for non ideal 
    """
    fp=np.atleast_1d(fp)
    k=np.array([-5.8666426e3,2.232870244e1,1.39387003e-2,-3.4262402e-5,2.7040955e-8,6.7063522e-1],dtype='f8')
    lnes=np.zeros(fp.shape,dtype='f8')
    for i in range(5):
        lnes=lnes+k[i]*(fp**(i-1.0))
    lnes+=k[5]*np.log(fp)
    vp=np.exp(lnes)/100.0
    if(enhance and len(p)>0):
        A=np.array([-6.0190570e-2,7.3984060e-4,-3.0897838e-6,4.3669918e-9],dtype='f8')
        B=np.array([-9.4868712e1,7.2392075e-1,-2.1963437e-3,2.4668279e-6],dtype='f8')
        if(len(temp)==0):
            temp=fp
        alpha=np.zeros(fp.shape,dtype='f8')
        beta=np.zeros(fp.shape,dtype='f8')
        for i in range(4):
            alpha=alpha+(A[i]*(temp**i))
            beta=beta+(B[i]*(temp**i))
        beta=np.exp(beta)
        ef=np.exp(alpha*(1-vp/p)+beta*(p/vp-1))
        vp=vp*ef
    return vp

def dp2vp(dp,p=[],temp=[],enhance=False):
    """
    Convert a dew point to a volume mixing ratio ( and vapour pressure )
    Using ITS-90 correction of Wexler's formula
    Optional enhancement factors for non ideal 
    """
    dp=np.atleast_1d(dp)
    g=np.array([-2.8365744e3,-6.028076559e3,1.954263612e1,-2.737830188e-2, 
       1.6261698e-5,7.0229056e-10,-1.8680009e-13,2.7150305],dtype='f8')
    lnes=np.log(dp)*g[7]
    for i in range(7):lnes=lnes+g[i]*(dp**(i-2.0))
    vp=np.exp(lnes)/1e2
    if(enhance and len(p)>0) :
        A=np.array([-1.6302041e-1,1.8071570e-3,-6.7703064e-6,8.5813609e-9],dtype='f8')
        B=np.array([-5.9890467e1,3.4378043e-1,-7.7326396e-4,6.3405286e-7],dtype='f8')
        if(len(temp)==0) : temp=fp
        alpha=np.zeros(fp.shape)
        beta=np.zeros(fp.shape)
        for i in range(4) :
            alpha=alpha+(A[i]*(temp**i))
            beta=beta+(B[i]*(temp**i))
        beta=np.exp(beta)
        ef=np.exp(alpha*(1-vp/p)+beta*(p/vp-1))
        vp=vp*ef
    return vp


def vp2fp(vp,p=[],temp=[],enhance=False):
    """
    Convert a volume mixing ratio to a frost point ( and vapour pressure )
    Using ITS-90 correction of Wexler's formula
    Optional enhancement factors for non ideal 
    """  
    vp=np.atleast_1d(vp)
    c=np.array([2.1257969e2,-1.0264612e1,1.4354796e-1,0],dtype='f8')
    d=np.array([1,-8.2871619e-2,2.3540411e-3,-2.4363951e-5],dtype='f8')
    c1=np.zeros(vp.shape,dtype='f8')
    d1=np.zeros(vp.shape,dtype='f8')
    if(enhance and len(p)>0):
        if(len(temp)==0):
            lnes=alog(vp*1e2)
            for i in range(4):
                c1=c1+c[i]*lnes**i
                d1=d1+d[i]*lnes**i
            fp=c1/d1
            temp=fp
        A=np.array([-6.0190570e-2,7.3984060e-4,-3.0897838e-6,4.3669918e-9],dtype='f8')
        B=np.array([-9.4868712e1,7.2392075e-1,-2.1963437e-3,2.4668279e-6],dtype='f8')
        alpha=np.zeros(vp.shape)
        beta=np.zeros(vp.shape)
        for i in range(4):
            alpha=alpha+(A[i]*(temp**i))
            beta=beta+(B[i]*(temp**i))
        beta=np.exp(beta)
        ef=np.exp(alpha*(1-vp/p)+beta*(p/vp-1))
        vp=vp/ef
    c1[:]=0
    d1[:]=0
    lnes=np.log(vp*100.0)
    for i in range(4):
        c1=c1+c[i]*lnes**i
        d1=d1+d[i]*lnes**i
    fp=c1/d1
    return fp
 
def vp2dp(vp,p=[],temp=[],enhance=False):
    """
    Convert a volume mixing ratio to a dew point ( and vapour pressure )
    Using ITS-90 correction of Wexler's formula
    Optional enhancement factors for non ideal 
    """  
    vp=np.atleast_1d(vp)
    c=np.array([-9.2288067e-06, 0.46778925, -20.156028, 207.98233],dtype='f8')
    d=np.array([-7.5172865e-05, 0.0056577518, -0.13319669, 1],dtype='f8')
    lnes=np.log(vp*1e2)
    dp=np.polyval(c,lnes)/np.polyval(d,lnes)
    if(enhance and len(p)>0) :
        if(len(temp)==0):
            temp=dp
        A=np.array([8.5813609e-09, -6.7703064e-06, 0.001807157, -0.16302041],dtype='f8')
        B=np.array([6.3405286e-07, -0.00077326396, 0.34378043, -59.890467],dtype='f8')
        alpha=np.polyval(A,temp)
        beta=np.exp(np.polyval(B,temp))
        ef=np.exp(alpha*(1-vp/p)+beta*(p/vp-1))
        vp=vp/ef
        lnes=np.log(vp*1e2)
        dp=np.polyval(c,lnes)/np.polyval(d,lnes)
    return dp




