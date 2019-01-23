import time
import os
import shutil
import time
import datetime
import sys
from subprocess import call
import tempfile
import argparse
import xml.etree.ElementTree
import sqlite3

#from stream_tee import *


#try:
import plotly
from plotly.graph_objs import Scatter, Layout
#except: print('You need to install plotly to produce responsive plots.')

def get_arg():
    try: parser = argparse.ArgumentParser()
    except: print("Some error happened with arguments")

    parser.add_argument("-sn","--sernum", help="NAR serial number to process")
    parser.add_argument("-a","--auto", action="store_true", default=False, help="Proceed all steps from the begining without asking questions.Default is False. ")

    try:
        a=parser.parse_args()
    except:
        print("\nNo arguments. You need to specify something. Use -h option for help.")
        input("Press ENTER")
        exit()

    if a.sernum!=None:
        print('Processing NAR files for SN:',a.sernum)
    else:
        print('No SN specified. You may use -sn option, or allow narvision to detect SN automatically in current directory.')

    return a


def save_graph(name):
    ftmp_h=open('temp-plot.html')
    name=name.replace('/','p')
    name=name.replace('second','s')
    name=name.replace('%','ratio')
    shutil.copy('temp-plot.html',plots_dir+name)
    return


def prcntl(l,p):
    i=len(l)
    if i==0: return 0
    if i==1: return l[0]
    m=sorted(l)
    j=int(round(p/100*(i-1),0))
#    if j=i: j-=1
#    print('percentile',j,i)
    return round(m[j],2)


def avg(l,i):
    if len(l)==0: return 0
    a=round(sum(l)/len(l),i)
    return a


def prod(l,m):
    n=list()
    for i in range(len(l)):
        n[i]=l[i]*m[i]
    return n


def sumprod(l,m):
    s=sum(prod(l,m))
    return s


def printw(s,t):
    print(s)
    time.sleep(t)
    return

def printi(s,msg):
    print(s)
    input('Printed:'+msg)
    return

def plotmany(x,many,plot_title):
# (x1,y1,label1, y2,label2, y3, label3,plot_title):
#n=len(many)
#many: [(y0),(y1),(y2)..(yn)]
#yn: [('label',labeln) ,('values',y_list))]
    title_long=''

    if len(many)<5:
        for y in many:
            #printi(many,'many')
            #printi(y,'y')
            title_long=title_long+'<BR>'+y['label']+'| 95-percentile='+str(prcntl(y['values'],95))
            title_long=title_long+' | Average='+str(avg(y['values'],1))

    title_long='<b>'+plot_title+'</b>'+title_long

    trace=list()
    for i in range(len(many)):
        trace.append(Scatter(name=many[i]['label'], x=x,y=many[i]['values']) )

    printw('Now building graphical representation of '+plot_title,0.1)
    printw('Results file will be saved to '+plot_title+'.html',0.1)
    try:
        plotly.offline.plot({
                "data": trace,
                "layout": Layout(title=title_long)})
    except:
        print("Plotting error. Please check if plotly installed on your computer. You may try to plot your CSV files with MS Excel.")
    try: save_graph(plot_title+'.html')
    except: printi('Failed autosaving graph to'+plot_title+'. You may try to copy it yourself. Press any key when done.','')

    return

def plot_csv(filename,directory):
#many: [(y0),(y1),(y2)..(yn)]
#yn: [('label',labeln) ,('values',y_list))]

    x=list()
    many=list()
    yn=dict()

    f=open(directory+filename)
    data=f.read()
    data=data.splitlines()
    if len(data)<2:
        print(filename,'has no data.')
        return
    header=data[0]
    labels=data[0].split(',')[2:]
    y=[list() for i in range(len(labels))]

    for line in data[1:]:
        words=line.split(',')
        x.append(words[1])
        for i in range(len(labels)):
            try: y[i].append(float(words[2+i]))
            except:y[i].append(0)

    for i in range(len(labels)):
        many.append(dict([('label',labels[i]),('values',y[i])]))
    plot_title=filename.split('.')[0]
    plotmany(x,many,plot_title)
    return



def clean_temp(path):
        print("Cleaning",tempfile.gettempdir(),"from previous runs. ",end='')
        sys.stdout.flush()
        for file in os.listdir(tempfile.gettempdir()):
            if file.startswith('nar') or file.startswith('output2merge') :
                full_path=os.path.join(tempfile.gettempdir(), file)
                try: os.remove(full_path)
                except:pass
        print('Done.')

        return

def nar_merger(nar1,nar2,nar_out):
    """
    naviseccli analyzer -archivemerge -data nar1 merged.nar -out merged2.nar -overwrite y
    del merged nar
    rename merged2.nar merged.nar
    """
#    print("NaviSECCli.exe"," analyzer -archivemerge -data "+nar1+" "+nar2+" -out "+nar_out+" -overwrite y")
    call(["cmd.exe","/c NaviSECCli.exe analyzer -archivemerge -data "+nar1+" "+nar2+" -out "+nar_out+" -overwrite y"])

    return

def get_config(SN):
        print("Extracting configuration data.")
        sys.stdout.flush()
        file_big="merged_"+SN+".nar"
        for file in os.listdir("."):
            if file.startswith(SN) and file.endswith('.nar') :
                commands= [
                "NaviSECCli.exe analyzer -archivedump -stats  "+file_big+"  -out "+SN+"_insights.txt -overwrite y",
                "NaviSECCli.exe analyzer -archivedump -config "+file+"  -xml -out config.xml -overwrite y",
                "NaviSECCli.exe analyzer -archivedump -rel    "+file+"  -xml -out config_L5.xml -level 5 -overwrite y"
                ]
                for command in commands:
                    try: call(["cmd.exe","/c"+command])
                    except: pass
                    time.sleep(1)
                break
        print('Done.')

        return

def get_all_merged(SN):
    """
    naviseccli analyzer -archivemerge -data nar1 merged.nar -out merged2.nar -overwrite y
    del merged nar
    rename merged2.nar merged.nar
    """
    try: os.remove('merged_'+SN+'.nar')
    except: pass

    file_list=list()
    for file in os.listdir("."):
        if file.startswith(SN) and file.endswith('.nar'):
#            nars+=','+file
            file_list.append(os.path.join("./", file))

    for f in file_list:
        print(f,'was found.')

    if len(file_list)==1:
        print('[ 100% ]: Only 1 file found. No merging required.')
        shutil.copy(file_list[0],"merged_"+SN+".nar")
        return

        print(len(file_list),'NAR files will be merged now.')

    print("[  0% ]:","Merging",file_list[0],"and",file_list[1],end='.')

    sys.stdout.flush()
    nar_merger(file_list[0],file_list[1],"old_merged.nar")

    for i in range(2,len(file_list)):
#        clean_temp(tempfile.gettempdir())
        progress=str(int(i*100/len(file_list)))+"%"
        if len(progress)<3:progress='0'+progress
        print("[",progress,"]: Adding",file_list[i],end='.')
        sys.stdout.flush()
        nar_merger("old_merged.nar",file_list[i],"new_merged.nar")
        os.remove("old_merged.nar")
        os.rename("new_merged.nar","old_merged.nar")

    os.rename("old_merged.nar","merged_"+SN+".nar")
    print("[100% ]: Finished merging",len(file_list),"NAR files for array S/N",SN)
    return

