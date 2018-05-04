"""

Quality Assurance-Quality Check (QA-QC) plotting for the total water isntrument

Layout (portrait):

           -------------   -------------
           |   Scatter  |  | Scatter   |
           |   plot of  |  | of wvss2r |
           |   GE/TWC   |  |  vs TWC   |
           -------------   -------------
  ---------------------------------------------
  |            In or out of cloud             |
  ---------------------------------------------
  ---------------------------------------------
  |           Instrument Status               |
  ---------------------------------------------
  ---------------------------------------------
  |                                           |
  |   Timeseries of temps from twc probe;     |
  |     nose, sample, source, ambient         |
  |                                           |
  ---------------------------------------------
  ---------------------------------------------
  |                                           |
  |         Timeseries of dew point           |
  |                temperatures               |
  |                                           |
  ---------------------------------------------



"""


import numpy as np
import matplotlib as mpl
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from general import QaQc_Figure, \
                    set_suptitle, get_data, add_takeoff, add_landing, \
                    zoom_to_flight_duration, add_time_buffer
from style import rcParams, axes_title_style


def vp2dp_buck(vp, p, temp):
    """Water vapour to dew point conversion using the formula from the
    Buck CR2 hygrometer manual p19f. Returns the dew point in K.

    Input:
      vp: vapour pressure in mb
      p: air pressure in mbar
      temp: air temperature in Kelvin

    Output:
      dew point temperature in K

    """
    a, b, c, d = (6.1121, 18.678, 257.14, 234.5)
    ef = 1.0+10**-4*(2.2+p/10.*(0.0383+6.4*10**-5*(temp-273.15)*2))
    s = np.log(vp/ef)-np.log(a)
    result = d/2.0 * (b-s-((b-s)**2-4*c*s/d)**0.5)
    return result+273.15



def wvss2_vmr2dp(vmr, p, temp):
    """Dewpoint from WVSS2B (deg C)

    """
    #p=self.getdata('wvss2b01_press',data)
    #vmr=self.getdata('wvss2b01_vmr',data)
    #temp=self.getdata('deiced_true_air_temp_k',data)

    wmr=vmr/1.6077
    vp=wmr*p/(622*10**3+wmr)
    dp=vp2dp_buck(vp, p, temp)
    return dp


#parameter names used in this script to plot temperature graphs
VARIABLE_NAMES = ['Time',                     # Time of measurement (seconds since midnight on start date)
                  'WOW_IND',                  # Weight on wheels indicator
                  'TWCDAT_status',            # 1
                  'TAMB_CAL',                 # twc_amb_temp - twc ambient temp
                  'TWCDAT_twc_detector',      # twc_detector - twc detector counts
                  'TWCDAT_twc_evap1',         # twc_evap1 - evap 1 current
                  'TWCDAT_twc_evap2',         # twc_evap2 - evap 2 current
                  'TWCDAT_twc_evap2_on',      # twc_evap2_on - evap 2 on signal
                  'TNOS_CAL',                 # twc_nose_temp - nose temp
                  'TWC_TSAM',                 # twc_samp_temp - sample temp
                  'ISRC_CAL',                 # twc_srce_i - source current
                  'TSRC_CAL',                 # twc_srce_temp - twc source temp
                  'TWC_DET',                  # Raw data from the TWC probe Lyman alpha detector
                  'TWC_EVAP',                 # Total water specific humidity from the TWC avaporator instrument
                  'TWC_TDEW',                 # Dew-point derived from TWC probe specific humidity (valid in cloud-free air)
                  'NV_TWC_P',
                  'TDEW_GE',                  # Dew point from the General Eastern instrument
                  'WVSS2R_VMR',               # Water Vapour Measurement from Rosemount inlet WVSSII serial no. 0388 linearly interpolated to 1Hz
                  'PS_RVSM',                  # Static pressure from the aircraft RVSM (air data) system
                  'TAT_ND_R']                 # True air temperature from the Rosemount non-deiced temperature sensor


