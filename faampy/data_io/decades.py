import csv
import numpy as np
import os

def read_tcp_defin(deffile):
    defin=csv.reader(open(deffile,'rb'),delimiter=',')
    conv={'text': 'S'}
    for en in list({'':'>','>':'>','<':'<'}.items()):
        for ty in list({'unsigned_int': 'u',
                        'int': 'i',
                        'signed_int': 'i',
                        'double': 'f',
                        'single_float': 'f',
                        'float': 'f',
                        'single': 'f',
                        'double_float': 'f',
                        'boolean': 'u',
                        'f':'f',
                        'i': 'i',
                        'u': 'u'}.items()):
            conv[en[0]+ty[0]]=en[1]+ty[1]
    label=''
    outputs=[]
    dt=[]
    total=0
    try:
        for row in defin:
            if(row):
                if row[0]!='field' :
                    total+=int(row[1])
                    if(label==''):
                        full_descriptor=row[0]
                        label=full_descriptor[1:-2]
                        dt.append(('label','S'+row[1]))
                    else:
                        f=int(row[1])/int(row[2])
                        para=label+'_'+row[0]
                        if(f>1):
                            dt.append((para,conv[row[3]]+row[2],(f,)))
                        else:
                            dt.append((para,conv[row[3]]+row[2]))
#                        if(row[0]=='packet_length'):
#                            self.pack_len=np.dtype(dt[-1][1])
    except Exception as e:
        return
    return (label, dt)


def read_udp_defin(deffile):
    defin=csv.reader(open(deffile,'rb'),delimiter=',')
    conv={'text': 'S'}
    for en in list({'':'>','>':'>','<':'<'}.items()):
        for ty in list({'unsigned_int': 'i',
                        'int': 'i8',
                        'signed_int': 'i8',
                        'double': 'f8',
                        'single_float': 'f8',
                        'float': 'f8',
                        'single': 'f8',
                        'double_float': 'f8',
                        'boolean': 'u',
                        'f':'f8',
                        'i': 'i8',
                        'u': 'u'}.items()):
            conv[en[0]+ty[0]]=en[1]+ty[1]
    label=''
    outputs=[]
    dt=[]
    total=0
    #try:
    if 1:
        for row in defin:
            if(row):
                if row[0]!='field' :
                    #total+=int(row[1])
                    if(label==''):
                        full_descriptor=row[0]
                        label=full_descriptor[1:-2]
                        dt.append(('label', 'S'+row[2]))
                    else:
                        para=label+'_'+row[0]
                        if row[1].lower().strip() == 'text':
                            dt.append((para, 'S'+row[2]))
                        else:
                            dt.append((para, conv[row[1]]))
    #except Exception, e:
    #    return
    return (label, dt)


def read_tcp(ifilelist, deffile):
    """
    :param ifilelist: tcp data file as stored by the decades system
    :param def_file: definition file
    """
    if isinstance(ifilelist, str):
        ifilelist = [ifilelist,]
    ifilelist.sort(key=lambda x: os.path.basename(x))

    label, dt = read_tcp_defin(deffile)
    d_lst = []
    for ifile in ifilelist:
        d_lst.append(np.fromfile(ifile, dtype=dt))
    d = np.concatenate(d_lst)
    return d
    #df = pd.Dataframe()


def read_udp(ifilelist, deffile):
    if isinstance(ifilelist, str):
        ifilelist = [ifilelist,]
    ifilelist.sort(key=lambda x: os.path.basename(x))

    label, _dt = read_udp_defin(deffile)
    names, dt = zip(*_dt)
    dt = list(dt)
    print(dt)
    d_lst = []
    for ifile in ifilelist:
        d_lst.append(np.genfromtxt(ifile,
                                   skip_header=20,
                                   skip_footer=20,
                                   delimiter=',',
                                   names=names,
                                   dtype=','.join(dt)))
    d = np.concatenate(d_lst)
    return d


def write(data, deffile, outfilename):
    data.tofile(outfilename, deffile)


#tcp_def = '/home/axel/gdrive/ncas/projects/pod_updates_validate/so2_upgrade/c060-oct-04/CORCON01_TCP_v7.csv'
#udp_def = '/home/axel/gdrive/ncas/projects/pod_updates_validate/so2_upgrade/c060-oct-04/CHTSOO01_v4.csv'
#udp_ifile= '/home/axel/decades_test/TEiSO2-43i_20171004_064434_C060.txt'
#dat = read_udp(udp_ifile, udp_def)

#label, dt = read_udp_defin(udp_def)
#dat = read_udp(udp_ifile, udp_def)

#ofilename = '/home/axel/gdrive/ncas/projects/pod_updates_validate/so2_upgrade/c060-oct-04/tmp/CHTSOO01_20171004_064434_C060'
#ofilename = '/home/axel/gdrive/ncas/projects/pod_updates_validate/so2_upgrade/c060-oct-04/tmp/CHTSOO01_20171004_064434_REDESIGN'
#write(dat, tcp_def, ofilename)