def dump_from_nar(nar,directory):
    commands= [
#    "NaviSECCli.exe analyzer -archivedump -stats  "+nar+" -out stats.txt -overwrite y",
#    "NaviSECCli.exe analyzer -archivedump -config "+nar+" -xml -out config.xml -overwrite y",
#    "NaviSECCli.exe analyzer -archivedump -rel    "+nar+" -xml -out pools.xml -level 2 -overwrite y",
#    "NaviSECCli.exe analyzer -archivedump -rel    "+nar+" -xml -out luns.xml -level 3 -overwrite y",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out disk_util.csv      -overwrite y -header y -delim cm -eol cr -object d -format on pt u",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out sp_util.csv        -overwrite y -header y -delim cm -eol cr -object s -format on pt u",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out sp_dirty.csv       -overwrite y -header y -delim cm -eol cr -object s -format on pt dp",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out sp_fcdirty.csv     -overwrite y -header y -delim cm -eol cr -object s -format on pt fcdp",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out sp_queues.csv      -overwrite y -header y -delim cm -eol cr -object s -format on pt abql ql",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out sp_response.csv    -overwrite y -header y -delim cm -eol cr -object s -format on pt rt",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out sp_bandwidth.csv   -overwrite y -header y -delim cm -eol cr -object s -format on pt tb rb wb",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out sp_throughput.csv  -overwrite y -header y -delim cm -eol cr -object s -format on pt tt rio wio",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out sp_blocksizes.csv  -overwrite y -header y -delim cm -eol cr -object s -format on pt ws rs",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out port_bandwidth.csv -overwrite y -header y -delim cm -eol cr -object p -format on pt tb rb wb",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out port_queuefull.csv -overwrite y -header y -delim cm -eol cr -object p -format on pt qfc",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out pool_fcachehr.csv  -overwrite y -header y -delim cm -eol cr -object pool -format on pt fcrhr fcwhr",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out pool_fcacheio.csv  -overwrite y -header y -delim cm -eol cr -object pool -format on pt fcrh fcrm fcwh fcwm",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out luns_queues.csv    -overwrite y -header y -delim cm -eol cr -object hl -format on pt abql",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out luns_response.csv  -overwrite y -header y -delim cm -eol cr -object hl -format on pt rt",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out luns_iops_tot.csv  -overwrite y -header y -delim cm -eol cr -object hl -format on pt tt",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out luns_iops_trw.csv  -overwrite y -header y -delim cm -eol cr -object hl -format on pt rio wio",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out disk_queues.csv    -overwrite y -header y -delim cm -eol cr -object d -format on pt abql",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out disk_response.csv  -overwrite y -header y -delim cm -eol cr -object d -format on pt rt",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out disk_iops.csv      -overwrite y -header y -delim cm -eol cr -object d -format on pt tt",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out disk_blocksizes.csv -overwrite y -header y -delim cm -eol cr -object d -format on pt ws rs",
    "NaviSECCli.exe analyzer -archivedump -data   "+nar+" -out disk_mbps.csv      -overwrite y -header y -delim cm -eol cr -object d -format on pt tb"

    ]

    names=[
    "sp_util.csv",
    "sp_dirty.csv",
    "sp_fcdirty.csv",
    "sp_response.csv",
    "disk_blocksizes.csv",
    "sp_blocksizes.csv",
    "pool_fcachehr.csv",

    "port_queuefull.csv",
    "sp_throughput.csv",
    "port_bandwidth.csv",
    "sp_queues.csv",
    "sp_bandwidth.csv",
    "pool_fcacheio.csv",

    "luns_queues.csv",
    "luns_iops_tot.csv",
    "disk_util.csv",
    "disk_queues.csv",
    "disk_iops.csv",
    "disk_mbps.csv",
    "luns_response.csv",
    "disk_response.csv",
    "luns_iops_trw.csv"
     ]
    i=0


    print("Extracting  statistics from NAR file.")
    for command in commands:
        progress=str(int(i*100/len(commands)))+"%"
        if len(progress)<3:progress='0'+progress
        i+=1
        print("[",progress,"]: ",end='')
        sys.stdout.flush()
        try: call(["cmd.exe","/c"+command])
        except:
            print('This stat type could not be extracted. Proceeding with other ones.')
        time.sleep(2)
            #        print()
    print("[100% ]: Done.")

    for file in os.listdir(directory):
        if file.endswith('.csv'):
            full_path=os.path.join(directory, file)
            try: os.remove(full_path)
            except:pass

    for n in names:
        os.rename(n,directory+n)

    return

def normalize_csv(filename,directory):
    f=open(directory+filename,'r')
    time=list()
    values=dict()
    count=dict()
    objects=list()
    new_header=['All Objects','Poll Time']
    #print(len(f))
    k=0
    data=f.read()
    data=data.splitlines()
    headers=data[0].split(',')
#    print(headers)
    file_output='norm_'+filename
    fo=open(directory+file_output,'w')

    for line in data[1:]:
        words=line.split(',')
        o=words[0].split('[')
        if not o[0] in objects:
            objects.append(o[0])
        if not words[1] in time:
            time.append(words[1])
            values[time[-1]]=list()
            for i in range(len(words[2:])):
                if words[2+i]!='':
                    values[time[-1]].append(round(float(words[2+i]),2))
                else:
                    values[time[-1]].append('')
                h=objects[-1]+'['+headers[2+i]+']'
                if not h in new_header: new_header.append(h)
#                print(new_header)
                #print(objects[-1], headers[2+i])
        else:
            i_time=time.index(words[1])
            for i in range(len(words[2:])):
                if words[2+i]!='':
                    values[time[i_time]].append(round(float(words[2+i]),2))
                else:
                    values[time[i_time]].append('')
                #print(objects[-1], headers[2+i])
                h=objects[-1]+'['+headers[2+i]+']'
                if not h in new_header: new_header.append(h)
#                print(new_header)

#    print(new_header)
    for h in new_header[:-1]:
        fo.write(h+',')
    fo.write(new_header[-1])
    fo.write('\n')

    for t in time:
        fo.write('All,'+t)
#        print(values[t])
        for v in values[t]:
            fo.write(',')
            fo.write(str(v))
        fo.write('\n')
    fo.close()

    if ('sp_' in filename) or ('pool_' in filename):
        plot_csv(file_output,directory)

    return

def merge_csv(filename,directory,mode):

    f=open(directory+filename,'r')
    time=list()
    values=dict()
    count=dict()
    #print(len(f))
    k=0
    data=f.read()
    data=data.splitlines()
    file_output='sys_'+filename
    fo=open(directory+file_output,'w')
    fo.write(data[0]+'\n')

    for line in data[1:]:
        words=line.split(',')
        if not words[1] in time:
            time.append(words[1])
            values[time[-1]]=list()
            for w in words[2:]:
                if w!='':
                    values[time[-1]].append(round(float(w),2))
                else:
                    values[time[-1]].append('')
                count[time[-1]]=1
#            print(time[-1],values[time[-1]],count[time[-1]])

        else:
            i_time=time.index(words[1])
            for i in range(len(words[2:])):
                if words[2+i]!='':
                    values[time[i_time]][i]+=round(float(words[2+i]),2)
                else:
                    values[time[-1]].append('')
            count[time[i_time]]+=1

    if mode=='avg':
        for i in range(len(time)):
            for j in range(len(values[time[i]])):
                if values[time[i]][j]!='':
                    values[time[i]][j]=round((values[time[i]][j]/count[time[i]]),2)

    for t in time:
        fo.write('Cumulative,'+t)
        for v in values[t]:
            fo.write(',')
            fo.write(str(v))
        fo.write('\n')
    fo.close()
    plot_csv(file_output,directory)
    return

def analyzer(filename,directory):
        f=open(directory+filename,'r')
        time=list()
        data=f.read()
        data=data.splitlines()
        headers=data[0].split(',')[2:]
        columns_qty=len(headers)
#        if filename=='norm_luns_queues.csv':
#            for header in headers: print(header)
#            print('!!!!')
        values=[list() for i in range(columns_qty+1)]
        print()
        errors=0
        for line in data[1:]:
            words=line.split(',')
#            for i in range(len(words[2:])): # НУЖНО ПОНЯТЬ ПОЧЕМУ МОЖЕТ БЫТЬ МЕНЬШЕ ЗАГОЛОВКОВ, ЧЕМ СЛОВ!!!!
            for i in range(len(headers)):
 #              print(len(words),len(headers),i, end=' ')
 #              print(headers[i], end=' ')
 #              try: print(words)#[2+i])
 #              except: print(words)
               try: values[i].append(round(float(words[2+i]),2))
               except: errors+=1

