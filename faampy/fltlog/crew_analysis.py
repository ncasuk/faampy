'''
Created on 1 Nov 2011

@author: axel
'''

ROOT_PATH = '/mnt/faamarchive/badcMirror/ftp.badc.rl.ac.uk/badc/faam/data/'

import re
import psycopg2
import os

crewPlaces = { 'MetOffice':     ( -3.474732, 50.727408 ),
               'Manchester':    ( -2.231981, 53.465924 ),
               'York':          ( -1.080267, 53.965147 ),
               'Leeds':         ( -1.556966, 53.807884 ),
               'CEH Edinburgh': ( -3.206400, 55.861881 ),
               'Reading':       ( -0.937170, 51.439382 ) }


def get_fids():
    sql_str = """SELECT FT.fid FROM flight_tracks AS FT WHERE FT.airport_takeoff = 'Cranfield' AND
                    airport_land = 'Cranfield' ORDER BY FT.fid;"""
    sql_conn = "dbname='flight_analysis_uk' user='axel' password='xxxxxxxx'"
    conn = psycopg2.connect( sql_conn )
    cur = conn.cursor()
    cur.execute( sql_str )
    result = cur.fetchall()
    cur.close()
    conn.close()
    return zip(*result)[0]


def get_filelist():
    list_inst = ( ['FAAM',],
              ['Directflight', 'DFL'],
              ['MetOffice','Met Office'],
              ['Manchester', 'UMIST'],
              ['Leeds',],
              ['York',],
              ['UEA', 'Anglia',],
              ['Reading',],
              ['Cambridge',],
              ['Leicester',],
              ['CEH',],
              ['Edinburgh',],
              ['Imperial',],
              ['Hertfordshire',],
              ['Oxford',],
              ['Sussex',],
              ['Glasgow',])
#              ['Karlsruhe',],
#              ['Mainz', 'MPI'],
#              ['Aquila',],
#              ['Denver',],
#              ['DLR',],
#              ['BBC',],)


summary = []
for ins in list_inst:
    cnt = counter( crews, ins )
    summary.append( (cnt, ins[0]) )
    summary.sort()
    summary.reverse()





    filelist = []
    for root, subFolders, files in os.walk( ROOT_PATH ):
        for file in files:
            if file.endswith('00README'):
                filelist.append( os.path.join( root, file ) )
#    return filelist


def filename_check( filename, fid ):
    result = False
    tmp = filename.split( '/' )
    if tmp[-1] == '00README':
        if tmp[-2].startswith( 'b%.3i' % fid ):
            result = True
    return result


def get_crews( filelist, fids ):
    crews = {}
    for fid in fids:
        if os.path.exists( '/home/axel/tmp_fltlog/b%.3i_flightlog_crew_list.txt' % fid ):
            key = 'b%.3i' % fid
            fin = open( '/home/axel/tmp_fltlog/b%.3i_flightlog_crew_list.txt' % fid, 'r')
            crews[key] = fin.readlines()
            fin.close()
        else:
            for file in filelist:
                if filename_check( file, fid ):
                    key = 'b%.3i' % fid
                    fin = open(file, 'r')
                    crews[key] = fin.readlines()
                    fin.close()
    return crews


def write_crews( crews ):
    outfile = open('/home/axel/crews.txt', 'w')
    keys = list(crews.keys())
    keys.sort()
    #k.sort()
    for k in keys:
        for line in crews[k]:
            outfile.write( k + ':   ' + line)
    outfile.close()

flights_with_crewlist = []
def counter( crews, institution ):
    global flight_with_crewlist
    keys = list(crews.keys())
    keys.sort()
    cnt = 0
    for k in keys:
        got_hit = False
        for line in crews[k]:
            for inst in institution:
                if str.lower( inst ) in str.lower( line ):
                    cnt += 1
                    if not got_hit:
                        got_hit = True
                        flights_with_crewlist.append( k )
                #print( k + ': ', line )
    print(institution[0] + ': ' + str(cnt) )
    return cnt


import scipy
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
def plot_circle( indata ):
    plt.rcParams['font.size'] = 22
    plt.rcParams['figure.figsize'] = 12, 12

    indata = indata[2:]

# make a square figure and axes
    plt.figure(1, figsize=(12,12))
    ax = plt.axes([0.1, 0.05, 0.8, 0.9])

    #labels = 'Frogs', 'Hogs', 'Dogs', 'Logs'
    #fracs = [15,30,45, 10]

    frac_raw, labels  = zip( *indata )
    frac_raw = scipy.float32( scipy.array( frac_raw ))
    print( scipy.sum(frac_raw))
    fracs = frac_raw / scipy.sum(frac_raw)*100.

    plt.pie(fracs, labels=labels, autopct='%1.1f%%', shadow=True)
    #plt.title('Raining Hogs and Dogs', bbox={'facecolor':'0.8', 'pad':5})
    plt.savefig( '/home/axel/plt5.png' )
    plt.clf()


def get_crew_centroid():
    crewPlaces = { 'MetOffice':     [( -3.474732, 50.727408 ), 377],
                   'Manchester':    [( -2.231981, 53.465924 ), 237],
                   'York':          [( -1.080267, 53.965147 ),  30],
                   'Leeds':         [( -1.556966, 53.807884 ),  76],
                   'CEH Edinburgh': [( -3.206400, 55.861881 ),  50],
                   'Reading':       [( -0.937170, 51.439382 ),  17],
                   'Imperial':      [( -0.174531, 51.499545 ),  17],
                   'UEA':           [(  1.240803, 52.621523 ), 113]
                   }

    template = """SELECT """
    pnt_list = []
    for k in list(crewPlaces.keys()):
        for i in range( crewPlaces[k][1] ):
            pnt_list.append( str(crewPlaces[k][0][0] ) + ' '+ str(crewPlaces[k][0][1] ))
    out = open('/home/axel/sql_tmp.txt', 'w')
    out.write( ','.join( pnt_list ))
    out.close()
get_crew_centroid()




list_inst = ( ['FAAM',],
              ['Directflight', 'DFL'],
              ['MetOffice','Met Office'],
              ['Manchester', 'UMIST'],
              ['Leeds',],
              ['York',],
              ['UEA', 'Anglia',],
              ['Reading',],
              ['Cambridge',],
              ['Leicester',],
              ['CEH',],
              ['Edinburgh',],
              ['Imperial',],
              ['Hertfordshire',],
              ['Oxford',],
              ['Sussex',],
              ['Glasgow',])
#              ['Karlsruhe',],
#              ['Mainz', 'MPI'],
#              ['Aquila',],
#              ['Denver',],
#              ['DLR',],
#              ['BBC',],)
#summary = []
#for ins in list_inst:
#    cnt = counter( crews, ins )
#    summary.append( (cnt, ins[0]) )
#    summary.sort()
#    summary.reverse()





#plot_circle()
#filelist = get_filelist()
#fids = get_fids()
#crews = get_crews(filelist, fids)
#plot_circle( summary )