def plot_twc_temperatures(ax, data):
    """
    Creates timeseries plot of the several temperatures measured by TWC probe (Nose, sample, source, ambient)

    """
    ix=np.where(data['WOW_IND'] != 0)[0]

    tnos_cal=data['TNOS_CAL'][:]
    tnos_cal[ix,:]=np.nan
    tsrc_cal=data['TSRC_CAL'][:]
    tsrc_cal[ix,:]=np.nan
    tamb_cal=data['TAMB_CAL'][:]
    tamb_cal[ix,:]=np.nan
    line_1 = ax.plot_date(data['mpl_timestamp'][:,0].ravel(),
                          tnos_cal[:,0], '-', label= 'nose')
    line_2 = ax.plot_date(data['mpl_timestamp'][:,0].ravel(),
                          tamb_cal[:,0], '-', label= 'ambient')
    ax.set_ylabel('Temperatures (K)')
    line_3 = ax.plot_date(data['mpl_timestamp'][:,0].ravel(),
                          tsrc_cal[:,0], '-', label= 'source')
    ax.text(0.05, 0.98, 'Temperatures from the TWC probe',
            axes_title_style, transform=ax.transAxes)

    plt.setp(ax.get_xticklabels(), visible=False)

    lines = line_1 + line_2 + line_3
    labs = [l.get_label() for l in lines]
    ax.legend(lines, labs, loc='lower left')
    ax.get_xticklabels()[-1].set_visible(False)
    return ax


def plot_dp_timeseries(ax, data):
    """
    Creates plot for dew point timeseries for TWC and WVSS2R_VMR

    """
    if not 'TWC_TDEW' in list(data.keys()):
        return

    ix=np.where(data['WOW_IND'] == 1)[0]
    twc_tdew=data['TWC_TDEW'][:]
    twc_tdew[ix,:]=np.nan

    line1= ax.plot_date(data['mpl_timestamp'][:,0].ravel(), twc_tdew[:,0], '-', label= 'TWC')

    #convert from volume mixing ratio to dew point, for the WVSS2R_VMR
    vmr_wvss2= data['WVSS2R_VMR'][:,0].ravel()
    p = data['PS_RVSM'][:,0].ravel()
    temp = data['TAT_ND_R'][:,0].ravel()
    dp_wvss2r = wvss2_vmr2dp(vmr_wvss2, p, temp)
    dp_wvss2r[ix] = np.nan

    line2 = ax.plot_date(data['mpl_timestamp'][:,0].ravel(), dp_wvss2r, '-', label= 'WVSS2R')

    ix=np.where(data['WOW_IND'] == 1)[0]
    tdew_ge=data['TDEW_GE'][:]
    tdew_ge[ix,:]=np.nan

    line3 = ax.plot_date(data['mpl_timestamp'].ravel()[::8], tdew_ge[:].ravel(), '-', label= 'GE')

    lines = line1+line2+line3
    labs = [l.get_label() for l in lines]
    ax.legend(lines,labs, loc='lower left')
    ax.text(0.05, 0.98,'Dewpoint temperatures', axes_title_style, transform=ax.transAxes)

    hourloc=mpl.dates.HourLocator()
    xtickformat=mpl.dates.DateFormatter('%H:%M')
    ax.xaxis.set_major_locator(hourloc)
    ax.xaxis.set_major_formatter(xtickformat)
    labels=ax.get_yticklabels()
    labels[-1].set_visible(False)
    ax.set_xlabel('Time (utc)')
    ax.set_ylabel('Temperature (K)')
    return ax