#               if filename=='norm_luns_queues.csv':  # проверка для отладки
        if errors>0:
            print('Warning!',errors,'exceptions occured in Analyzer module when working with',filename)
            print('The reason may be configuration change during performance data collection period.')
 #           print('dump_'+filename,'may contain invalid data.')
 #           print('skew_'+filename,'may contain invalid data.')

            average=list()
        p98=list()
        maximum=dict()
        average=dict()
        percentile=dict()

        for i in range(columns_qty):
            maximum[headers[i]]=prcntl(values[i],99.9)
            average[headers[i]]=avg(values[i],2)
            percentile[headers[i]]=prcntl(values[i],95)

        fdump=open(directory+'dump_'+filename,'w')
        fdump.write('Object[Counter],  Maximum, Percentile-95, Average\n')

        for i in range(columns_qty):
            fdump.write(headers[i]+','+str(maximum[headers[i]])+','+str(percentile[headers[i]])+','+str(average[headers[i]])+'\n')
        fdump.close()

        aaa=sorted(average.items(),    key=lambda item: (-item[1], item[0]))
        mmm=sorted(maximum.items(),    key=lambda item: (-item[1], item[0]))
        ppp=sorted(percentile.items(), key=lambda item: (-item[1], item[0]))

        fo=open(directory+'skew_'+filename,'w')
        fo.write('Index, Object, Maximum, Percentile-95, Average\n')

        for i in range(len(ppp)):
            j=0
            k=0
            for a in aaa:
                if a[0]==ppp[i][0]:
#                    print('avg',aaa[j][0],aaa[j][1])
                    break
                else: j+=1

            for m in mmm:
                if m[0]==ppp[i][0]:
#                    print('pcnt',ppp[k][0],ppp[k][1])
                    break
                else: k+=1
            fo.write(str(i)+','+str(ppp[i][0])+','+str(mmm[k][1])+','+str(ppp[i][1])+','+str(aaa[j][1])+'\n')

        fo.close()
        plot_csv('skew_'+filename,directory)
#            input()



        return
"""
        d = {"aa": 3, "bb": 4, "cc": 2, "dd": 1}
        s = [(k, d[k]) for k in sorted(d, key=d.get, reverse=True)]
        >>> for k, v in s:
        ...     k, v
        А теперь по значениям по убыванию и ключам.
        sorted(my_dict.items(), key=lambda item: (-item[1], item[0]))
        [('0', 3), ('a', 3), ('b', 2), ('c', 1)]
"""


def process_csv(directory):
        names=[
        "sp_util.csv",
        "sp_dirty.csv",
        "sp_fcdirty.csv",
        "sp_response.csv",
        "disk_blocksizes.csv",
        "sp_blocksizes.csv",
        "pool_fcachehr.csv",

        "sp_throughput.csv",
        "sp_queues.csv",
        "sp_bandwidth.csv",
        "port_queuefull.csv",
        "port_bandwidth.csv",
        "pool_fcacheio.csv",
        "luns_iops_tot.csv",
        "luns_iops_trw.csv",
        "luns_queues.csv",
        "disk_util.csv",
        "disk_mbps.csv",
        "disk_queues.csv",
        "disk_iops.csv",

        "disk_response.csv",
        "luns_response.csv"
         ]

        print('Processing CSV data.')
        for n in names[:7]:
            print('Merging',n,end='. ')
            sys.stdout.flush()
            merge_csv(n,directory,'avg')
            print('Done.')

        for n in names[7:19]:
            print('Merging',n,end='. ')
            sys.stdout.flush()
            merge_csv(n,directory,'summ')
            print('Done.')

        for n in names:
            print('Normalizing',n,end='. ')
            sys.stdout.flush()
            normalize_csv(n,directory)
            print('Done.')

#        for n in names[-6:]:
#            print('Analyzing',n,end='. ')
#            sys.stdout.flush()
#            analyze_csv('norm_'+n,directory)
#            print('Done.')

        return

def analyze_csv(directory):
    names=[
        "disk_util.csv",
        "disk_mbps.csv",
        "disk_queues.csv",
        "disk_iops.csv",
        "luns_queues.csv",
        "luns_iops_tot.csv",
        "luns_iops_trw.csv",
        "luns_response.csv",
        "disk_response.csv"
         ]

    for n in names:
        print('Analyzing',n,end='. ')
        sys.stdout.flush()
        analyzer('norm_'+n,directory)
        print('Done.')


    return

#def get_config():
#        print("Extracting configuration data.")
#        for file in os.listdir("."):
#            if file.startswith('CK') and file.endswith('.nar') :
#                commands= [
#                "NaviSECCli.exe analyzer -archivedump -stats  "+file,
#                "NaviSECCli.exe analyzer -archivedump -stats  "+file+"  -out stats.txt -overwrite y",
#                "NaviSECCli.exe analyzer -archivedump -config "+file+"  -xml -out config.xml -overwrite y",
#                "NaviSECCli.exe analyzer -archivedump -rel    "+file+"  -xml -out config_L5.xml -level 5 -overwrite y"
#                ]
#                for command in commands:
#                    call(["cmd.exe","/c"+command])
#                break
#        print('Done.')
#        return

def init_db(conn):
    cur = conn.cursor()
    cur.executescript('''
    DROP TABLE IF EXISTS SPA_B;
    DROP TABLE IF EXISTS PORTS;
    DROP TABLE IF EXISTS BUSES;
    DROP TABLE IF EXISTS RG_LUNS;
    DROP TABLE IF EXISTS POOL_LUNS;
    DROP TABLE IF EXISTS SNAPSHOTS;
    DROP TABLE IF EXISTS RAID_GROUPS;
    DROP TABLE IF EXISTS POOLS;
    DROP TABLE IF EXISTS DRIVES;
    ''')

    cur.executescript('''
    CREATE TABLE SPA_B (
        uid  INTEGER NOT NULL PRIMARY KEY
            AUTOINCREMENT UNIQUE,
        name TEXT,
        read_cache BOOLEAN,
        write_cache BOOLEAN,
        cache_page INTEGER,
        low_water INTEGER,
        high_water INTEGER,
        phys_mem INTEGER,
        rc_size INTEGER,
        wc_size INTEGER,
        warning BOOLEAN
        );

    ''')


    cur.executescript('''
    CREATE TABLE PORTS (
        uid  INTEGER NOT NULL PRIMARY KEY
            AUTOINCREMENT UNIQUE,
         id INTEGER,
         sp INTEGER,
         type INTEGER,
         cur_speed INTEGER,
         max_speed INTEGER,
         iops_avg INTEGER,
         iops_p95 INTEGER,
         mbps_avg INTEGER,
         mbps_p95 INTEGER,
         warning BOOLEAN
         );
    ''')

    cur.executescript('''
    CREATE TABLE BUSES (
        uid  INTEGER NOT NULL PRIMARY KEY
            AUTOINCREMENT UNIQUE,
         id INTEGER,
         iops_avg INTEGER,
         mbps_avg INTEGER,
         abql_avg INTEGER,
         ssd INTEGER,
         sas INTEGER,
         nlsas INTEGER,
         warning BOOLEAN
         );
    ''')

    cur.executescript('''
    CREATE TABLE RG_LUNS (
        uid  INTEGER NOT NULL PRIMARY KEY
            AUTOINCREMENT UNIQUE,
        lun_id INTEGER,
        lun_name TEXT,
        cur_owner TEXT,
        def_owner TEXT,
        max_capacity FLOAT,
        rg_id INTEGER,
        rg_name TEXT,
        util_avg FLOAT,
        util_p95 FLOAT,
        iops_avg INTEGER,
        iops_p95 INTEGER,
        mbps_avg INTEGER,
        mbps_p95 INTEGER,
        lat_avg FLOAT,
        lat_p95 FLOAT,
        abql_avg FLOAT,
        abql_p95 FLOAT,
        warning BOOLEAN
        );
    ''')

    cur.executescript('''
    CREATE TABLE POOL_LUNS (
        uid  INTEGER NOT NULL PRIMARY KEY
            AUTOINCREMENT UNIQUE,
        lun_id INTEGER,
        lun_name TEXT,
        cur_owner TEXT,
        alloc_owner TEXT,
        max_capacity FLOAT,
        used_capacity FLOAT,
        snapshots INTEGER,
        snaps_capacity INTEGER,
        pool_id INTEGER,
        pool_name TEXT,
        util_avg FLOAT,
        util_p95 FLOAT,
        fcrhr_avg FLOAT,
        fcrhr_p95 FLOAT,
        fcwhr_avg FLOAT,
        fcwhr_p95 FLOAT,
        iops_avg INTEGER,
        iops_p95 INTEGER,
        mbps_avg INTEGER,
        mbps_p95 INTEGER,
        lat_avg FLOAT,
        lat_p95 FLOAT,
        abql_avg FLOAT,
        abql_p95 FLOAT,
        warning BOOLEAN

        );
    ''')

    cur.executescript('''
    CREATE TABLE SNAPSHOTS (
        uid  INTEGER NOT NULL PRIMARY KEY
            AUTOINCREMENT UNIQUE,

        lun_id INTEGER,
        lun_name TEXT,
        cur_owner TEXT,
        def_owner TEXT,
        user_capacity FLOAT,
        snaps_used_capacity FLOAT,
        snapshots INTEGER,
        pool_id INTEGER,
        pool_name TEXT,
        util_avg FLOAT,
        util_p95 FLOAT,
        fcrhr_avg FLOAT,
        fcrhr_p95 FLOAT,
        fcwhr_avg FLOAT,
        fcwhr_p95 FLOAT,
        iops_avg INTEGER,
        iops_p95 INTEGER,
        mbps_avg INTEGER,
        mbps_p95 INTEGER,
        lat_avg FLOAT,
        lat_p95 FLOAT,
        abql_avg FLOAT,
        abql_p95 FLOAT,
        warning BOOLEAN

        );
    ''')

    cur.executescript('''
    CREATE TABLE RAID_GROUPS (
        uid  INTEGER NOT NULL PRIMARY KEY
            AUTOINCREMENT UNIQUE,
        id INTEGER,
        name TEXT,
        max_capacity INTEGER,
        free_capacity INTEGER,
        free_cap_prcn INTEGER,
        RAID TEXT,
        ssd INTEGER,
        sas INTEGER,
        nlsas INTEGER,
        util_avg FLOAT,
        util_p95 FLOAT,
        fcrhr_avg FLOAT,
        fcwhr_avg FLOAT,
        iops_avg INTEGER,
        mbps_avg INTEGER,
        lat_avg FLOAT,
        abql_avg FLOAT,
        warning BOOLEAN

        );
    ''')

    cur.executescript('''
    CREATE TABLE POOLS (
        uid  INTEGER NOT NULL PRIMARY KEY
            AUTOINCREMENT UNIQUE,
        id INTEGER,
        name TEXT,
        max_capacity INTEGER,
        used_capacity INTEGER,
        used_cap_prcn INTEGER,
        snaps_capacity INTEGER,
        snaps_cap_prcn INTEGER,
        free_capacity INTEGER,
        free_cap_prcn INTEGER,
        fcache_on BOOLEAN,
        ssd INTEGER,
        sas INTEGER,
        nlsas INTEGER,
        fcrhr_avg FLOAT,
        fcrhr_p95 FLOAT,
        fcwhr_avg FLOAT,
        fcwhr_p95 FLOAT,
        iops_avg INTEGER,
        mbps_avg INTEGER,
        lat_avg FLOAT,
        abql_avg FLOAT,
        warning BOOLEAN
        );
    ''')

    cur.executescript('''
    CREATE TABLE DRIVES (
        uid  INTEGER NOT NULL PRIMARY KEY
            AUTOINCREMENT UNIQUE,
        drive_type TEXT,
        name TEXT,
        bus INTEGER,
        dae INTEGER,
        slot TEXT,
        drive_cap INTEGER,
        pool_name TEXT,
        util_avg FLOAT,
        util_p95 FLOAT,
        iops_avg INTEGER,
        iops_p95 INTEGER,
        mbps_avg INTEGER,
        mbps_p95 INTEGER,
        lat_avg FLOAT,
        lat_p95 FLOAT,
        abql_avg FLOAT,
        abql_p95 FLOAT,
        warning BOOLEAN
        );
    ''')

    conn.commit()

    return

