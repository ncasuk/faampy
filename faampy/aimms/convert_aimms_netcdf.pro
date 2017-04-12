PRO convert_aimms_netcdf, basedir, corefile, ofile, fnum, $
                          time,atime,btime,ctime,dtime, $
                          average1hz=make_average, $
                          release_data=datarelease
;
; PROCEDURE:   CONVERT_AIMMS_NETCDF
; 
; PURPOSE:     To read post-processed data from an AIMMS ascii file and output to NetCDF format.
;              Assumes that the ascii file has 20 data values per second. Time array is recreated
;              to overcome apparent AIMMS clock-rate error.
; 
; ARGUMENTS:   BASEDIR - directory in which AIMMS ascii file is located and NetCDF written, assumed
;              to point to a project directory such as '/project/obr/COPE'
;              FNUM - the flight number, bnnn
;              AVERAGE1HZ = MAKE_AVERAGE - If set and non-zero, output dataset is 1Hz average
;              RELEASE_DATA = DATARELEASE - If set, specifies an alternative data release number (default = 0)
;
; DATE:        12/11/2013
; AUTHOR:      Steve Abel, with modifications by Phil Brown
;
; VERSION:     v001 - 06/12/2013 Initial version set up to idenify and process all AIMMS 20Hz ascii files found
;                     in the target directory. Options to match output time array to Core data file and to 
;                     generate 1Hz average output. Contains a fix to identify and correct time jumps in the input
;                     ascii data. Ascii file post-processing using "ekf553_oemv.exe".
;              v002 - 05/02/2014 Update to NetCDF attributes:
;                   - additional GLOBAL attributes specified for similarity with FAAM Core files,
;                   - additional CF-1.6 compliant standard_name attributes supplied for variables, where possible
;                   - applies adjustment to AIMMS date/time where Core data starts before midnight on the previous day
;              v003 - 18/02/2014 Further updates to NetCDF attributes:
;                   - units for dimensionless variables = 1
;                   - standard names of latitude and longitude parameters
;                   - time units
;                   - status variable excluded
;                   - correct long_name now given for AOSS and AOA 
;                   - 28/02/2014 FILE_SEARCH replaces FINDFILE (line 50)
;                   - 07/03/2014 minor correction to standard_name attribute for latitude
;                   - 21/05/2014 minor change to dealing with skip/jump times - jumps preceding the first skip are ignored
;                   - 23/05/2014 fudge skip times for B800 and b807
;                   - 04/12/2014 Test for existence of Core and Core1hz files before trying to open them. Allows processing
;                                when only the Core1hz is available
;                   - 03/08/2015 Changes to allow runng in garden-variety IDL (using IDL standard functions rather
;                                than Met Office specific ones.                         
;
on_error, 0

; COMMON to hold NetCDF file and variable id's
common varids, id, LTIME, LCAL, cp0_id,cpa_id,cpb_id,B0_id,Ba_id,Bb_id,A0_id,Aa_id,Ab_id, $
  time_id,tk_id,rh_id,p_id,u_id,v_id,w_id,lat_id,lon_id,alt_id,vn_id,ve_id,vz_id, $
  roll_id,ptch_id,hdg_id,tas_id,aoss_id,dpaoa_id,dpaoss_id,aoa_id

version = 'v003'
if not(keyword_set(datarelease)) then datarelease=0
rstring = 'r'+STRTRIM(STRING(datarelease),1)

;fdir = STRUPCASE(fnum)+'/'                           ; find ascii input files under base directory
;daq_file = basedir+'/AIMMS/'+fdir+'*'+fnum+'*.out'
daq_file = basedir+fnum+'*.out'
daq_files = file_search(daq_file)
;daq_file = aimmsfile
nfiles = n_elements(daq_files)
;if daq_files(0) eq '' then begin
;  print,'Input data not found: ', daq_file
; return
;ndif
;print,nfiles,' data files for reading.',daq_files

; identify Core file and read time data from it. Time data is the same in Core and Core1hz files. If you don't find the Core file
; then look for the Core1hz. If you still don't find that, then exit.
;
;corefile = findcorefile(basedir,fnum,core1hz)
;print, '***', corefile
;if strlen(corefile) gt 0 then begin
cid = NCDF_OPEN(corefile,/NOWRITE)
;endif else begin
;  if strlen(core1hz) gt 0 then begin
;    cid = NCDF_OPEN(core1hz)
;  endif else begin
;    print,'No core files could be found. Exiting.....'
;    return
;  endelse
;endelse

NCDF_VARGET,cid,'Time',core_time                  ; Core data time in seconds after midnight
NCDF_ATTGET,cid,'Time','units',coretimeunits      ; units of Core data time (specifies which day)
print,string(coretimeunits)
print,'Range of core time = ',gmt(core_time(0)),gmt(core_time(n_elements(core_time)-1))
;
cyear = fix(string(coretimeunits(14:17)))               ; year, month, day of Core data  
cmonth= fix(string(coretimeunits(19:20)))
cday  = fix(string(coretimeunits(22:23)))

start_time = core_time(0)
if not(keyword_set(make_average)) then begin     ; create 20Hz time array to span range of Core time
  core_time = findgen(n_elements(core_time)*20)*0.05 + start_time
endif

; **********************************************************************************************************
; start of loop over the number of ascii input file
; **********************************************************************************************************

FOR jfile=0,nfiles-1 DO BEGIN
print,'Reading file ',jfile

; first read aerodynamic calibration coefficients from top of ascii file
cal_coeff = READ_ASCII(daq_file,DATA_START=1,NUM_RECORDS=1)
Cp_0 = cal_coeff.field01(0)
Cp_alpha = cal_coeff.field01(1)
Cp_beta = cal_coeff.field01(2)
B_0 = cal_coeff.field01(5)
B_alpha = cal_coeff.field01(6)
B_beta = cal_coeff.field01(7)
A_0 = cal_coeff.field01(8)
A_alpha = cal_coeff.field01(9)
A_beta = cal_coeff.field01(10)

; now read data from the ascii file

DATA = READ_ASCII(DAQ_FILES(JFILE),COUNT=NT,DATA_START=2,HEADER=HEADER)
Time = REFORM(data.FIELD01(0,*))
Tc   = REFORM(data.FIELD01(1,*))
RH   = REFORM(data.FIELD01(2,*))
Pres = REFORM(data.FIELD01(3,*))
V    = REFORM(data.FIELD01(4,*))
U    = REFORM(data.FIELD01(5,*))
Lat  = REFORM(data.FIELD01(6,*))
Lon  = REFORM(data.FIELD01(7,*))
alt  = REFORM(data.FIELD01(8,*))
Vn   = REFORM(data.FIELD01(9,*))
Ve   = REFORM(data.FIELD01(10,*))
Vz   = REFORM(data.FIELD01(11,*))
Roll = REFORM(data.FIELD01(12,*))
Pitch= REFORM(data.FIELD01(13,*))
Hdg  = REFORM(data.FIELD01(14,*))
Tas  = REFORM(data.FIELD01(15,*))
W    = REFORM(data.FIELD01(16,*))
Aoss = REFORM(data.FIELD01(17,*))
Dpaoa= REFORM(data.FIELD01(18,*))
Dpaoss= REFORM(data.FIELD01(19,*))
; Status= REFORM(data.FIELD01(20,*))

Time = Time*3600.   ; seconds after midnight
print,'Raw time converted to seconds.'

; **********************************************************************************************************
; First, detect any time data where the clock has wrapped around midnight. In this case, times will be less than
; the initial time in the data so add 24 hours to them.
initial_time = Time(0)
next_day = where(Time lt initial_time)
if next_day(0) ne -1 then begin 
  Time(next_day) = Time(next_day) + 86400.
  print,'Time adjustment made where AIMMS clock has crossed midnight.'
endif

; **********************************************************************************************************
; now search for periods when time skips due to purge event. These events take the form of about 1 second's worth
; of data points that skip back in time by about 0.5 sec. At the end of this event, the time jumps ahead by about
; the same amount to resume the expected sequence.

stime = time
index = lindgen(n_elements(time))

if (fnum eq 'b807') then begin                              ; fudge time skips for b807 only
  time(231691:231700) = time(231691:231700) + 0.45
  time(231701:231710) = time(231701:231710) + 0.90
  time(231711:231719) = time(231711:231719) + 1.35
endif

skip = where(time(index)-time(index-1) lt 0.0)              ; first element where time has skipped back
jump = where(time(index+1)-time(index) gt 0.06)             ; last element before time skips forward again
help,skip,jump

nfirst = min(where(jump ge skip(0)))
njump  = n_elements(jump)
jump   = jump(nfirst:njump-1)                               ; trims any jumps before the first skip

; if (jump(0) lt skip(0) and n_elements(jump) gt n_elements(skip)) then begin
;  njump = n_elements(jump)
;  jump = jump(1:njump-1)
;  help,skip,jump
; endif
;
; Here are some ad-hoc adjustments to cope with individual flights
;
if (fnum eq 'b765') then skip = skip([0,2,3,4])
if (fnum eq 'b800') then skip = skip(0:6)
;if (fnum eq 'b882') then begin
;  skip = skip(0:2)
;  jump = [jump(0:1),jump(3:(n_elements(jump)-1))]
;endif
if (fnum eq 'b884') then begin
  jump = [jump(0),jump(2:(n_elements(jump)-1))]
endif

if skip(0) gt -1 then begin
  print,'Skip times: ',gmt(time(skip))
  print,'Jump times: ',gmt(time(jump))
  nevent = n_elements(skip)                                   ; count of number of events
  for j=0,nevent-1 do begin
    deltat = time(skip(j)-1) - time(skip(j)) +0.05            ; amount to shift times forward
    stime(skip(j):jump(j)) = stime(skip(j):jump(j)) + deltat  ; move this group of times forward
  endfor
endif

; **********************************************************************************************************
; now re-create a 20Hz time array starting at the same time and find the start of the first FULL second

atime = stime                            ; atime holds original time values read from data corrected for jumps

btime = round(atime*100)                 ; using ROUND for IDL compatibility in place of NINT
ctime = round(atime)*100
diff = btime - ctime
nsec = max(btime)/100 - min(btime)/100 - 2 ; remove the first and last second that has data because 
                                           ; it will generally not be full
help,nsec
nvals20 = long(nsec*20)                 ; the number of 20Hz values in the full seconds
help,nvals20
nstart  = min(where(diff eq 0))         ; start index of the first full second of data
help,nstart

dtime = dindgen(nvals20)*0.05+double(btime(nstart))/100.  ; regular 20Hz time array spanning same interval
help,dtime

; **********************************************************************************************************
; now spline interpolate data onto the regular time array
print,'Interpolate data onto regular time array.'

help,atime,tc
Tc   = spline(atime, tc, dtime, 1.0)
help,dtime,tc
RH   = spline(atime, rh, dtime, 1.0)
Pres = spline(atime, pres, dtime, 1.0)
V    = spline(atime, v, dtime, 1.0)
U    = spline(atime, u, dtime, 1.0)
W    = spline(atime, w, dtime, 1.0)
Lat  = spline(atime, lat, dtime, 1.0)
Lon  = spline(atime, lon, dtime, 1.0)
alt  = spline(atime, alt, dtime, 1.0)
Vn   = spline(atime, vn, dtime, 1.0)
Ve   = spline(atime, ve, dtime, 1.0)
Vz   = spline(atime, vz, dtime, 1.0)
Roll = spline(atime, roll, dtime, 1.0)
Pitch= spline(atime, pitch, dtime, 1.0)
Hdg  = spline(atime, hdg, dtime, 1.0)
Tas  = spline(atime, tas, dtime, 1.0)
Aoss = spline(atime, aoss, dtime, 1.0)
Dpaoa= spline(atime, dpaoa, dtime, 1.0)
Dpaoss= spline(atime, dpaoss, dtime, 1.0)
;Status= spline(atime, status, dtime, 1.0)

print,'Interpolation complete.'
; tplot,dtime,lat,psym=1

; **********************************************************************************************************
; create additional data arrays, to be calculated from input data

Aoa = -1.0*(A_0 +(A_alpha*dpaoa) +(A_beta*dpaoss))  ; calculate AOA from existing variables

; **********************************************************************************************************
; if output is to be 1hz averages then first create these
if keyword_set(make_average) then begin
  dtime = REFORM(dtime,20,nsec)
  dtime = REFORM(dtime(0,*))
  print,dtime(0)
  Tc   = MEAN(REFORM(tc,20,nsec),DIMENSION=1,/NAN)
  RH   = MEAN(REFORM(rh,20,nsec),DIMENSION=1,/NAN)
  Pres = MEAN(REFORM(pres,20,nsec),DIMENSION=1,/NAN)
  V    = MEAN(REFORM(v,20,nsec),DIMENSION=1,/NAN)
  U    = MEAN(REFORM(u,20,nsec),DIMENSION=1,/NAN)
  W    = MEAN(REFORM(w,20,nsec),DIMENSION=1,/NAN)
  Lat  = MEAN(REFORM(lat,20,nsec),DIMENSION=1,/NAN)
  Lon  = MEAN(REFORM(lon,20,nsec),DIMENSION=1,/NAN)
  alt  = MEAN(REFORM(alt,20,nsec),DIMENSION=1,/NAN)
  Vn   = MEAN(REFORM(vn,20,nsec),DIMENSION=1,/NAN)
  Ve   = MEAN(REFORM(ve,20,nsec),DIMENSION=1,/NAN)
  Vz   = MEAN(REFORM(vz,20,nsec),DIMENSION=1,/NAN)
  Roll = MEAN(REFORM(roll,20,nsec),DIMENSION=1,/NAN)
  Pitch= MEAN(REFORM(pitch,20,nsec),DIMENSION=1,/NAN)
  Hdg  = MEAN(REFORM(hdg,20,nsec),DIMENSION=1,/NAN)
  Tas  = MEAN(REFORM(tas,20,nsec),DIMENSION=1,/NAN)
  Aoss = MEAN(REFORM(aoss,20,nsec),DIMENSION=1,/NAN)
  Aoa  = MEAN(REFORM(aoa,20,nsec),DIMENSION=1,/NAN)
  Dpaoa= MEAN(REFORM(dpaoa,20,nsec),DIMENSION=1,/NAN)
  Dpaoss= MEAN(REFORM(dpaoss,20,nsec),DIMENSION=1,/NAN)
;  Status= MEAN(REFORM(status,20,nsec),DIMENSION=1,/NAN)
  help,dtime,tc
endif

start_time = dtime(0)
date = READ_ASCII(daq_files(jfile),DATA_START=0,NUM_RECORDS=1) ; read date information from ascii file
day = FLOOR(date.field1(0))
month = FLOOR(date.field1(1))
year = FLOOR(date.field1(2))

; **********************************************************************************************************
; Test AIMMS date information against Core. If Core data started on the previous day, then adjust accordingly.
; The only plausible circumstance is that Core data recording commence before midnight and AIMMS data after midnight,
; so set AIMMS date information equal to Core and increment AIMMS time by 24*60*60 = 86400.
; **********************************************************************************************************

if (day ne cday) or (month ne cmonth) or (year ne cyear) then begin
  day = cday
  month = cmonth
  year = cyear
  start_time = start_time + 86400.
  print,'AIMMS date and start time re-alligned with Core.'
endif

print,'Start time =',start_time

; **********************************************************************************************************
; if this is the first ascii file, read date information, create NetCDF file name, open it and write other required
; creation information - 
; **********************************************************************************************************

if jfile eq 0 then begin
  date_str = '00000000'                 ; create date string for NC file - yyyymmdd
  STRPUT,date_str,STRTRIM(year,1),0
  if month lt 10 then pos=5 else pos=4
  STRPUT,date_str,STRTRIM(month,1),pos
  if day lt 10 then pos=7 else pos=6
  STRPUT,date_str,STRTRIM(day,1),pos

; create NC filename
  ;nc_file  = basedir+'/AIMMS/'+fdir+'metoffice-aimms_faam_'+date_str+'_'+version+'_'+rstring+'_'+fnum
  ;if keyword_set(make_average) then nc_file=nc_file+'_1hz'
  ;nc_file = nc_file+'.nc'
  nc_file = ofile
  print,'Input:   ', daq_files(jfile)
  Print,'Output:  ', nc_file
  
; open the NetCDF output file and create global attributes and variable information
; id=NCDF_CREATE(nc_file,/CLOBBER)

  id=NCDF_CREATE(ofile, /CLOBBER)
  s_start = strtrim(string(gmt(dtime(0))),2)
  if strlen(s_start) lt 6 then s_start='0'+s_start
  s_end   = strtrim(string(gmt(max(dtime))),2)
  if strlen(s_end) lt 6 then s_end='0'+s_end
  
  NCDF_ATTPUT,id,/GLOBAL,'title','Standard AIMMS-20 data from '+fnum+' on '+date_str
  NCDF_ATTPUT,id,/GLOBAL,'AIMMS_files',daq_file
  NCDF_ATTPUT,id,/GLOBAL,'Date',date_str
  NCDF_ATTPUT,id,/GLOBAL,'TimeInterval',s_start+'-'+s_end
  NCDF_ATTPUT,id,/GLOBAL,'Conventions','CF-1.6'
  NCDF_ATTPUT,id,/GLOBAL,'INSTITUTION','FAAM'
  NCDF_ATTPUT,id,/GLOBAL,'SOURCE','FAAM BAe146 aircraft data'
  NCDF_ATTPUT,id,/GLOBAL,'REFERENCES','http://www.faam.ac.uk'
  ;
  descriptor = 'Post-processed 20Hz AIMMS data converted to NetCDF'
  if keyword_set(make_average) then descriptor=descriptor+' and 1hz averages'
  NCDF_ATTPUT,id,/GLOBAL,'Description',descriptor
  NCDF_ATTPUT,id,/GLOBAL,'Post_processor_executable','ekf556'
  NCDF_ATTPUT,id,/GLOBAL,'Software_version',version

; **********************************************************************************************************
; Define output variables and attributes
; **********************************************************************************************************

  LTIME = NCDF_DIMDEF(id,'TIME',/UNLIMITED)   ; TIME dimension created unlimited so as to be extensible
  LCAL = NCDF_DIMDEF(id,'CONST',1)

  cp0_id = NCDF_VARDEF(id,'CP_0',[LCAL],/FLOAT)
  NCDF_ATTPUT,id,cp0_id,'units','1'
  NCDF_ATTPUT,id,cp0_id,'long_name','CP_0 calibration coefficient'

  cpa_id = NCDF_VARDEF(id,'CP_alpha',[LCAL],/FLOAT)
  NCDF_ATTPUT,id,cpa_id,'units','1'
  NCDF_ATTPUT,id,cpa_id,'long_name','CP_alpha calibration coefficient'

  cpb_id = NCDF_VARDEF(id,'CP_beta',[LCAL],/FLOAT)
  NCDF_ATTPUT,id,cpb_id,'units','1'
  NCDF_ATTPUT,id,cpb_id,'long_name','CP_beta calibration coefficient'

  B0_id = NCDF_VARDEF(id,'B_0',[LCAL],/FLOAT)
  NCDF_ATTPUT,id,B0_id,'units','degree'
  NCDF_ATTPUT,id,B0_id,'long_name','B_0 calibration coefficient'

  Ba_id = NCDF_VARDEF(id,'B_alpha',[LCAL],/FLOAT)
  NCDF_ATTPUT,id,Ba_id,'units','degree'
  NCDF_ATTPUT,id,Ba_id,'long_name','B_alpha calibration coefficient'

  Bb_id = NCDF_VARDEF(id,'B_beta',[LCAL],/FLOAT)
  NCDF_ATTPUT,id,Bb_id,'units','degree'
  NCDF_ATTPUT,id,Bb_id,'long_name','B_beta calibration coefficient'

  A0_id = NCDF_VARDEF(id,'A_0',[LCAL],/FLOAT)
  NCDF_ATTPUT,id,A0_id,'units','degree'
  NCDF_ATTPUT,id,A0_id,'long_name','A_0 calibration coefficient'

  Aa_id = NCDF_VARDEF(id,'A_alpha',[LCAL],/FLOAT)
  NCDF_ATTPUT,id,Aa_id,'units','degree'
  NCDF_ATTPUT,id,Aa_id,'long_name','A_alpha calibration coefficient'

  Ab_id = NCDF_VARDEF(id,'A_beta',[LCAL],/FLOAT)
  NCDF_ATTPUT,id,Ab_id,'units','degree'
  NCDF_ATTPUT,id,Ab_id,'long_name','A_beta calibration coefficient'

; **********************************************************************************************************

  time_units = 'seconds since '+strmid(date_str,0,4)+'-'+strmid(date_str,4,2)+'-'+strmid(date_str,6,2)+' 00:00:00 +0000'
  time_id = NCDF_VARDEF(id,'TIME',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,time_id,'units',time_units
  NCDF_ATTPUT,id,time_id,'long_name','time of measurement'
  NCDF_ATTPUT,id,time_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,time_id,'standard_name','time'

  tk_id = NCDF_VARDEF(id,'TK',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,tk_id,'units','K'
  NCDF_ATTPUT,id,tk_id,'long_name','AIMMS true air temperature'
  NCDF_ATTPUT,id,tk_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,tk_id,'standard_name','air_temperature'

  rh_id = NCDF_VARDEF(id,'RH',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,rh_id,'units','percent'
  NCDF_ATTPUT,id,rh_id,'long_name','AIMMS Relative humidity wrt water'
  NCDF_ATTPUT,id,rh_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,rh_id,'standard_name','relative_humidity'

  p_id = NCDF_VARDEF(id,'PRES',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,p_id,'units','hPa'
  NCDF_ATTPUT,id,p_id,'long_name','AIMMS Static pressure'
  NCDF_ATTPUT,id,p_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,p_id,'standard_name','air_pressure'

  u_id = NCDF_VARDEF(id,'U',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,u_id,'units','m s-1'
  NCDF_ATTPUT,id,u_id,'long_name','AIMMS eastwards wind component'
  NCDF_ATTPUT,id,u_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,u_id,'standard_name','eastward_wind'

  v_id = NCDF_VARDEF(id,'V',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,v_id,'units','m s-1'
  NCDF_ATTPUT,id,v_id,'long_name','AIMMS northwards wind component'
  NCDF_ATTPUT,id,v_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,v_id,'standard_name','northward_wind'
 
  w_id = NCDF_VARDEF(id,'W',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,w_id,'units','m s-1'
  NCDF_ATTPUT,id,w_id,'long_name','AIMMS vertical wind component'
  NCDF_ATTPUT,id,w_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,w_id,'standard_name','upward_air_velocity'

  lat_id = NCDF_VARDEF(id,'LAT',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,lat_id,'units','degree_north'
  NCDF_ATTPUT,id,lat_id,'long_name','AIMMS GPS latitude'
  NCDF_ATTPUT,id,lat_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,lat_id,'standard_name','latitude'

  lon_id = NCDF_VARDEF(id,'LON',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,lon_id,'units','degree_east'
  NCDF_ATTPUT,id,lon_id,'long_name','AIMMS GPS longitude'
  NCDF_ATTPUT,id,lon_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,lon_id,'standard_name','longitude'
  
  alt_id = NCDF_VARDEF(id,'ALT',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,alt_id,'units','m'
  NCDF_ATTPUT,id,alt_id,'long_name','AIMMS GPS altitude'
  NCDF_ATTPUT,id,alt_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,alt_id,'standard_name','altitude'

  vn_id = NCDF_VARDEF(id,'VN',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,vn_id,'units','m s-1'
  NCDF_ATTPUT,id,vn_id,'long_name','AIMMS Northwards ground speed'
  NCDF_ATTPUT,id,vn_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,vn_id,'standard_name','platform_speed_wrt_ground'
  

  ve_id = NCDF_VARDEF(id,'VE',[LTIME],/FLOAT); now read data from the ascii file
  NCDF_ATTPUT,id,ve_id,'units','m s-1'
  NCDF_ATTPUT,id,ve_id,'long_name','AIMMS Eastwards ground speed'
  NCDF_ATTPUT,id,ve_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,ve_id,'standard_name','platform_speed_wrt_ground'

  vz_id = NCDF_VARDEF(id,'VZ',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,vz_id,'units','m s-1'
  NCDF_ATTPUT,id,vz_id,'long_name','AIMMS vertical speed'
  NCDF_ATTPUT,id,vz_id,'_FillValue',-9999.0
; no standard name

  roll_id = NCDF_VARDEF(id,'ROLL',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,roll_id,'units','degree'
  NCDF_ATTPUT,id,roll_id,'long_name','AIMMS roll angle'
  NCDF_ATTPUT,id,roll_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,roll_id,'standard_name','platform_roll_angle'

  ptch_id = NCDF_VARDEF(id,'PITCH',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,ptch_id,'units','degree'
  NCDF_ATTPUT,id,ptch_id,'long_name','AIMMS pitch angle'
  NCDF_ATTPUT,id,ptch_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,ptch_id,'standard_name','platform_pitch_angle'

  hdg_id = NCDF_VARDEF(id,'HDG',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,hdg_id,'units','degree'
  NCDF_ATTPUT,id,hdg_id,'long_name','AIMMS Heading angle'
  NCDF_ATTPUT,id,hdg_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,hdg_id,'standard_name','platform_yaw_angle'

  tas_id = NCDF_VARDEF(id,'TAS',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,tas_id,'units','m s-1'
  NCDF_ATTPUT,id,tas_id,'long_name','AIMMS True air speed'
  NCDF_ATTPUT,id,tas_id,'_FillValue',-9999.0
  NCDF_ATTPUT,id,tas_id,'standard_name','platform_speed_wrt_air'

  aoss_id = NCDF_VARDEF(id,'AOSS',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,aoss_id,'units','degree'
  NCDF_ATTPUT,id,aoss_id,'long_name','AIMMS angle of sideslip (positive, flow from left)'
  NCDF_ATTPUT,id,aoss_id,'_FillValue',-9999.0
; no standard name

  dpaoa_id = NCDF_VARDEF(id,'DPAOA',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,dpaoa_id,'units','1'
  NCDF_ATTPUT,id,dpaoa_id,'long_name','AIMMS non-dimensional angle of attack differential pressure'
  NCDF_ATTPUT,id,dpaoa_id,'_FillValue',-9999.0
; no standard name  

  dpaoss_id = NCDF_VARDEF(id,'DPAOSS',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,dpaoss_id,'units','1'
  NCDF_ATTPUT,id,dpaoss_id,'long_name','AIMMS non-dimensional angle of sideslip differential pressure'
  NCDF_ATTPUT,id,dpaoss_id,'_FillValue',-9999.0
; no standard name

;  status_id = NCDF_VARDEF(id,'STATUS',[LTIME],/FLOAT)
;  NCDF_ATTPUT,id,status_id,'units',' '
;  NCDF_ATTPUT,id,status_id,'long_name','AIMMS Status flag (0 - solution invalid)'
;  NCDF_ATTPUT,id,status_id,'_FillValue',-9999.0
; no standard name

; additional variables
  aoa_id = NCDF_VARDEF(id,'AOA',[LTIME],/FLOAT)
  NCDF_ATTPUT,id,aoa_id,'units','degree'
  NCDF_ATTPUT,id,aoa_id,'long_name','AIMMS angle of attack (positive, flow from below aircraft)'
  NCDF_ATTPUT,id,aoa_id,'_FillValue',-9999.0
; no standard name

  NCDF_CONTROL,id,/ENDEF           ; end of file definition stage
  print,'NetCDF file definition completed.'
  
; first file so write the aerodynamic calibration coeffs to output

  NCDF_VARPUT,id,cp0_id,cp_0 
  NCDF_VARPUT,id,cpa_id,cp_alpha
  NCDF_VARPUT,id,cpb_id,cp_beta
  NCDF_VARPUT,id,A0_id,A_0 
  NCDF_VARPUT,id,Aa_id,A_alpha
  NCDF_VARPUT,id,Ab_id,A_beta
  NCDF_VARPUT,id,B0_id,B_0 
  NCDF_VARPUT,id,Ba_id,B_alpha
  NCDF_VARPUT,id,Bb_id,B_beta
  print,'NetCDF aerodynamic constants written.'
  
; First file, so write out the entire Core time array to the time variable and then pad all variables with NaN
  NCDF_VARPUT,id,time_id,core_time,OFFSET=0L
  pad_value = -9999.0
  padval = fltarr(n_elements(core_time))+pad_value       ; set array of fill-in values

  NCDF_VARPUT, id, tk_id, padval, OFFSET=0L
  NCDF_VARPUT, id, p_id, padval, OFFSET=0L
  NCDF_VARPUT, id, lat_id, padval, OFFSET=0L
  NCDF_VARPUT, id, lon_id, padval, OFFSET=0L
  NCDF_VARPUT, id, rh_id, padval, OFFSET=0L
  NCDF_VARPUT, id, u_id, padval, OFFSET=0L
  NCDF_VARPUT, id, v_id, padval, OFFSET=0L
  NCDF_VARPUT, id, w_id, padval, OFFSET=0L
  NCDF_VARPUT, id, alt_id, padval, OFFSET=0L
  NCDF_VARPUT, id, vn_id, padval, OFFSET=0L
  NCDF_VARPUT, id, ve_id, padval, OFFSET=0L
  NCDF_VARPUT, id, vz_id, padval, OFFSET=0L
  NCDF_VARPUT, id, roll_id, padval, OFFSET=0L
  NCDF_VARPUT, id, ptch_id, padval, OFFSET=0L
  NCDF_VARPUT, id, hdg_id, padval, OFFSET=0L
  NCDF_VARPUT, id, tas_id, padval, OFFSET=0L
  NCDF_VARPUT, id, aoss_id, padval, OFFSET=0L
  NCDF_VARPUT, id, aoa_id, padval, OFFSET=0L
  NCDF_VARPUT, id, dpaoa_id, padval, OFFSET=0L
  NCDF_VARPUT, id, dpaoss_id, padval, OFFSET=0L
;  NCDF_VARPUT, id, status_id, padval, OFFSET=0L
    
endif                              ; end of items required when processing first file
  
; output only the data for full seconds and on adjusted time
; if not(keyword_set(extendtime)) then NCDF_VARPUT,id,time_id, dtime, OFFSET=data_offset                          
; TIME variable already pre-filled with core_time

data_offset = where(core_time eq start_time)
print,'Data output offset =',data_offset

NCDF_VARPUT,id,tk_id,tc + 273.15, OFFSET=data_offset   ;  convert to K
NCDF_VARPUT,id,rh_id,rh * 100.0, OFFSET=data_offset    ; convert to percent
NCDF_VARPUT,id,p_id,pres* 0.01, OFFSET=data_offset     ; convert to hPa
NCDF_VARPUT,id,u_id,u, OFFSET=data_offset
NCDF_VARPUT,id,v_id,v, OFFSET=data_offset
NCDF_VARPUT,id,w_id,-1.0 * w, OFFSET=data_offset       ; change sign
NCDF_VARPUT,id,lat_id,lat, OFFSET=data_offset
NCDF_VARPUT,id,lon_id,lon, OFFSET=data_offset
NCDF_VARPUT,id,alt_id,alt, OFFSET=data_offset
NCDF_VARPUT,id,vn_id,vn, OFFSET=data_offset
NCDF_VARPUT,id,ve_id,ve, OFFSET=data_offset
NCDF_VARPUT,id,vz_id,vz, OFFSET=data_offset            ; not multiplied by -1.0
NCDF_VARPUT,id,roll_id,roll, OFFSET=data_offset
NCDF_VARPUT,id,ptch_id,pitch, OFFSET=data_offset
NCDF_VARPUT,id,hdg_id,hdg, OFFSET=data_offset
NCDF_VARPUT,id,tas_id,tas, OFFSET=data_offset
NCDF_VARPUT,id,aoss_id,-1.0*aoss, OFFSET=data_offset   ; change sign
NCDF_VARPUT,id,aoa_id,Aoa, OFFSET=data_offset
NCDF_VARPUT,id,dpaoa_id,dpaoa, OFFSET=data_offset   ;x -1.0?
NCDF_VARPUT,id,dpaoss_id,dpaoss, OFFSET=data_offset
;NCDF_VARPUT,id,status_id,status, OFFSET=data_offset

last_time = max(dtime)                           ; save the end of data from this ascii file

ENDFOR
; ******************************************************************************************************************
; end of loop over the number of ascii input files
; ******************************************************************************************************************

NCDF_CLOSE,id                  ;  close the NetCDF output


END