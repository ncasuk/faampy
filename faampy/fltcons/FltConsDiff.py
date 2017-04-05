'''
Created on 30 Dec 2009

@author: axel
'''

import CoreData

import copy
import difflib
import os
import re
       

def unique(alist):
    """returns a list of unique values and keeps the order of their occurence"""
    
    aset = set(alist)
    index = []
    for val in aset:
        index.append( alist.index( val ))
    
    tmp = zip( index, list(aset) )
    tmp.sort()
    newlist = []
    for val in tmp:
        newlist.append( val[1] )
    
    return newlist


def __getFlightConstants__(ncfilename):
        
    cd = CoreData()
    cd.open(ncfilename)
    
    try:
        fc = cd.ds.Flight_Constants
    except:
        pass
    
    try:
        fc = cd.ds.FLIGHT_CONSTANTS
    except:
        pass
    
    cd.close()
    
    return fc.split('\n')



class FlightConstants(object):
    
    def __init__(self, Filelist):
        
        self.Filelist = Filelist

    
    def diff( self, id1, id2, r1=None, r2=None ):
        
        cdfl = CoreData.FileList()
        cdfl.__createFileList__()
        fn1 = cdf.__filterByFlightNumberAndRevision__( id1, r1 )
        fn2 = cdf.__filterByFlightNumberAndRevision__( id2, r2 )
        
        fc1 = __getFlightConstants__( fn1 )
        fc2 = __getFlightConstants__( fn2 )

        differ = difflib.HtmlDiff( tabsize=4, wrapcolumn=40 )
        html = differ.make_file( fc1, fc2, context=False )
        
        outfile = open( '/home/axel/tmp/difftest.html', 'w' )
        outfile.write(html)
        outfile.close()


    def get_table( self ):
                       
        for file in self.Filelist:
            #print(file)
            cd = CoreData.Summary()
            cd.open( file )
            cd.get_file_info()
            cd.get_flight_info()
            cd.get_data_info()
            cd.get_var_info()
            cd.get_flicon_info()
            
            self.table.append(cd)
            
            cd.close()
            del(cd)

        
    def check_calfactor(self, par=None):

        caltable = []
        for entry in self.table:
            caltable.append(entry)
            
        #sort by flying time
        _time = []
        _cal = []
        for entry in caltable:
            _time.append( time.mktime( entry.file_info['created'] ))
            _cal.append( entry.cal_info[par][0] )
        
        ucal = unique(_cal)
        print 'INFO: %i different cal factors' % len(ucal)
        
        numit = dict(zip(ucal, range(len(ucal))))
        new = []
        for i in _cal:
            new.append( numit[i] ) 

        print new
        for i in ucal: print i


#if __name__ == '__main__':
calfactor_list = ['TASCORR', 'CALCABT', 'GELIMS', 'CALGE', 'PRTCCAL', 'HEIMCAL', 'INSLEVL', 'CALLWC', 'CALNPRS', 'CALNTMP', 'CALNBTS', 'CALNGTS', 'CALNRTS', 'CALNBBS', 'CALNGBS', 'CALNRBS', 'CALNHUM', 'CALNSTS', 'CALNVLW', 'CALNVLR', 'CALNVLC', 'CALNVTW', 'CALNVTR', 'CALNVTC', 'CALRSL', 'CALRST', 'CALO3', 'CALO3P', 'CALO3T', 'CALO3F', 'CALO3MX', 'CALNO', 'CALNO2', 'CALNOX', 'CALNOMX', 'CALSO2', 'CALCOMR', 'CALCOMX', 'CALCABP', 'CALS9SP', 'CALPLIN', 'CALPLOG', 'CALUP1S', 'CALUP2S', 'CALUIRS', 'CALLP1S', 'CALLP2S', 'CALLIRS', 'CALCUCF', 'CALCURF', 'CALCUIF', 'CALCLCF', 'CALCLRF', 'CALCLIF', 'TRFCTR', 'CALDIT', 'CALNDT', 'CALTP1', 'CALTP2', 'CALTP3', 'CALTP4', 'CALTP5', 'AOA_A0', 'AOA_A1', 'AOSS_B0', 'AOSS_B1', 'TOLER', 'TASCOR1', 'ALPH0', 'ALPH1', 'BET0', 'BET1', 'CALTNOS', 'CALTSAM', 'CALTAMB', 'CALTSRC', 'CALHTR1', 'CALHTR2', 'CALISRC', 'INSPOSN']

cdfl = CoreData.FileList()
cdfl.__createFileList__()
cdfl.__filterLatestRevison__()
cdfl.__sortByFlightNumber__()


FC = FlightConstants(cdfl.FileList[420:])
#FC.diff(457, 460, r1=1, r2=0)

FC.get_table()
#FC.check_calfactor()
for cal in calfactor_list:
    FC.check_calfactor(cal)

print '*** END ***'