def scan_snap(conn,obj):
    cur = conn.cursor()
    warning=False
    for details in obj:
        words=obj.attrib['name'].split('[')
        lun_name=words[0]
        #print('LUN Name:',lun_name)
        tip=obj.attrib['type']
        #print('Type:',tip)
        for value in obj.iter('value'):
            if value.attrib['type']=='LUN Number':
                lun_id=value.text
                #print('Pool ID:',pool_id)
            if value.attrib['type']=='User Capacity':
                user_capacity=round(int(value.text)/2/1024/1024/1024,3)
                #print('LUN Type:',lun_type)
            if value.attrib['type']=='Snap Used Capacity':
                snaps_used_capacity=round(int(value.text)/2/1024/1024/1024,3)
                #print('Allocated capacity:',used_capacity,'TB')
            if value.attrib['type']=='Snap Count':
                snapshots=int(value.text)
                #print('Snap Count:',snapshots)
            if value.attrib['type']=='Current Owner':
                cur_owner=value.text
                #print('cur_owner',cur_owner)
            if value.attrib['type']=='Default Owner':
                def_owner=value.text
                #print('def_owner',def_owner)
                if def_owner!=cur_owner:
                    warning=True
                    #print('Warning! Current Owner does not match Default Owner for',lun_name)
                    #print('Performance is degraded!')
    cur.execute('''INSERT INTO SNAPSHOTS
    (lun_id, lun_name, cur_owner, def_owner, user_capacity, snaps_used_capacity, snapshots, warning)
    VALUES ( ?, ?, ?, ?, ?, ?, ?, ? )''',
    ( lun_id, lun_name, cur_owner, def_owner, user_capacity, snaps_used_capacity, snapshots, warning) )

    return

def scan_lun(conn,obj):
    cur = conn.cursor()
    warning=False
    for details in obj:
        words=obj.attrib['name'].split('[')
        lun_name=words[0]
        #print('LUN Name:',lun_name)
        w=words[1].split(']')[0]
        if ';' in w: lun_id=w.split(';')[0]
        else: lun_id=w
        #print('LUN ID:',lun_id)
        tip=obj.attrib['type']
        #print('Type:',tip)
        for value in obj.iter('value'):
            if value.attrib['type']=='Pool ID':
                pool_id=value.text
                #print('Pool ID:',pool_id)
            if value.attrib['type']=='LUN Type':
                lun_type=value.text
                #print('LUN Type:',lun_type)
            if value.attrib['type']=="RAID Group ID":
                rg_id=value.text
                #print('RAID Group ID:',rg_id)
            if value.attrib['type']=='LUN Capacity' and value.attrib['metric']=='Blocks':
                max_capacity=round(int(value.text)/2/1024/1024/1024,3)
                #print('Maximum capacity:',max_capacity,'TB')
            if value.attrib['type']=='Consumed Size' and value.attrib['metric']=='Blocks':
                used_capacity=round(int(value.text)/2/1024/1024/1024,3)
                #print('Allocated capacity:',used_capacity,'TB')
            if value.attrib['type']=='Snap Count':
                snapshots=int(value.text)
                #print('Snap Count:',snapshots)
            if value.attrib['type']=='Snap Used Capacity':
                snaps_capacity=round(int(value.text)/2/1024/1024/1024,3)
                #print('Snaps used capacity:',snaps_capacity,'TB')
            if value.attrib['type']=='Current Owner':
                cur_owner=value.text
                #print('cur_owner',cur_owner)
            if value.attrib['type']=='Default Owner':
                def_owner=value.text
                #print('def_owner',def_owner)
                if def_owner!=cur_owner:
                    warning=True
                    #print('Warning! Current Owner does not match Default Owner for',lun_name)
                    #print('Performance is degraded!')
            if value.attrib['type']=="Allocation Owner":
                alloc_owner=value.text
                #print('alloc_owner',alloc_owner)
                if alloc_owner!=cur_owner:
                    warning=True
                    #print('Warning! Current Owner does not match Allocation Owner for',lun_name)
                    #print('Performance is degraded!')
        #print()
        if tip=='Pool Public LUN' or tip=='Thin LUN':
            cur.execute('''INSERT INTO POOL_LUNS
                            (lun_id, lun_name, cur_owner, alloc_owner, max_capacity, used_capacity, snapshots, snaps_capacity, pool_id,warning)
                            VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )''',
            ( lun_id, lun_name, cur_owner, alloc_owner, max_capacity, used_capacity, snapshots, snaps_capacity, pool_id,warning ) )
        if tip=='Public RaidGroup LUN':
            cur.execute('''INSERT INTO RG_LUNS
                            (lun_id, lun_name, max_capacity, cur_owner, rg_id,warning)
                            VALUES ( ?, ?, ?, ?, ?, ? )''',
            ( lun_id, lun_name, max_capacity, cur_owner, rg_id, warning ) )

    return

