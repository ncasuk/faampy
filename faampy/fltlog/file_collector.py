#!/usr/bin/python

"""
The purpose of the script is to ease the creation of the FAAM flight logs
that is created for each science flight. The flight logs are to be created by
the flight manager of the flight and uploaded to CEDA.

Collects as many files as possible for the specific flight by browsing through
some relevant folders on the R-drive. The files are copied to a separate folder
and indexed, so that the files are already in the correct order.

"""

import os
import re
import shutil

from collections import OrderedDict


inpaths = ['/mnt/faamarchive/Data/Flt Mgr Data_Logs/',
           '/mnt/faamarchive/Data/coreflightdata/data/',
           '/mnt/faamarchive/Data/Flt Mgr Data_Logs/asxx/',
           '~/gdrive/']

outpath = os.path.join(os.path.expanduser('~'),
                       'fltlog_output/')

search_dict = OrderedDict()

search_dict['front_page'] = (10, ['[bc]{fid} flight folder front page.*',])
search_dict['flight_summary'] = (20, ['flight-sum_faam_.*_[bc]{fid}.txt',])
#search_dict['surface_pressure_chart']=(30, ['asxx_{date_string}_0600utc.pdf', 'asxx_{date_string}_1200utc.pdf'])
search_dict['track_plot'] = (40, ['[bc]{fid}_gin_track.ps', '[bc]{fid}_track.ps'])
search_dict['sortie_brief'] = (50, ['/[bc]{fid}/[bc]{fid}.*sortie.*',])
search_dict['ms_log'] = (60, ['[bc]{fid}_ms.*', '[bc]{fid}_mis.*', 'Mis.*xls', 'Mis.*xlsx'])
search_dict['preflighter_log'] = (70, ['b{fid}_preflight_log.pdf',])
search_dict['science_defects_log'] = (80, ['[bc]{fid} science defects log.doc',])
search_dict['avaps_log'] = (90, ['[bc]{fid} faam dropsonde flight log.doc',])
search_dict['cloud_physics_log'] = (100, ['[bc]{fid}_corecloud_flightlog.txt',])
search_dict['lidar_log'] = (110, ['/[bc]{fid}/[bc]{fid}.*lidar.*.pdf',])
search_dict['chemistry_log'] = (120, ['[bc]{fid}_corechemlog*.rtf',])
search_dict['was_log'] = (130, ['[bc]{fid}.was',])
search_dict['chat_log'] = (130, ['/[bc]{fid}.*chat.*txt',])
search_dict['other'] = (140, ['/[bc]{fid}/.*pdf', '/[bc]{fid}/.*png', '/[bc]{fid}/.*jpg', '/[bc]{fid}/.*jpeg'])


class FltLog_file_list(object):

    file_list, total_file_list=[], []
    file_list_sorted=False

    def __init__(self, fid, date_string, outpath=None):
        self.fid = fid
        self.fid_int=int(fid[1:])
        self.date_string=date_string
        if not outpath:
            self.outpath=os.path.join(os.environ['HOME'], '%s_flight_log_files' % (self.fid,))
        else:
            self.outpath=os.path.join(outpath, '%s_flight_log_files' % (self.fid,))

    def get_total_file_list(self):
        result=[]
        for path in inpaths:
            for root, subFolders, files in os.walk(path):
                for f in files:
                    result.append(os.path.join(root, f))
        self.total_file_list=result

    def match(self):
        result=[]
        fid = self.fid
        date_string=self.date_string
        for k in search_dict.keys():
            item=search_dict[k]
            for pattern in item[1]:
                #print(k, pattern)
                for f in self.total_file_list:
                    if 'fid' in pattern:
                        pat=pattern.format(fid=fid[1:])
                    elif 'date_string' in pattern:
                        pat=pattern.format(date_string=date_string)
                    else:
                        pat=pattern
                    if (re.findall(pat, os.path.basename(f).lower())) or (re.findall(pat, f.lower())):
                        result.append((k, f))
                        self.total_file_list.remove(f)
        self.file_list=result

    def sort(self):
        # sort key
        skey=lambda x: os.path.basename(x[1])
        l1=[i for i in self.file_list if i[0] != 'other']
        l2=[i for i in self.file_list if i[0] == 'other']
        l2.sort(key=skey)
        self.file_list=l1+l2
        self.file_list_sorted=True


    def get(self):
        return self.file_list

    def index(self):
        c=0
        k=''
        r2=[]
        for r in self.file_list:
            if r[0] != k:
                k=r[0]
                c=0
            index=search_dict[r[0]][0]+c
            r2.append((r[0],
                       r[1],
                       os.path.join(self.outpath,
                                    '%0.3i_%s' % (index, os.path.basename(r[1])))))
            c+=1
        self.file_list=r2

    def remove_duplicates(self):
        #http://stackoverflow.com/questions/497426/deleting-multiple-elements-from-a-list
        indices=[] # indices of element that should be removed
        for i in range(1, len(self.file_list)):
            if os.path.basename(self.file_list[i][1]) == os.path.basename(self.file_list[i-1][1]):
                indices.append(i)
        self.file_list=[i for j, i in enumerate(self.file_list) if j not in indices]

    def copy(self):
        if not os.path.exists(self.outpath):
            os.mkdir(self.outpath)
        for _none, src, dst in self.file_list:
            shutil.copy2(src, dst)

    def process(self):
        self.get_total_file_list()
        self.match()
        self.sort()
        self.remove_duplicates()
        self.index()
        self.copy()

    def __str__(self):
        """prints out a short summary of the collected files
        """
        result='%s - %s File Collection\n===============================\n' % (self.fid, self.date_string)
        if self.file_list:
            for i in self.file_list:
               result+='  %s\n' % os.path.basename(i[1])
        else:
            result+='No files found.\n'
        result+='\n'
        return result


def process(fid, date_string, outpath=None):
    flog_list = FltLog_file_list(fid, date_string, outpath=outpath)
    flog_list.process()
    print(flog_list)
    return flog_list


if __name__ == '__main__':
    import argparse
    from argparse import RawTextHelpFormatter
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('fid', action="store", type=str,
                        help='FLight ID; format `[b,c]NNN`')
    parser.add_argument('--date_string', action="store", type=str,
                        help='Date string; format "YYYYMMDD" ')

    args = parser.parse_args()
    if not re.match('[b,c]\d{3}', args.fid):
        import yaml
        current_path = os.path.dirname(os.path.realpath(__file__))
        yaml_file = os.path.join(current_path,'fltlog.yaml')
        campaign_list = yaml.load(open(yaml_file, 'r'), Loader=yaml.Loader)
        for campaign in campaign_list:
            if campaign.keys()[0] == args.fid:
                print(campaign.keys()[0])
                for entry in campaign.values()[0]:
                     fids = [i.keys()[0] for i in campaign.values()[0]]
                     date_strings = [str(i.values()[0]) for i in campaign.values()[0]]

    else:
        fids = [args.fid, ]
        date_strings = [args.date_string,]

    args = parser.parse_args()
    for fid, date_string in zip(fids, date_strings):
        process(fid, date_string)
