'''
Created on 29 Jul 2014

@author: axel
'''

import datetime
import re
import os

file_list=[]
root_dir='/home/data/faam/badc'

root_dir='/mnt/faamarchive/badcMirror'

for root, subfolders, files in os.walk(root_dir):
    for f in files:
        if f.endswith('00README'):
            file_list.append(os.path.join(root, f))

def extract_info(f):
    txt=open(f, 'r').readlines()
    tmp=['',]*6
    for line in txt:
        #get fid
        line=line.lower()
        if 'cranfield' in line:
            tmp[5]='Cranfield'
        if re.findall('b\d{3}', f):
            fid=re.findall('b\d{3}', f)[0]
        if fid and not tmp[0]:
            tmp[0]=fid        
        if 'pre' in line:
            power=re.findall('\d{4}z', line)[0]
            if not tmp[1]:
                tmp[1]=power
        if 'brief' in line:
            brief=re.findall('\d{4}z', line)[0]
            if not tmp[2]:
                tmp[2]=brief
        if 'take' in line:
            take=re.findall('\d{4}z', line)[0]
            if not tmp[3]:
                tmp[3]=take
        if tmp[3] and tmp[2]:
            tmp[4]=str(datetime.datetime.strptime(tmp[3], '%H%Mz')-datetime.datetime.strptime(tmp[2], '%H%Mz'))
    return tmp
    
    

file_list.sort()
file_list.reverse()


#test=extract_info(file_list[30])

result=[]
for f in file_list:    
    try:
        result.append(extract_info(f))
    except:
        pass
for r in result:
    if r[1]+r[2]+r[3]:
        print(','.join(r))
    

    