def plot_twc_vs_ge(ax, data):
    """
    Creates scatter plot for the GE and TWC instruments

    """
    if not 'TWC_TDEW' in list(data.keys()):
        return
    ix=list(np.where(data['WOW_IND'] == 0)[0])
    ax.plot(data['TDEW_GE'][ix,0].ravel(),
            data['TWC_TDEW'][ix,0].ravel(), '.', label='TDEW_GE')

    ax.set_xlabel('GE dp (K)')
    ax.set_ylabel('TWC dp (K)')

    ax.text(0.05,0.9,'GE vs. TWC', axes_title_style, transform=ax.transAxes)
    axis_range=(min([ax.get_xlim()[0], ax.get_ylim()[0]]), max([ax.get_xlim()[1], ax.get_ylim()[1]]))
    ax.set_xlim(axis_range)
    ax.set_ylim(axis_range)
    ax.plot(ax.get_xlim(),ax.get_ylim(), linestyle='--', color=rcParams['grid.color'])
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    for label in ax.get_xticklabels()[::2]:
        label.set_visible(False)
    for label in ax.get_yticklabels()[::2]:
        label.set_visible(False)
    return ax


def plot_twc_vs_wvss2f(ax, data):
    """
    Creates scatter plot for WVSS2F and TWC

    """

    if not 'TWC_TDEW' in list(data.keys()):
        return

    ix=list(np.where(data['WOW_IND'] == 0)[0])
    vmr_wvss2= data['WVSS2R_VMR'][:,0].ravel()
    p=data['PS_RVSM'][:,0].ravel()
    temp=data['TAT_ND_R'][:,0].ravel()
    dp_wvss2r=wvss2_vmr2dp(vmr_wvss2, p, temp)

    ax.plot(dp_wvss2r[ix], data['TWC_TDEW'][ix,0].ravel(),'.', label='WVSS2R_VMR')

    ax.set_xlabel('WVSS2R dp (K)')
    ax.set_ylabel('TWC dp (K)')

    ax.text(0.05,0.9,'WVSS2R_VMR vs. TWC', axes_title_style, transform=ax.transAxes)
    axis_range=(min([ax.get_xlim()[0], ax.get_ylim()[0]]), max([ax.get_xlim()[1], ax.get_ylim()[1]]))
    ax.set_xlim(axis_range)
    ax.set_ylim(axis_range)
    ax.plot(ax.get_xlim(), ax.get_ylim(),
            linestyle='--', color=rcParams['grid.color'])
    #http://stackoverflow.com/questions/12608788/changing-the-tick-frequency-on-x-or-y-axis-in-matplotlib
    for label in ax.get_xticklabels()[::2]:
        label.set_visible(False)
    for label in ax.get_yticklabels()[::2]:
        label.set_visible(False)
    return ax


def plot_cloud(ax, data):
    """
    plots liquid water content timeseries i.e. cloud status

    """
    plt.setp(ax.get_xticklabels(), visible=False)
    plt.setp(ax.get_yticklabels(), visible=False)
    #ax.text(0.05, 0.98, 'TODO: Will show cloud IN/OUT',
    #        axes_title_style, transform=ax.transAxes)
    rng = np.max(data['NV_TWC_P'], axis=1) - np.min(data['NV_TWC_P'], axis=1)
    rng_class = np.zeros(rng.shape)
    rng_class[rng > 0.2] = 1
    toggle = np.diff(rng_class)
    time_periods = zip(list(np.where(toggle == 1)[0]),
                       list(np.where(toggle == -1)[0]))
    for t in time_periods:
        #plt.barh(0, data['mpl_timestamp'][0,1], left=data['mpl_timestamp'][0,0])
        width = data['mpl_timestamp'][t[1], 0]-data['mpl_timestamp'][t[0], 0]
        ax.add_patch(patches.Rectangle((data['mpl_timestamp'][t[0],0], 0),
                                       width, 1, color='#ffaf4d'))
    ax.set_ylabel('cloud')
    ax.grid(False)
    return ax