def scan_disk(conn,obj):
    cur = conn.cursor()
    d=dict()
    for details in obj:
        name=obj.attrib['name']
        bus=int(name.split(' ')[1])
        dae=int(name.split(' ')[3])
        slot=str(name.split(' ')[5])
        #print('Name:',name)
        #print('BED:',bus, dae,slot)
        for value in obj.iter('value'):
            if value.attrib['type']=='Drive Type':
                drive_type=value.text
                #print('Drive Type:',drive_type)
            if value.attrib['type']=='Capacity':
                drive_cap=int(round(int(value.text)/1024,0))
                #print('Drive Capacity:',drive_cap,'GB')
    #print()

    cur.execute('''INSERT INTO DRIVES
                    (drive_type, name, bus, dae, slot, drive_cap)
                    VALUES ( ?, ?, ?, ?, ?, ? )''',
    ( drive_type, name, bus, dae, slot, drive_cap ) )

    return

def scan_pool(conn,obj):
    cur = conn.cursor()
    warning=False

    for details in obj:
        name=obj.attrib['name']
        #print('Name:',name)
        for value in obj.iter('value'):
            if value.attrib['type']=='Pool Name':
                name=value.text
                #print('pool_name:',name)
            if value.attrib['type']=="Total Capacity" :
                max_capacity=round(int(value.text)/2/1024/1024/1024,2)
                #print('pool_cap:',max_capacity,'TB')
            if value.attrib['type']=="Consumed Capacity" :
                used_capacity=round(int(value.text)/2/1024/1024/1024,2)
                #print('pool_cons:',used_capacity,'TB')
            if value.attrib['type']=="Free Capacity" :
                free_capacity=round(int(value.text)/2/1024/1024/1024,2)
                #print('pool_free:',free_capacity,'TB')
            if value.attrib['type']=="Allocated Snap Space" :
                snaps_capacity=round(int(value.text)/2/1024/1024/1024,2)
                #print('pool_snaps:',snaps_capacity,'TB')
                free_cap_prcn=int(round(free_capacity/max_capacity*100,0))
                used_cap_prcn=int(round(used_capacity/max_capacity*100,0))
                snaps_cap_prcn=int(round(snaps_capacity/max_capacity*100,0))
                if used_capacity/max_capacity>0.85: warning=True
            if value.attrib['type']=="FAST Cache state":
                if value.text.lower()=='enabled': fcache_on=True
                else: fcache_on=False
                #print('FCache Enabled:',fcache_on)

    cur.execute('''INSERT INTO POOLS
                    (name, max_capacity, used_capacity, used_cap_prcn, snaps_capacity,snaps_cap_prcn,free_capacity,free_cap_prcn, fcache_on, warning)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ? )''',
    (name, max_capacity, used_capacity, used_cap_prcn, snaps_capacity,snaps_cap_prcn,free_capacity,free_cap_prcn, fcache_on, warning ) )

    return

def scan_rgrp(conn, obj):
    cur = conn.cursor()
    for details in obj:
        name=obj.attrib['name']
        #print('Name:',name)
        for value in obj.iter('value'):
            if value.attrib['type']=='Group ID':
                id=value.text
                #print('RG ID:',id)
            if value.attrib['type']=="Total Capacity" :
                max_capacity=round(int(value.text)/2/1024/1024/1024,2)
                #print('RG Total Capacity:',max_capacity,'TB')
            if value.attrib['type']=='Free Space':
                free_capacity=round(int(value.text)/2/1024/1024/1024,2)
                #print('RG Free Capacity:',free_capacity,'TB')
                free_cap_prcn=int(round(free_capacity/max_capacity*100,0))
            if value.attrib['type']=='RAID Type':
                RAID=value.text

    cur.execute('''INSERT INTO RAID_GROUPS
                    (id, name, max_capacity, free_capacity, free_cap_prcn, RAID)
                    VALUES (?, ?, ?, ?, ?, ? )''',
    (id, name, max_capacity, free_capacity, free_cap_prcn, RAID) )


    return

def update_object_value(conn,tname,obj,objname,field,value):
#    print('Updating',field,'for',objname,'with',value,'in table',tname)
#    value='"'+value+'"'
#    print(value)
#    c.execute("SELECT * FROM {tn} WHERE {idf}=?".\
#    format(tn=table_name, cn=column_2, idf=id_column), (123456,))
    cur=conn.cursor()
    cur.execute('UPDATE '+tname+' SET '+field+' = ? WHERE '+obj+' = ? ', [value,objname] )
    return

def set_fast_cache_drives(conn):
    cur=conn.cursor()
    print('Searching for FAST Cache drives.')
#    input()
    cur.execute('UPDATE DRIVES SET pool_name = "FAST_Cache" WHERE pool_name IS NULL AND (drive_type="SAS Flash" OR drive_type="SATA Flash")')
    conn.commit()
#    cur.execute('UPDATE DRIVES SET pool_name = "FAST_Cache" WHERE pool_name IS NULL AND drive_type="SATA Flash"')
    return


def nar_get_config_data(SN):
    fname='config.xml'
    conn = sqlite3.connect('narvision.db')
    cur = conn.cursor()
    init_db(conn)
    tree = xml.etree.ElementTree.parse(fname)
    root = tree.getroot()
    for child in root:
        print(child.tag, child.attrib)
    for obj in root.iter('object'):
        if obj.attrib['type']=='Pool':
            scan_pool(conn,obj)
        if obj.attrib['type']=='RAID Group':
            scan_rgrp(conn,obj)
        if ('LUN' in obj.attrib['type']) and ('Public' in obj.attrib['type']):
            scan_lun(conn,obj)
        if ('Snapshot Mount Point' in obj.attrib['type']):
            scan_snap(conn,obj)
        if obj.attrib['type']=='Disk':
            scan_disk(conn,obj)
    conn.commit()

    #input('config_L5.xml')
    fname='config_L5.xml'
    tree = xml.etree.ElementTree.parse(fname)
    root = tree.getroot()
    for child_l1 in root:
        #print('L1', child_l1.attrib) #Universe
        for child_l2 in child_l1:
            #print('L2', child_l2.attrib) #Storage Subsystems
            for child_l3 in child_l2:
                #print('L3', child_l3.attrib) #SP, RAID Groups, Pools, Consistency Groups
                if child_l3.attrib['type']=='RAID Group' or child_l3.attrib['type']=='Pool':
                    pool_name=child_l3.attrib['name']
                    #print(pool_name)
                    for child_l4 in child_l3:
                        if child_l4.attrib['type']=='Disk': #Disks, LUNs
                            #print('L4', child_l4.attrib)
                            disk_name=child_l4.attrib['name']
                            update_object_value(conn,'DRIVES','name',disk_name,'pool_name',pool_name)
                        if child_l4.attrib['type']=='Public RaidGroup LUN':
                            lun_name=child_l4.attrib['name'].split('[')[0]
                            update_object_value(conn,'RG_LUNS','lun_name',lun_name,'rg_name',pool_name)
                        if child_l4.attrib['type']=='Pool Public LUN' or child_l4.attrib['type']=='Thin LUN':
                            lun_name=child_l4.attrib['name'].split('[')[0]
                            update_object_value(conn,'POOL_LUNS','lun_name',lun_name,'pool_name',pool_name)
                        if child_l4.attrib['type']=='Snapshot Mount Point':
                            lun_name=child_l4.attrib['name'].split('[')[0]
                            update_object_value(conn,'SNAPSHOTS','lun_name',lun_name,'pool_name',pool_name)

    conn.commit()
    return


def nar_display_system_summary(SN):
    conn = sqlite3.connect('narvision.db')
    cur = conn.cursor()
