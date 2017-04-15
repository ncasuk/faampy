FUNCTION findcorefile, basedir, fnum, core1hz

; FUNCTION:   FINDCOREFILE
;
; PURPOSE:    Returns a string value containing the full path/filename information for a FAAM Core NetCDF file.
;
; ARGUMENTS:  BASEDIR - String variable containing the base directory in which to start searching. This assumes that data files are organised
;                       within a directory structure: /project/obr/project_name with sub-directories for Core and 
;                       other data below that level.
;                       Example: /pr

fnum=STRLOWCASE(fnum)
help,fnum
corefile=basedir+'/faam_core/'+'*'+fnum+'*.nc'   
corefile=file_search(corefile) 
print,'Core:     ',corefile

core1hz=basedir+'/faam_core/'+'*'+fnum+'*_1hz.nc'   
core1hz=file_search(core1hz) 
print,'Core_1hz: ',core1hz


return, core1hz
END
 