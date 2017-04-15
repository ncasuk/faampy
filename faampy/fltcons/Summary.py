'''

Created on 20 Dec 2010

@author: axel
'''

import re
from faampy.fltcons.db import DB
#from faampy.utils import *


class Summary(object):

    def __init__ (self, par, filtered=True):
        self.filtered = filtered
        self.par = par
        self.Data = None
        self.Flag = None
        self.__fetchData__()
        self.__flagData__()

    def __flagData__( self ):

        self.Flag = []
        self.Flag.append(0)
        for i in range(1, len(self.Data)):
            cal0 = re.sub(r'\s', '', str( self.Data[i-1][4].split('!')[0]))
            cal1 = re.sub(r'\s', '', str( self.Data[i][4].split('!')[0]))
            if cal0 == cal1:
                self.Flag.append(self.Flag[-1])
            else:
                self.Flag.append(self.Flag[-1]+1)

    def __fetchData__(self):
        fcdb = DB()
        fcdb.connect()

        if self.filtered:
            sql = """SELECT f.par,f.fid,f.rev,f.rdate,f.line,f.fname
                    FROM ( SELECT fid, max(rev) AS maxrev
                           FROM fltcons GROUP BY fid ORDER BY fid
                         ) AS x INNER JOIN fltcons AS f ON f.fid=x.fid AND f.rev=x.maxrev AND f.par='%s'""" % (self.par)
        else:
            sql = """SELECT par,fid,rev,rdate,line FROM fltcons WHERE par='%s' ORDER BY fid,rev""" %  (self.par)
        cur = fcdb.con.cursor()
        cur.execute(sql)
        self.Data = cur.fetchall()
        cur.close()

    def __str__(self):
        ref = -9999

        out = ""
        out += 80 * "=" + "\n"
        out += " %2s | %12s | %5s | %3s | %10s | %s \n" % ('I', 'Par', 'Fid', 'rev', 'date', 'Value/Comment')
        out += 80 * "=" + "\n"
        for i in range(len(self.Data)):
            if self.Flag[i] != ref:
                out += " %02i | %12s | %5s | %3s | %10s | %s \n" % (self.Flag[i], self.Data[i][0], self.Data[i][1],self.Data[i][2],self.Data[i][3],self.Data[i][4])
                if self.filtered:
                    ref = self.Flag[i]
        out += 80 * "="
        return out


if __name__ == '__main__':
    pass