def plot_twc_status(ax, data):
    """
    plots total water instrument status

    Bit 1: Detector Data Value, false' indicates detector failure or source failure
    Bit 2: Nose Temperature, almost certainly would indicate a heater failure on the nose cone, or a failure in its associated thermostat electronics
    Bit 3: Sample Temperature, out of range indicates a heater problem. As they age they become higher resistance and eventually cannot keep the sample temperature high enough
    Bit 4: not used, set to 1
    Bit 5: Source Temperature, check against 'source ready' light
    Bit 6: not used, set to 1
    Bit 7: not used, set to 1
    Bit 8: Source Current, easy to check by switching source on/off when source is ready
    """
    # convert integer to binary represntation
    def get_bin(x):
        return format(x, 'b').zfill(8)

    plt.setp(ax.get_xticklabels(), visible=False)
    plt.setp(ax.get_yticklabels(), visible=False)

    status_list = [list(get_bin(b)) for b in data['TWCDAT_status'][:].ravel()]
    s1, s2, s3, s4, s5, s6, s7, s8 = zip(*status_list)
    for i, s in enumerate([s1, s2, s3, s4, s5, s6, s7, s8]):
        toggle = np.diff(np.array(s, dtype=int))
        time_periods = zip(list(np.where(toggle == 1)[0]),
                           list(np.where(toggle == -1)[0]))
        for t in time_periods:
            width = data['mpl_timestamp'][t[1], 0] - \
                    data['mpl_timestamp'][t[0], 0]
            height = 0.125*8
            y = 0.125*i*8
            ax.add_patch(patches.Rectangle((data['mpl_timestamp'][t[0], 0], y),
                                           width, height, color='0.6'))
    ax.grid(True)
    ax.set_yticks(np.arange(0, 8), minor=False)
    ax.set_ylim(0, 8)
    ax.set_ylabel('Status')
    return ax


def main(ds):
    """
    Creates an overview plot for the Lyman-Alpha total water content probe (TWC).
    It calls all plotting functions and sets up axes layout.

    """
    #Setup up axes layout
    gs = gridspec.GridSpec(2, 1, height_ratios=[1, 4])
    top_cell = gs[0, 0]
    bottom_cell = gs[1, 0]
    # sets up bottom 4 axes; dp timeseries,
    # twc timeseries, twc status and cloud status
    gs1 = gridspec.GridSpecFromSubplotSpec(4, 1, bottom_cell,
                                           height_ratios=[2, 2, 6, 10],
                                           hspace=0.05)

    fig = QaQc_Figure().setup()
    ax_dp_ts = fig.add_subplot(gs1[3])
    ax_twc_temperatures_ts = fig.add_subplot(gs1[2], sharex=fig.get_axes()[0])
    ax_twc_status = fig.add_subplot(gs1[1], sharex=fig.get_axes()[0])
    ax_cloud_ts = fig.add_subplot(gs1[0], sharex=fig.get_axes()[0])

    # sets up top 2 axes; ge scatter and wvss2r scatter
    gs2 = gridspec.GridSpecFromSubplotSpec(1, 2, top_cell)
    ax_scatter_ge = fig.add_subplot(gs2[0], aspect='equal')
    ax_scatter_wvss2r = fig.add_subplot(gs2[1], aspect='equal')

    set_suptitle(fig, ds, 'QA-Total Water Content Probe')

    data = get_data(ds, VARIABLE_NAMES)
    for k in list(data.keys()):
        if 'int' not in str(data[k].dtype):
            data[k][data[k] == -9999.] = np.nan

    # Call the plotting methods below:
    plot_dp_timeseries(ax_dp_ts, data)
    plot_twc_temperatures(ax_twc_temperatures_ts, data)
    plot_twc_status(ax_twc_status, data)

    plot_cloud(ax_cloud_ts, data)
    plot_twc_vs_ge(ax_scatter_ge, data)
    plot_twc_vs_wvss2f(ax_scatter_wvss2r, data)

    # adds grey bar showing takeoff/landing and only plots the flight
    ax = fig.get_axes()[0]
    zoom_to_flight_duration(ax, data)
    add_time_buffer(ax)

    for ax in fig.get_axes()[0:4]:
        add_takeoff(ax, data)
        add_landing(ax, data)
    return fig
