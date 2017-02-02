import os
import re


DATA_TYPES = {'core-hires':        'core_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bBdD][0-9][0-9][0-9].nc$',
              'core-lowres':       'core_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bBdD][0-9][0-9][0-9]_1[Hh]z.nc$',
              'core-descrip':      'core_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bBdD][0-9][0-9][0-9]_descrip.txt$',
              'core-quality':      'core_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bBdD][0-9][0-9][0-9]_quality.txt$',
              'dropsonde-proc':    '.*dropsonde_faam_.*_r.*_[bBdD][0-9][0-9][0-9]_proc.nc$',                    
              'dropsonde-raw':     '.*dropsonde_faam_.*_r.*_[bBdD][0-9][0-9][0-9]_raw.nc$',
              'dropsonde-descrip': '.*dropsonde_faam_.*_r.*_[bBdD][0-9][0-9][0-9]_descrip.txt$',
              'flight-cst':        'flight-cst_faam_20[0-9][0-9][0-1][0-9][0-3][0-9]_r.*_[bBdD][0-9][0-9][0-9].txt$',
              'flight-log':        'flight-log_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bBdD][0-9][0-9][0-9].pdf$',
              'flight-sum':        'flight-sum_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bBdD][0-9][0-9][0-9].txt$',
              'rawdrs':            'core_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bB][0-9][0-9][0-9]_rawdrs.zip$',
              'rawgin':            'core_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bB][0-9][0-9][0-9]_rawgin.zip$',
              'rawgps':            'core_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bB][0-9][0-9][0-9]_rawgps.zip$',
              'rawdlu':            'core_faam_20[0-9][0-9][0-1][0-9][0-3][0-9].*_r.*_[bB][0-9][0-9][0-9]_rawdlu.zip$'}


def get_revision_from_filename(filename):
    """
    Extracts the revision number from the netCDF core filename

        Example:
        >>> file = 'core_faam_20090529_v004_r1_b450.nc'
        >>> getRevisionFromFilename(file)
        1
        >>>
    """
    fn = os.path.basename(filename)
    fn = fn.split('.')[0]
    parts = fn.split('_')
    for p in parts:
        if re.match('r\d', p):
            result = int(p[1:])
            return result                
    return


def get_data_type_from_filename(filename):
    """
    returns the datatype for the input filename determined using the DATA_TYPES
    dictionary
    """
    for key in DATA_TYPES.keys():
        if re.match(DATA_TYPES[key], os.path.basename(filename)):
            return key
    return


def get_fid_from_filename(filename):
    """
    Extracts the flight number from the netCDF core filename
        
    Example:
        >>> ncfile = 'core_faam_20090529_v004_r1_b450.nc'
        >>> getFlightNumbserFromFilename(ncfile)
        b450
        >>>
    """         
    fn = os.path.basename(filename)
    fn = fn.split('.')[0]
    parts = fn.split('_')   
    for p in parts:
        if re.match('[bBdD][0-9][0-9][0-9]', p):
            return p.lower()
    return


def get_date_from_filename(filename):
    """
    Extracts the flight date from the netCDF core filename
        
    Example:
        >>> ncfile = 'core_faam_20090529_v004_r1_b450.nc'
        >>> getDateFromFilename(ncfile)
        20090529
        >>>
    """     
    fn = os.path.basename(filename)
    fn = fn.split('.')[0]
    parts = fn.split('_')   
    for p in parts:
        if re.match('20\d{6}', p):
            return p
        elif re.match('20\d{12}', p):                                                                                                       
            return p                                                                                                                        
        else:
            pass
    return


class File_Info(object):
    """
    Holds all file specific information for a FAAM data file:
      * filename
      * path
      * Flight Number (fid)
      * date
      * revision
      * datatype    
    """
    def __init__(self, filename):
        self.filename = os.path.basename(filename)
        self.path = os.path.dirname(filename)
        self.fid = get_fid_from_filename(filename)
        self.date = get_date_from_filename(filename)
        self.rev = get_revision_from_filename(filename)
        self.data_type = get_data_type_from_filename(filename)

    def __str__(self):
        output = '\n'
        labels = ['Filename', 'Path', 'FID', 'Date', 'Revision', 'Data Type']
        values = [self.filename,
                  self.path,
                  self.fid,
                  self.date,
                  str(self.rev),
                  self.data_type]
        for s in zip(labels, values):
            output += '%9s: %s\n' % s
        return output
    
#    def __cmp__(self, obj):
#        cmp_key = '%4s_%0.3i_%s' % (self.fid, self.rev, self.datatype)
#        cmp_key_other = '%4s_%0.3i_%s' % (obj.fid, obj.rev, obj.datatype)
#        if cmp_key < cmp_key_other:
#            return -1
#        elif cmp_key == cmp_key_other:
#            return 0
#        elif cmp_key > cmp_key_other:
#            return 1
#        else:
#            pass

    def __eq__(self, other):
        return ((self.fid, self.rev, self.data_type) == 
                (other.fid, other.rev, other.data_type))
    def __ne__(self, other):
        return not self == other
    def __gt__(self, other):
        return (self.fid, self.rev) > (other.fid, other.rev)
    def __lt__(self, other):
        return (self.fid, self.rev) < (other.fid, other.rev)
    def __ge__(self, other):
        return (self > other) or (self == other)
    def __le__(self, other):
        return (self < other) or (self == other)