#    get_config(SN)
    for file in os.listdir("."):
        if file.startswith('CK') and file.endswith('.nar') :
            SN=file.split('_')[0]
            break

    directory=SN+'_csv/'
    fnames=['dump_norm_disk_iops.csv', 'dump_norm_disk_response.csv', 'dump_norm_disk_queues.csv', 'dump_norm_disk_mbps.csv']

    for fname in fnames:
        f=open(directory+fname)
        data=f.read()
        data=data.splitlines()
        for line in data[1:]:
            words=line.split(',')
            name=words[0].split('[')[0]
    #        print(name)
            counter=words[0].split('[')[1][:-1]
    #        print(counter)
            p95=float(words[2])
            avg=float(words[3])
            if 'iops' in fname:
                update_object_value(conn,'DRIVES','name',name,'iops_avg',avg)
                update_object_value(conn,'DRIVES','name',name,'iops_p95',p95)
            if 'response' in fname:
                update_object_value(conn,'DRIVES','name',name,'lat_avg',avg)
                update_object_value(conn,'DRIVES','name',name,'lat_p95',p95)
            if 'queues' in fname:
                update_object_value(conn,'DRIVES','name',name,'abql_avg',avg)
                update_object_value(conn,'DRIVES','name',name,'abql_p95',p95)
            if 'mbps' in fname:
                update_object_value(conn,'DRIVES','name',name,'mbps_avg',avg)
                update_object_value(conn,'DRIVES','name',name,'mbps_p95',p95)

    fnames=['dump_norm_luns_iops_tot.csv', 'dump_norm_luns_response.csv', 'dump_norm_luns_queues.csv']

    for fname in fnames:
        f=open(directory+fname)
        data=f.read()
        data=data.splitlines()
        for line in data[1:]:
            words=line.split(',')
            name=words[0].split('[')[0]
            counter=words[0].split('[')[1][:-1]
            p95=float(words[2])
            avg=float(words[3])
            #print(name,counter,avg,p95)
            #input()
            if 'iops' in fname:
                update_object_value(conn,'RG_LUNS','lun_name',name,'iops_avg',avg)
                update_object_value(conn,'RG_LUNS','lun_name',name,'iops_p95',p95)
                update_object_value(conn,'POOL_LUNS','lun_name',name,'iops_avg',avg)
                update_object_value(conn,'POOL_LUNS','lun_name',name,'iops_p95',p95)
                update_object_value(conn,'SNAPSHOTS','lun_name',name,'iops_avg',avg)
                update_object_value(conn,'SNAPSHOTS','lun_name',name,'iops_p95',p95)
            if 'response' in fname:
                update_object_value(conn,'RG_LUNS','lun_name',name,'lat_avg',avg)
                update_object_value(conn,'RG_LUNS','lun_name',name,'lat_p95',p95)
                update_object_value(conn,'POOL_LUNS','lun_name',name,'lat_avg',avg)
                update_object_value(conn,'POOL_LUNS','lun_name',name,'lat_p95',p95)
                update_object_value(conn,'SNAPSHOTS','lun_name',name,'lat_avg',avg)
                update_object_value(conn,'SNAPSHOTS','lun_name',name,'lat_p95',p95)
            if 'queues' in fname:
                update_object_value(conn,'RG_LUNS','lun_name',name,'lat_avg',avg)
                update_object_value(conn,'RG_LUNS','lun_name',name,'lat_p95',p95)
                update_object_value(conn,'POOL_LUNS','lun_name',name,'abql_avg',avg)
                update_object_value(conn,'POOL_LUNS','lun_name',name,'abql_p95',p95)
                update_object_value(conn,'SNAPSHOTS','lun_name',name,'abql_avg',avg)
                update_object_value(conn,'SNAPSHOTS','lun_name',name,'abql_p95',p95)

    conn.commit()

    set_fast_cache_drives(conn)

    cur.execute('SELECT drive_cap,drive_type, bus, dae, slot, iops_p95,lat_p95,abql_p95,pool_name FROM DRIVES ORDER BY iops_p95 DESC')
    data=cur.fetchmany(20)

    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print('|                                      Top DRIVES by IOPS                                                                                  |',file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print("|drive_cap  type       bus         enc         slot         iops_p95    lat_p95    abql_p95     pool_name                                  |",file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    for row in data:
        for d in row:
             print ("{:<11}".format(d),end=' ',file=report)
        print('\n_________________________________________________________________________________________________________________________________________',file=report)
    cur.execute('SELECT drive_cap,drive_type, bus, dae, slot, iops_p95,lat_p95,abql_p95,pool_name FROM DRIVES ORDER BY lat_p95 DESC')
    data=cur.fetchmany(20)
    print('\n',file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print('|                                    Top DRIVES by Latency                                                                                 |',file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print("|drive_cap  type       bus         enc         slot         iops_p95    lat_p95    abql_p95     pool_name                                  |",file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    for row in data:
        for d in row:
            if d!=None: print ("{:<11}".format(d),end=' ',file=report)
        print('\n_________________________________________________________________________________________________________________________________________',file=report)
    cur.execute('SELECT drive_cap,drive_type, bus, dae, slot, iops_p95,lat_p95,abql_p95,pool_name FROM DRIVES ORDER BY abql_p95 DESC')
    data=cur.fetchmany(20)
    print('\n',file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print("|                                      Top DRIVES by ABQL                                                                                  |",file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print("|drive_cap  type       bus         enc         slot         iops_p95    lat_p95    abql_p95     pool_name                                  |",file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    for row in data:
        for d in row:
             print ("{:<11}".format(d),end=' ',file=report)
        print('\n_________________________________________________________________________________________________________________________________________',file=report)

    cur.execute('''SELECT lun_id,cur_owner,alloc_owner,max_capacity,used_capacity,snapshots,warning,
                          iops_p95,lat_p95,abql_p95,pool_name FROM POOL_LUNS ORDER BY iops_p95 DESC''')
    data=cur.fetchmany(20)
    print('\n',file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print('|                                  Top POOL_LUNS by IOPS                                                                                   |',file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print("|lun_id      cur_owner   alloc_owner  max_cap       used_cap   snapshots      warning      iops_p95     lat_p95      abql_p95    pool_name |",file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    for row in data:
        for d in row:
             print ("{:<12}".format(d),end=' ',file=report)
        print('\n_________________________________________________________________________________________________________________________________________',file=report)

    cur.execute('''SELECT lun_id,cur_owner,alloc_owner,max_capacity,used_capacity,snapshots,warning,
                          iops_p95,lat_p95,abql_p95,pool_name FROM POOL_LUNS ORDER BY lat_p95 DESC''')
    data=cur.fetchmany(20)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print('|                                 Top POOL_LUNS by Latency                                                                                 |',file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print("|lun_id      cur_owner   alloc_owner  max_cap       used_cap   snapshots      warning      iops_p95     lat_p95      abql_p95    pool_name |",file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    for row in data:
        for d in row:
             print ("{:<12}".format(d),end=' ',file=report)
        print('\n_________________________________________________________________________________________________________________________________________',file=report)
    cur.execute('''SELECT lun_id,cur_owner,alloc_owner,max_capacity,used_capacity,snapshots,warning,
                          iops_p95,lat_p95,abql_p95,pool_name FROM POOL_LUNS ORDER BY abql_p95 DESC''')
    data=cur.fetchmany(20)
    print('',file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print('|                                   Top POOL_LUNS by ABQL                                                                                  |',file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print("|lun_id      cur_owner   alloc_owner  max_cap       used_cap   snapshots      warning      iops_p95     lat_p95      abql_p95    pool_name |",file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    for row in data:
        for d in row:
             print ("{:<12}".format(d),end=' ',file=report)
        print('\n_________________________________________________________________________________________________________________________________________',file=report)
    cur.execute('''SELECT lun_id,cur_owner,def_owner,user_capacity,snaps_used_capacity,snapshots,warning,
                          iops_p95,lat_p95,abql_p95,pool_name FROM SNAPSHOTS ORDER BY iops_p95 DESC''')
    data=cur.fetchmany(20)
    print('',file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print('|                                Top SNAPSHOTS by IOPS                                                                                     |',file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print("|lun_id     cur_owner    def_owner    max_cap      used_cap   snapshots   warning          iops_p95    lat_p95      abql_p95      pool_name|",file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    for row in data:
        for d in row:
             print ("{:<12}".format(d),end=' ',file=report)
        print('\n_________________________________________________________________________________________________________________________________________',file=report)
    cur.execute('''SELECT lun_id,cur_owner,def_owner,user_capacity,snaps_used_capacity,snapshots,warning,
                          iops_p95,lat_p95,abql_p95,pool_name FROM SNAPSHOTS ORDER BY lat_p95 DESC''')
    data=cur.fetchmany(20)
    print('',file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print('|                              Top SNAPSHOTS by Latency                                                                                    |',file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print("|lun_id     cur_owner    def_owner    max_cap      used_cap   snapshots   warning          iops_p95    lat_p95      abql_p95      pool_name|",file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    for row in data:
        for d in row:
             print ("{:<12}".format(d),end=' ',file=report)
        print('\n_________________________________________________________________________________________________________________________________________',file=report)
    cur.execute('''SELECT lun_id,cur_owner,def_owner,user_capacity,snaps_used_capacity,snapshots,warning,
                          iops_p95,lat_p95,abql_p95,pool_name FROM SNAPSHOTS ORDER BY abql_p95 DESC''')
    data=cur.fetchmany(20)
    print('',file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print('|                              Top SNAPSHOTS by ABQL                                                                                        |',file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    print("|lun_id     cur_owner    def_owner    max_cap      used_cap   snapshots   warning          iops_p95    lat_p95      abql_p95       pool_name|",file=report)
    print(" ------------------------------------------------------------------------------------------------------------------------------------------",file=report)
    for row in data:
        for d in row:
             print ("{:<12}".format(d),end=' ',file=report)
        print('\n_________________________________________________________________________________________________________________________________________',file=report)

    print('\n',file=report)
    print('-------------------------------------------------------------------------------',file=report)
    print('|                       System IOPS Summary (AVG)',file=report)
    print('-------------------------------------------------------------------------------',file=report)
    sys_iops=0
    cur.execute('SELECT SUM(iops_avg) FROM POOL_LUNS')
    d=cur.fetchone()
    #print(d)
    if d[0]!=None: sys_iops=int(d[0])
    cur.execute('SELECT SUM(iops_avg) FROM RG_LUNS')
    d=cur.fetchone()
    if d[0]!=None: sys_iops+=int(d[0])
    cur.execute('SELECT SUM(iops_avg) FROM SNAPSHOTS')
    d=cur.fetchone()
    if d[0]!=None: sys_iops+=int(d[0])
    print('|    frontend all  |   ',sys_iops,'IOPS',file=report)
    print('-------------------------------------------------------------------------------',file=report)

    #if d[0]!=None : print('all backend',int(d[0]),'IOPS')
    cur.execute('SELECT SUM(iops_avg) FROM DRIVES')
    d=cur.fetchone()
    if d[0]!=None :
        print('|    backend all   |   ',int(d[0]),'IOPS',file=report)
        print('-------------------------------------------------------------------------------',file=report)
    cur.execute('SELECT SUM(iops_avg) FROM DRIVES WHERE drive_type="SAS Flash" OR drive_type="SATA Flash"')
    d=cur.fetchone()
    if d[0]!=None :
        print('|    backend ssd   |   ',int(d[0]),end=' ',file=report)

    cur.execute('SELECT SUM(iops_avg) FROM DRIVES WHERE pool_name="FAST_Cache"')
    d=cur.fetchone()
    if d[0]!=None :
        print('(incl. fcache:',int(d[0]),') IOPS',file=report)
    else: print('IOPS',file=report)
    print('-------------------------------------------------------------------------------',file=report)

    cur.execute('SELECT SUM(iops_avg) FROM DRIVES WHERE drive_type="SAS"')
    d=cur.fetchone()
    if d[0]!=None :
        print('|    backend sas   |   ',int(d[0]),'IOPS',file=report)
        print('-------------------------------------------------------------------------------',file=report)

    cur.execute('SELECT SUM(iops_avg) FROM DRIVES WHERE drive_type="NL SAS"')
    d=cur.fetchone()
    if d[0]!=None :
        print('|    backend nlsas |   ',int(d[0]),'IOPS',file=report)
        print('-------------------------------------------------------------------------------',file=report)

    print("",file=report)
    cur.execute('SELECT DISTINCT bus FROM DRIVES')
    d=cur.fetchall()

    print('\n-------------------------------------------------------------------------------',file=report)
    print('|                       System Backend Summary',file=report)
    print('-------------------------------------------------------------------------------',file=report)
    print('|                           Total Busses:',len(d),file=report)
    print('|      Following bus numbers are present:',end='',file=report)
    for bus in d: print(bus,end=',',file=report)
    print('',file=report)
#    input()
    for b in d:
        print('-------------------------------------------------------------------------------',file=report)
        cur.execute('SELECT COUNT(bus) FROM DRIVES WHERE (drive_type="SAS Flash" OR drive_type="SATA Flash")  AND bus=?',(b[0],))
        d=cur.fetchall()
        bus_ssd=str(d[0][0])
        cur.execute('SELECT COUNT(bus) FROM DRIVES WHERE drive_type="SAS" AND bus=?',(b[0],))
        d=cur.fetchall()
        bus_sas=str(d[0][0])
        cur.execute('SELECT COUNT(bus) FROM DRIVES WHERE drive_type="NL SAS" AND bus=?',(b[0],))
        d=cur.fetchall()
        bus_nlsas=str(d[0][0])
        print('|   bus   ',b[0],'   |    ssd:',bus_ssd.rjust(3),'    sas:',bus_sas.rjust(3),'    nl sas:',bus_nlsas.rjust(3),file=report)
        print('-------------------------------------------------------------------------------',file=report)
        cur.execute('SELECT SUM(iops_avg) FROM DRIVES WHERE bus=?',(b[0],))
        d=cur.fetchall()

        if d[0][0]!=None:
            bus_iops_avg=str(round(float(d[0][0]),0))
        else:
            print("No drives found on bus:",b[0],"!!!",file=report)

        cur.execute('SELECT SUM(iops_p95) FROM DRIVES WHERE bus=?',(b[0],))
        d=cur.fetchall()

        if d[0][0]!=None:
            bus_iops_p95=str(round(float(d[0][0]),0))
        else:
            print("No drives found on bus:",b,"!!!",file=report)

        print('|   bus   ',b[0],'   |   iops avg   ',bus_iops_avg.rjust(7),'   |   iops p95   ',bus_iops_p95.rjust(7),file=report)

        print('-------------------------------------------------------------------------------',file=report)
        cur.execute('SELECT SUM(mbps_avg) FROM DRIVES WHERE bus=?',(b[0],))
        d=cur.fetchall()

        if d[0][0]!=None:
            bus_mbps_avg=str(round(float(d[0][0]),0))
        else:
            print("No drives found on bus:",b[0],"!!!",file=report)

        cur.execute('SELECT SUM(mbps_p95) FROM DRIVES WHERE bus=?',(b[0],))
        d=cur.fetchall()

        if d[0][0]!=None:
            bus_mbps_p95=str(round(float(d[0][0]),0))
        else:
            print("No drives found on bus:",b,"!!!",file=report)

        print('|   bus   ',b[0],'   |   mbps avg   ',bus_mbps_avg.rjust(7),'   |   mbps p95   ',bus_mbps_p95.rjust(7),file=report)
        print('-------------------------------------------------------------------------------',file=report)
        cur.execute('SELECT SUM(abql_avg) FROM DRIVES WHERE bus=?',(b[0],))
        d=cur.fetchall()

        if d[0][0]!=None:
            bus_abql_avg=str(round(float(d[0][0]),0))
        else:
            print("No drives found on bus:",b[0],"!!!",file=report)

        cur.execute('SELECT SUM(abql_p95) FROM DRIVES WHERE bus=?',(b[0],))
        d=cur.fetchall()

        if d[0][0]!=None:
            bus_abql_p95=str(round(float(d[0][0]),0))
        else:
            print("No drives found on bus:",b[0],"!!!",file=report)
            continue


        print('|   bus   ',b[0],'   |   abql avg   ',bus_abql_avg.rjust(7),'   |   abql p95   ',bus_abql_p95.rjust(7),file=report)
        print('-------------------------------------------------------------------------------',file=report)

        print("",file=report)

    print('\n',file=report)
    print('-------------------------------------------------------------------------------',file=report)
    print('|                    Pools/RAID Groups and Backend IO Summary',file=report)
    print('-------------------------------------------------------------------------------',file=report)
    cur.execute('SELECT DISTINCT pool_name FROM DRIVES')
    pools=cur.fetchall()
    for pool in pools:
        print('\n',file=report)
        print('-------------------------------------------------------------------------------',file=report)
        cur.execute('SELECT COUNT(drive_type) FROM DRIVES WHERE (drive_type="SAS Flash" OR drive_type="SATA Flash") AND pool_name=?', pool)
        ssd_qty=cur.fetchall()[0][0]
    #    print(pool[0])
    #    print(ssd_qty)
    #    input()
        cur.execute('SELECT COUNT(drive_type) FROM DRIVES WHERE drive_type="SAS" AND pool_name=?', pool)
        sas_qty=cur.fetchall()[0][0]
        cur.execute('SELECT COUNT(drive_type) FROM DRIVES WHERE drive_type="NL SAS" AND pool_name=?', pool)
        nlsas_qty=cur.fetchall()[0][0]
        if pool[0]=='FAST_Cache':
            print('|                             FAST Cache SSDs',ssd_qty,file=report)
            print('-------------------------------------------------------------------------------',file=report)

            continue
        else: print('| ',pool[0],'         SSD:',ssd_qty,'   SAS:',sas_qty,'    NLSAS:',nlsas_qty,'',file=report)
        print('-------------------------------------------------------------------------------',file=report)

        cur.execute('SELECT SUM(iops_avg) FROM DRIVES WHERE pool_name=?', pool)
        d=cur.fetchall()
        if d[0][0]==None:
            print("No pools found",file=report)
            continue
        pool_iops_be=int(round(float(d[0][0]),0))

        cur.execute('SELECT SUM(abql_avg) FROM DRIVES WHERE pool_name=?', pool)
        d=cur.fetchall()
        pool_abql=int(round(float(d[0][0]),0))
        pool_iops_fe=0
        cur.execute('SELECT SUM(iops_avg) FROM POOL_LUNS WHERE pool_name=?', pool)
        d=cur.fetchall()
    #    print(d)
        if d[0][0]!=None: pool_iops_fe+=int(round(float(d[0][0]),0))
        cur.execute('SELECT SUM(iops_avg) FROM RG_LUNS WHERE rg_name=?', pool)
        d=cur.fetchall()
    #    print(d)
        if d[0][0]!=None: pool_iops_fe+=int(round(float(d[0][0]),0))
        cur.execute('SELECT SUM(iops_avg) FROM SNAPSHOTS WHERE pool_name=?', pool)
        d=cur.fetchall()
    #    print(d)
        if d[0][0]!=None: pool_iops_fe+=int(round(float(d[0][0]),0))
        print('|   fe iops avg ',str(pool_iops_fe).rjust(5), '|   be iops avg ',str(pool_iops_be).rjust(5),'|   be abql_avg ',str(pool_abql).rjust(5),file=report)
        print('-------------------------------------------------------------------------------',file=report)
        cur.execute('SELECT SUM(iops_p95) FROM DRIVES WHERE pool_name=?', pool)
        d=cur.fetchall()
        pool_iops_be=int(round(float(d[0][0]),0))

        cur.execute('SELECT SUM(abql_p95) FROM DRIVES WHERE pool_name=?', pool)
        d=cur.fetchall()
        pool_abql=int(round(float(d[0][0]),0))

        pool_iops_fe=0
        cur.execute('SELECT SUM(iops_p95) FROM POOL_LUNS WHERE pool_name=?', pool)
        d=cur.fetchall()
    #    print(d)
        if d[0][0]!=None: pool_iops_fe+=int(round(float(d[0][0]),0))
        cur.execute('SELECT SUM(iops_p95) FROM RG_LUNS WHERE rg_name=?', pool)
        d=cur.fetchall()
    #    print(d)
        if d[0][0]!=None: pool_iops_fe+=int(round(float(d[0][0]),0))
        cur.execute('SELECT SUM(iops_p95) FROM SNAPSHOTS WHERE pool_name=?', pool)
        d=cur.fetchall()
    #    print(d)
        if d[0][0]!=None: pool_iops_fe+=int(round(float(d[0][0]),0))
        print('|   fe iops p95 ',str(pool_iops_fe).rjust(5), '|   be iops p95 ',str(pool_iops_be).rjust(5),'|   be abql p95 ',str(pool_abql).rjust(5),file=report)
        print('-------------------------------------------------------------------------------',file=report)
    print("\n\n\n\n\n\n\nEND OF DOCUMENT",file=report)


    return


#top_items=cur.fetchmany(20)
#print('lun_id,lun_name,cur_owner,def_owner,user_capacity,snaps_used_capacity,snapshots,pool_name,warning,iops_avg,iops_p95,lat_avg,lat_p95,abql_avg,abql_p95')
#for item in top_items:
#    print(item)




#SN="CKM00134500989"
print("""
NarVision version 0.1.
By Denis Serov. All Rights Reserved.

This program is designed to help Dell EMC storage professionals to save their time when analyzing of VNX Storage Systems.
NarVision processes VNX NAR files to create plots and produce system insights (BE bus IO balance, FE-to-BE IO ratio, Pools IO balance, Top Busy objects)
NaviSECCli must be installed on your computer and added to path environment to have full functionality.
You need to provide at least one NAR file from VNX system for problem period.

NarVision processing steps are following:
1. Extract storage configuration data from NAR.
2. Merge NARs for specific SN in current directory.
3. Dump all data from NARs to serialized CSV files.
4. Normalize (deserialize) CSV data to create interactive HTML plots for key metrics (SP,LUNs,Drives workload).
5. Produce preliminairy analytics plots (workload skews for LUNs and Drives)
6. Load data to database for more analytics.
7. Generate system-level performance insights.

All above steps are automated with -a option (recommended).
If -a is not specified, it will run interactively.

CSVs will be stored in SN_csv directory.
HTML plots will be stored in SN_plots directory.
Insights will be stored in current directory in SN_insights.txt file.
Where SN is serial number of VNX (i.e. CKM0013450098).

This pre-productoon build is provided to Alexey Leontiev for personal use and testing purposes.
""")

start_time=time.time()
print("Started at",datetime.datetime.now())

arg=get_arg()
SN=None
if arg.sernum!=None:
    SN=arg.sernum
else:
    for file in os.listdir("."):
        if (file.startswith('CK') or file.startswith('AP')) and file.endswith('.nar'):
            s=file.split('_')[0]
            if input('Do you want to proceed for this SN:'+s+'? ([y]/n): ')!='n':
                SN=s
                break
    if SN==None:
        print('You did not choose any SN.')
        exit()

if arg.auto: AUTO=True
else: AUTO=False

directory=SN+'_csv/'
plots_dir=SN+'_plots/'

print("Processing NAR files for SN",SN)

if not os.path.exists(directory):
        os.makedirs(directory)
if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
clean_temp(tempfile.gettempdir())

if AUTO or input('Do you want to get array configuration data in XML format from NAR file? [for quick snap of what is inside of NAR](y/[n])')=='y': get_config(SN)
report=open(SN+"_insights.txt","a")
if AUTO or input('Do you want to merge all NAR files matching '+SN+' in current directory? [required if you did not merge yet ](y/[n])')=='y':  get_all_merged(SN)
if AUTO or input('Do you want to dump raw data to CSVs from NAR [Required for further processing, if you did not dump data yet]?(y/[n])')=='y': dump_from_nar("merged_"+SN+".nar",directory)#"merged_"+SN+".nar")
if AUTO or input('Do you want to process dumped raw data stored in CSVs now? [Required if your data are not normalized yet](y/[n])')=='y':      process_csv(directory)
if AUTO or input('Analyze normalized CSV? [This will produce HTML plots from normalized data]?(y/[n])')=='y': analyze_csv(directory)
if AUTO or input('Create configuration DB from previsouly generated XMLs? [Required for producing performance insights](y/[n])')=='y':          nar_get_config_data(SN)
if AUTO or input('Generate system performance insights? [This will create reports of how key system components are performning in general](y/[n])')=='y':
                                                                                                                                                nar_display_system_summary(SN)
                                                                                                                                                report.close()
                                                                                                                                                print("Examine",SN+"_insights.txt in current directory")

#normalize_csv('port_bandwidth.csv',directory)
#analyze_csv('norm_luns_iops_tot.csv',directory)
#plot_csv('sys_sp_queues.csv')
end_time=time.time()
print("Finished at",datetime.datetime.now())
print('It took ',int(round((end_time-start_time)/60,0)),'minute(s) to finish the job.')
input('Press ENTER')
