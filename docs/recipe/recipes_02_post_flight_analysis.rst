

Recipe - Post Flight Analysis
=============================

A standard example what the post flight analysis could look like using faampy.
  
Flight Data
-----------

The data we are using here are from the "Into the Blue" flight b991 on the 24th October 2016. This flight took us up and down the west coast between Morecambe and Wales.

Warning: All the Chemistry data are preliminary uncalibrated and not suitable for scientific analysis. The purpose here is to show an example for a post flight
work flow.


FAAM Dataset
------------

import pandas as pd
from faampy.core.faam_data import FAAM_Dataset

nox_dateparse = lambda x: pd.datetime(year, month, day)+datetime.timedelta(seconds=int(float(float(x) % 1) * 86400.))
fgga_dateparse = lambda x: pd.datetime.utcfromtimestamp(int(x))

df_nox = pd.read_csv(nox_file, parse_dates=[0], date_parser=nox_dateparse)
df_nox = df_nox.set_index('TheTime')
df_nox = df_nox[['no_conc', 'no2_conc', 'nox_conc']]
df_nox[df_nox < 0] = np.nan

fgga_names=['identifier', 'packet_length', 'timestamp', 'ptp_sync', 'MFM', 'flight_num','CPU_Load','USB_disk_space','ch4','co2','h2o','press_torr','temp_c','fit_flag','rda_usec','rdb_usec', 'ch4_ppb','co2_ppm','MFC_1_absolute_pressure','MFC_1_temperature','MFC_1volumetic_flow','MFC_1mass_flow','MFC_1set_point','V1','V2','V3','V4','restart_FGGA','FGGA_Pump','CAL_MFC_1Set_Value']
df_fgga=pd.read_csv(fgga_file, names=fgga_names, delimiter=',', parse_dates=[2], date_parser=fgga_dateparse, skiprows=100)

df_fgga['ch4_ppb'][df_fgga['V1'] != 0] = np.nan
df_fgga['co2_ppm'][df_fgga['V2'] != 0] = np.nan
df_fgga['ch4_ppb'][df_fgga['V2'] != 0] = np.nan


ds = FAAM_Dataset(nc_file)

t = df_nox.index.values
t.astype('datetime64[s]')
df_nox.index=t
df_nox.index.names = ['timestamp']
ds.merge(df_nox.to_records(convert_datetime64=False), index='timestamp')
ds.merge(df_fgga.to_records(convert_datetime64=False), index='timestamp')

var_list=['Time', 'LAT_GIN', 'LON_GIN', 'ALT_GIN', 'HGT_RADR', 'CO_AERO', 'O3_TECO', 'U_C', 'V_C', 'W_C', 'U_NOTURB', 'V_NOTURB', 'WOW_IND', 'TAT_DI_R', 'TDEW_GE', 'PS_RVSM', 'ch4_ppb', 'co2_ppm', 'no_conc', 'no2_conc', 'nox_conc', 'TSC_BLUU', 'TSC_GRNU' , 'TSC_REDU', 'BSC_BLUU', 'BSC_GRNU', 'BSC_REDU', 'IAS_RVSM']
ds.write(os.path.join(data_root_path, 'data', '%s_merged.nc' % (FID.lower())), v_name_list=var_list)


var_list=['Time', 'LAT_GIN', 'LON_GIN', 'ALT_GIN', 'HGT_RADR', 'CO_AERO', 'O3_TECO', 'U_C', 'V_C', 'W_C', 'U_NOTURB', 'V_NOTURB', 'WOW_IND', 'TAT_DI_R', 'TDEW_GE', 'PS_RVSM', 'ch4_ppb', 'co2_ppm', 'no_conc', 'no2_conc', 'nox_conc', 'TSC_BLUU', 'TSC_GRNU' , 'TSC_REDU', 'BSC_BLUU', 'BSC_GRNU', 'BSC_REDU', 'IAS_RVSM']
ds.write('~/faampy_data/b991/b991_merged.nc', v_name_list=var_list)





merging data



get it back as pandas dataframe
writing out as a new netcdf


Google-Earth overlays
---------------------


faampy nc_to_gpx ~/faampy_data/b991/core/core_faam_20161024_v004_r0_b991.nc

gpscorrelate --gps ~/faampy_data/b991/core/b991_20161024.gpx --photooffset -3600 ~/faampy_data/b991/photos/*jpg

faampy ge_photo_album ~/faampy_data/b991/photos/*jpg ~/faampy_data/b991/ge_photo_album_20161024_b991.kmz


Quicklook Figures
-----------------

Create quicklook.cfg file, that defines the figure layouts.

cd ~/faampy/b991
mkdir quicklooks
touch quicklooks.cfg

[['TSC_BLUU', 'TSC_GRNU' , 'TSC_REDU'], ['BSC_BLUU', 'BSC_GRNU', 'BSC_REDU']]
[['O3_TECO'], ['CO_AERO']]
[['ch4_ppb'], ['co2_ppm']]
[['no_conc'], ['no2_conc'], ['nox_conc']]

faampy quicklooks --config_file ~/faampy_data/b991/quicklook.cfg ~/faampy_data/b991/core/core_faam_20161024_v004_r0_b991.nc ~/faampy_data/b991/core/flight-sum_faam_20161024_r0_b991.txt ~/faampy_data/b991/quicklooks/

