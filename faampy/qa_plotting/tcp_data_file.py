from datetime import datetime
import struct
import numpy as np
import os
import sys
import tempfile
import zipfile

from collections import OrderedDict

class TCPDataChecker(object):
    def __init__(self, ifile):
        f=open(ifile, 'r')
        b=f.read()
        f.close()

        dlu_identifier = '$' + os.path.basename(ifile).split('_')[0]
        lines = [dlu_identifier+i for i in b.split(dlu_identifier)][1:]

        timestamp = [struct.unpack('>9s i I', line[0:17])[2] for line in lines]
        ptp_sync = []
        for line in lines:
            if len(line) >= 17:
                try:
                    ptp_sync.append(int(struct.unpack('s', line[17])[0]))
                except:
                    ptp_sync.append(0)

        packet_length = [len(line) for line in lines]

        n = len(timestamp)
        if n > 0:
            duration = (max(timestamp) - min(timestamp))+1
        else:
            self.summary=OrderedDict()
            self.summary['file_name']=os.path.basename(ifile)
            self.summary['duration'] = 0
            return

        #http://stackoverflow.com/questions/10741346/numpy-most-efficient-frequency-counts-for-unique-values-in-an-array
        y=np.bincount(packet_length)
        ii=np.nonzero(y)[0]
        perc=[float(y[i])/n*100. for i in ii]
        packet_length_occ=zip(ii, perc)
        #print(packet_length_occ)

        self.summary=OrderedDict()
        self.summary['file_name']=os.path.basename(ifile)
        # we need to
        self.summary['data_start']=datetime.utcfromtimestamp(min(timestamp)).strftime('%H:%M:%S %Y-%m-%d')
        self.summary['data_end']=datetime.utcfromtimestamp(max(timestamp)).strftime('%H:%M:%S %Y-%m-%d')
        self.summary['duration']=duration
        self.summary['n_data_packets']=n
        self.summary['n_unique_timestamps']=len(set(timestamp))
        self.summary['n_ptp_synced']=np.sum(ptp_sync)
        self.summary['completeness']=(float(n)/float(duration) * 100.0)
        #self.summary['packet_size']=float(np.where(np.array(packet_length) != defined_packet_length)[0].size)/len(timestamp)*100.0
        self.summary['packet_size']=packet_length_occ

    def get_summary(self):
        return self.summary

    def __str__(self):
        result=''
        result+='\nSummary:\n'
        result+='   File name         : %s\n' % self.summary['file_name']

        if self.summary['duration'] == 0:
            result += '    File contains no valid data.\n'
            return result
        result+='   Data Start        : %s\n' % self.summary['data_start']
        result+='   Data End          : %s\n' % self.summary['data_end']
        result+='   Duration          : %i secs\n' % self.summary['duration']
        result+='   Data packets      : %i\n' % self.summary['n_data_packets']
        result+='   Unique Timestamps : %i \n' % self.summary['n_unique_timestamps']
        result+='   PTP synced        : %i (%.1f %%)\n' % (self.summary['n_ptp_synced'],
                                                          ((float(self.summary['n_ptp_synced'])/float(self.summary['duration']))*100.))
        result+='   Completeness      : %.1f percent\n' % self.summary['completeness']
#        result+='   Packet size       : %.1f percent\n' % self.summary['percentage_wrong_packet_size']
        return result


def tcp_file_checker(core_rawdlu_file):
    tmpdir=tempfile.mkdtemp()
    #print(tmpdir)
    zip_ref=zipfile.ZipFile(core_rawdlu_file, 'r')
    zip_ref.extractall(tmpdir)
    zip_ref.close()
    file_list=[os.path.join(tmpdir, f) for f in os.listdir(tmpdir)]
    file_list.sort()
    file_list2=[]
    for f in file_list:
        if not os.path.splitext(f)[1] in ['.csv', '.bin']:
            file_list2.append(f)
    file_list=file_list2
    file_summaries=[]
    for f in file_list:
        check=TCPDataChecker(f)
        file_summaries.append(check.get_summary())
    table=[]
    for s in file_summaries:
        table.append([i[1] for i in s.items()])
    return table

#table=tcp_file_checker('/home/axel/gdrive/ncas/core_processing/2017/c027-aug-03/core_faam_20170803_r0_c027_rawdlu.zip')

#core_rawdlu_file='./data/core_faam_20160317_r0_b952_rawdlu.zip'
#core_rawdlu_file='/home/axel/Dropbox/campaigns/spring2016/b955-may-06/core_faam_20160506_r0_b955_rawdlu.zip'
#file_summaries_table=tcp_file_checker(core_rawdlu_file)
