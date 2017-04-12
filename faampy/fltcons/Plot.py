'''
Created on 13 Jan 2010

@author: axel
'''

import sys

import matplotlib
import matplotlib.pyplot as plt
import os
import re
import scipy

import faampy
import faampy.utils

#from orderedset import OrderedSet
from faampy.fltcons.db import DB


import collections

# http://code.activestate.com/recipes/576694-orderedset/
class OrderedSet(collections.MutableSet):

    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)


def fid_as_integer(fid):
    if fid[0].lower() == 'c':
        offset = 1000
    else:
        offset = 0
    return int(fid[1:]) + offset


class Plot(object):

    def __init__ (self, par):
        self.par = par
        self.outpath = None
        self.Figure = None

    def get_data(self):
        """gets the data for the plot"""
        fcdb = DB()
        fcdb.connect()
        sql = """SELECT f.par,f.fid,f.rev,f.rdate,f.line,f.fname
                    FROM ( SELECT fid, max(rev) AS maxrev
                           FROM fltcons GROUP BY fid ORDER BY fid
                         ) AS x INNER JOIN fltcons AS f ON f.fid=x.fid AND f.rev=x.maxrev AND f.par='%s' ORDER BY x.fid""" % (self.par)

        cur = fcdb.con.cursor()
        cur.execute(sql)
        data = cur.fetchall()
        cur.close()
        par, fid, rev, rdate, cal, fname = zip(*data)
        newcal = []
        for c in cal:
            c = c.split(' ', 1)[1]
            c = c.split('!')[0]
            c = c.strip()
            newcal.append(c)
        cal = newcal
        allBarData = []
        for c in OrderedSet(cal):
            curBarData, beg, end = ([], None, None)
            for i in range(len(fid)):
                if c == cal[i]:
                    if not beg and not end:
                        #beg = int(fid[i])
                        #end = int(fid[i])
                        beg = fid_as_integer(fid[i])
                        end = fid_as_integer(fid[i])
                    else:
                        end = fid_as_integer(fid[i])
                    if i == len(fid) - 1:
                        end = fid_as_integer(fid[i])
                        curBarData.append((beg, end-beg))
                else:
                    if (beg and end):
                        curBarData.append((beg, end-beg))
                        beg = None
                        end = None
                    else:
                        pass

            allBarData.append(curBarData)
        self.allBarData = allBarData
        print(curBarData)
        pltData = []
        for i in range(len( allBarData)):
            for n in allBarData[i]:
                pltData.append((float(n[0])-0.5, n[1]))
        self.pltData = pltData
        return pltData

    def create(self):
        allBarData = self.allBarData
        pltData = self.pltData
        fig = plt.figure(figsize=(8, 2))
        ax = fig.add_subplot(111)
        ax.grid(True)
        xsize, ysize = (8, 3.5)   # x-size for all plots
        fcol = ['#a6cee3',
                '#1f78b4',
                '#b2df8a',
                '#33a02c',
                '#fb9a99',
                '#e31a1c',
                '#fdbf6f',
                '#ff7f00',
                '#cab2d6',
                '#6a3d9a',
                '#ffff99',
                '#b15928']*12
        ypos = 2
        for i in range(1):
            xpltData = []
            for pair in pltData:
                xpltData.append((pair[0], pair[1]+1))
            ax.broken_barh(xpltData, (1, 8), facecolors=fcol[0:len(pltData)])
            ax.set_ylim(0, 10)
            ax.set_yticks([5])
            ax.set_yticklabels([' '])
            ax.set_ylabel(self.par)
            fig.canvas.draw()
            xlabels = [item.get_text() for item in ax.get_xticklabels()]
            for i, l in enumerate(xlabels):
                if not l:
                    continue
                if int(l) < 1000:
                    xlabels[i] = 'b%0.3i' % int(l)
                else:
                    xlabels[i] = 'c%0.3i' % (int(l)-999)
            ax.set_xticklabels(xlabels)
        fig.savefig(os.path.join(faampy.fltcons.FIGURES_PATH, str.strip(self.par) + '.png'))
        self.Figure = fig
