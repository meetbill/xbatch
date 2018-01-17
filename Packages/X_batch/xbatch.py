#!/usr/bin/python
#coding:utf8
#Author=Bill
# 变量说明(4类变量)
# (1)主机群组hostgroup_all dict
# (2)主机 servers_allinfo dict
# (3)运行模式xbatch
# (3)全局变量output_info
VERSION="1.6.3"
# system
import os
import sys
import json
import subprocess
import traceback
from pydoc import render_doc
import threading
import ConfigParser
import time
import re
import getpass
import random

root_path = os.path.split(os.path.realpath(__file__))[0]
sys.path.insert(0, os.path.join(root_path, 'mylib'))
os.chdir(root_path)
reload(sys)
sys.setdefaultencoding('utf8')

# mylib
import mylog
import init_install
import format_show
import argparse
import paramiko

HOME = os.path.split(os.path.realpath(__file__))[0]
DIR_LOG='/var/log/xbatch'
DIR_CONF='/etc/xbatch'
#------------------------------------log
LogFile='%s/xbatch.log' %DIR_LOG
SLogFile='%s/xbatch.source.log' %DIR_LOG
from BLog import Log
debug=False
logpath = "%s/xbatch_arch.log" %DIR_LOG
logger = Log(logpath,level="debug",is_console=debug, mbs=5, count=5)

#------------------------------------config
HostsFile="%s/hosts" %DIR_CONF
ConfFile="%s/xbatch.conf" %DIR_CONF
try:
    paramiko.util.log_to_file('%s/paramiko.log' %DIR_LOG)
except Exception,e:
    pass

def Read_config(file="%s"%ConfFile):
    global CONFMD5,Useroot,RunMode,UseKey,ssh_key
    global HOSTSMD5
    HostsGroup={}
    
    # (1)查看是否有配置文件
    if  not os.path.exists(HostsFile):
        print "读取配置文件错误"
        sys.exit(1)
        print
    if  not os.path.exists(ConfFile):
        print "读取配置文件错误"
        sys.exit(1)
        print
    
    # (2)读取Config配置文件
    config_file=ConfigParser.ConfigParser()
    try:
        config_file.read(file)
    except ConfigParser.ParsingError,e:
        print "文件%s格式错误.\a\n\t" % (file)
        sys.exit(1)
    except Exception,e:
        print e
        sys.exit(1)
    #---------------------------------------------------------------config Useroot
    Useroot=config_file.get("X_batch","Useroot").upper()

    #---------------------------------------------------------------config RunMode
    try:
        RunMode=config_file.get("X_batch","RunMode").upper()
    except Exception,e:
        RunMode='M'
        print "No Runmode default Mutiple(M)"

    #---------------------------------------------------------------config UseKey
    try:
        UseKey=config_file.get("X_batch","UseKey").upper()
    except:
        UseKey="N"
    try:
        ssh_key=config_file.get("X_batch","ssh_key")
    except:
        ssh_key="~/.ssh/id_rsa"

    # (3)读取host配置文件
    try:
        host_file=open(HostsFile)
        NoPassword=False
        NoRootPassword=False
        # 判断第一行是否有主机组
        line_one_flag=True
        servers_info={}
        for line in host_file:
            if re.search("^#",line) or re.search("^ *$",line):
                continue
            if re.search("^ *\[.*\] *$",line):
                CurGroup=re.sub("^ *\[|\] *$","",line).strip().lower()
                HostsGroup[CurGroup]=[]
                line_one_flag=False
                # 显示主机组
                # print CurGroup
                continue
            else:
                if line_one_flag:
                    print "请为hosts文件第一行处命令一个主机组的名字 [主机组名字]"
                    sys.exit()
            host_info=line.strip().split("===")
            if len(host_info)<5:
                print """您的配置文件中没有足够的列:\033[1m\033[1;31m[%s]\033[1m\033[0m\a
请使用如下格式:
主机地址===端口号===登陆账户===登陆密码===su-root密码，如果没有配置使用su-root，此列可为None""" % line.strip()
                sys.exit()
            # 端口
            servers_info[host_info[0]]={}
            servers_info[host_info[0]]["ip"]=host_info[0]
            servers_info[host_info[0]]["port"]=int(host_info[1])
            try:
                HostsGroup[CurGroup].append(host_info[0])
            except Exception,e:
                HostsGroup[CurGroup]=[]
                HostsGroup[CurGroup].append(host_info[0].lower())
            if UseKey.upper()=="N":
                servers_info[host_info[0]]["username"]=host_info[2]
                TP=re.search("^[Nn][Oo][Nn][Ee]$",host_info[3])
                if TP:
                    servers_info[host_info[0]]["password"]=None
                    NoPassword=True
                else:
                    servers_info[host_info[0]]["password"]=host_info[3]
                        
            else:
                servers_info[host_info[0]]["username"]=host_info[2]
                servers_info[host_info[0]]["password"]=None
            if Useroot.upper()=="Y":
                try:
                    TK=re.search("^[Nn][Oo][Nn][Ee]$",host_info[4])
                    if TK:
                        NoRootPassword=True
                        servers_info[host_info[0]]["rootpassword"]=None
                    else:
                        servers_info[host_info[0]]["rootpassword"]=host_info[4]
                except Exception,e:
                    print """您使用了su - root ，但未指定su - root的密码
%s===端口===账户名===密码===root的密码""" % (host_info[0])
                    print e
                    sys.exit()
        host_file.close()
    except IndexError:
        print """您的主机文件中，没有足够的配置，正确的应该是:
主机列===端口列===账户名列===密码列===su-root密码列"""
        sys.exit()
    except Exception,e:
        print "读取配置错误 %s (%s) "%(e,HostsFile)
        sys.exit(1)
    if NoPassword and UseKey=="N":
        SetPassword=getpass.getpass("请在此处为在密码列填写了[None]的主机指定密码,如果没有填写None的主机，密码依然读取配置文件中的信息(请确保您输入的密码适用于所有密码列填写了None的主机，否则请在配置文件%s/hosts文件中逐个指定)\n\033[1;33mHosts Password:\033[0m  "%DIR_CONF)
        if SetPassword:
            print "已为所有主机指定密码"
        else:
            print "您尚未指定密码，程序退出"
            sys.exit()
        for host in servers_info:
            if servers_info[host]["password"] is None:
                servers_info[host]["password"]=SetPassword
        NoPassword=False
    if Useroot=="Y":
        if NoRootPassword:
            SetRootPassword=getpass.getpass("请指定su-root的密码 (仅适用于您填写了None列的主机,没有填写None列的主机依然读取配置中的密码): ")
            if SetRootPassword:
                print  "已指定su - root密码"
                for host in servers_info:
                    if  servers_info[host]["password"] is None:
                        servers_info[host]["password"]=SetRootPassword
            else:
                print "您尚未指定su - root的密码,程序退出"
                sys.exit()
    # 返回机器群组和机器信息
    return HostsGroup,servers_info
def LocalScriptUpload(host_info,s_file,d_file):
    ip=host_info["ip"]
    username=host_info["username"]
    port=host_info["port"]
    password=host_info["password"]
    try:        
        t = paramiko.Transport((ip,port))
        if UseKey=='Y':
            KeyPath=os.path.expanduser('~/.ssh/id_rsa')
            key=paramiko.RSAKey.from_private_key_file(KeyPath)
            t.connect(username = username,pkey=key)
        else:
            t.connect(username = username,password = password)
        sftp = paramiko.SFTPClient.from_transport(t)
        sftp.put(s_file,d_file)
    except Exception,e:     
        print "LocalScript inited Failed",e
        return False    
    else:
        t.close()
def SSH_cmd_silent(host_info,cmd,ssh_key=""):
    ip=host_info["ip"]
    username=host_info["username"]
    port=host_info["port"]
    password=host_info["password"]
    global output_all
    PROFILE=". /etc/profile 2>/dev/null;. ~/.bash_profile 2>/dev/null;. /etc/bashrc 2>/dev/null;. ~/.bashrc 2>/dev/null;"
    PATH="export PATH=$PATH:/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin;"
    global PWD
    start_time=time.time()
    ResultSum=''
    ResultSumLog=''
    PWD=re.sub("/{2,}","/",PWD)
    try:
        err=None
        ssh=paramiko.SSHClient()
        if ssh_key:
            ssh_mode = "key"
            KeyPath=os.path.expanduser(ssh_key)
            key=paramiko.RSAKey.from_private_key_file(KeyPath)
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip,port,username,pkey=key)  
        else:
            ssh_mode = "password"
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip,port,username,password)
        stdin,stdout,stderr=ssh.exec_command(PWD+cmd)
        out=stdout.readlines()
        for o in out:
            ResultSum +=o
            ResultSumLog +=o.strip('\n') + '\\n'
        error_out=stderr.readlines()
        for err in error_out:
            ResultSum +=err
            ResultSumLog +=err.strip('\n') + '\\n'
        if err:
            exe_stat = "ERR"
            output_all["failip_list"].append(ip)
            output_all["return_msg"][ip]=""
            err_info = ResultSum
        else:
            exe_stat = "OK"
            err_info = ""
            output_all["return_msg"][ip]=ResultSum
    except Exception,e:
        output_all["failip_list"].append(ip)
        output_all["return_msg"][ip]= ""
        err_info = traceback.format_exc()
        exe_stat = "ERR"
        #traceback.print_exc()
    else:
        ssh.close()
    finally:
        operation = "ssh:%s" % cmd
        exe_time = "%0.2f Sec"%float(time.time()-start_time)
        logger.debug("op:[%s] ip:[%s] user:[%s] port:[%s] sshkey:[%s] stat:[%s] exe_time:[%s] ssh_mode:[%s] return_msg:[%s] err_info:[%s]" %(operation,ip,username,port,ssh_key,exe_stat,exe_time,ssh_mode,output_all["return_msg"][ip],err_info))

def SSH_cmd(host_info,cmd,UseLocalScript,OPTime,show_output=True):
    ip=host_info["ip"]
    username=host_info["username"]
    port=host_info["port"]
    password=host_info["password"]
    PROFILE=". /etc/profile 2>/dev/null;. ~/.bash_profile 2>/dev/null;. /etc/bashrc 2>/dev/null;. ~/.bashrc 2>/dev/null;"
    PATH="export PATH=$PATH:/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin;"
    global All_Servers_num,All_Servers_num_all,All_Servers_num_Succ,Done_Status,Global_start_time,PWD,FailIP
    start_time=time.time()
    ResultSum=''
    ResultSumLog=''
    PWD=re.sub("/{2,}","/",PWD)
    try:
        o=None
        err=None
        ssh=paramiko.SSHClient()
        if UseKey=='Y':
            KeyPath=os.path.expanduser('~/.ssh/id_rsa')
            key=paramiko.RSAKey.from_private_key_file(KeyPath)
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip,port,username,pkey=key)  
        else:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip,port,username,password)
        stdin,stdout,stderr=ssh.exec_command(PWD+cmd)
        out=stdout.readlines()
        All_Servers_num += 1
        if show_output:
            print "\r"
        for o in out:
            ResultSum +=o
            ResultSumLog +=o.strip('\n') + '\\n'
        error_out=stderr.readlines()
        for err in error_out:
            ResultSum +=err
            ResultSumLog +=err.strip('\n') + '\\n'
        if err:
            FailIP.append(ip)
            ResultSum_count="\033[1m\033[1;32m+OK [%s@%s] (%0.2f Sec, %d/%d \033[1m\033[1;31mCmd:Failed\033[1m\033[1;32m)\033[1m\033[0m" % (username,ip,float(time.time()-start_time),All_Servers_num,All_Servers_num_all)
            out='Null\n'
            mylog.log_write(ip,ResultSumLog.strip('\\n'),out,cmd,LogFile,'N',username,UseLocalScript,OPTime)
        else:
            error_out='NULL'
            ResultSum_count="\033[1m\033[1;32m+OK [%s@%s] (%0.2f Sec, %d/%d  Cmd:Sucess)\033[1m\033[0m" % (username,ip,float(time.time()-start_time),All_Servers_num,All_Servers_num_all)
            All_Servers_num_Succ+=1
            mylog.log_write(ip,error_out,ResultSumLog.strip('\\n') + '\n',cmd,LogFile,'N',username,UseLocalScript,OPTime)
        Show_Result=ResultSum + '\n' +ResultSum_count
        TmpShow=format_show.Show_Char(Show_Result+"Time:"+OPTime,0)  
        mylog.log_writesource(TmpShow)
        if show_output:
            print TmpShow
    except Exception,e:
        FailIP.append(ip)
        All_Servers_num += 1
        ResultSum_count="\n\033[1m\033[1;31m-ERR [%s@%s] %s (%0.2f Sec %d/%d)\033[1m\033[0m\a"  % (username,ip,e,float(time.time() - start_time),All_Servers_num,All_Servers_num_all)
        Show_Result= ResultSum+ResultSum_count
        TmpShow=format_show.Show_Char(Show_Result+"Time:"+OPTime,1)
        mylog.log_writesource(TmpShow)
        if show_output:
            print TmpShow
        mylog.log_write(ip,str(e),'NULL\n',cmd,LogFile,'N',username,UseLocalScript,OPTime)
    else:
        ssh.close()
    if All_Servers_num == All_Servers_num_all: #这里防止计数器永远相加下去
        FailNum=All_Servers_num_all-All_Servers_num_Succ
        if FailNum>0:
            FailNumShow="\033[1m\033[1;31mFail:%d\033[1m\033[0m" % (FailNum)
        else:
            FailNumShow="Fail:%d" % (FailNum)
        if show_output:
            print "+Done (Succ:%d,%s, %0.2fSec X_batch(V:%s) )" % (All_Servers_num_Succ,FailNumShow,time.time()-Global_start_time,VERSION)
        All_Servers_num =0
        All_Servers_num_Succ=0
        Done_Status='end'
def Upload_file(host_info,local_file,remote_dir,backup=True):
    '''
    local_file --> remote_dir
    上传文件
    '''
    ip=host_info["ip"]
    username=host_info["username"]
    port=host_info["port"]
    password=host_info["password"]
    start_time=time.time()
    global All_Servers_num
    global All_Servers_num_all
    global All_Servers_num_Succ
    global Global_start_time
    try:
        t = paramiko.Transport((ip,port))
        if UseKey=='Y':
            KeyPath=os.path.expanduser('~/.ssh/id_rsa')
            key=paramiko.RSAKey.from_private_key_file(KeyPath)
            try:
                t.connect(username = username,pkey=key)
            except EOFError:
                print "Try use RunMode=D"
            ##########################################
        else:
            try:
                t.connect(username = username,password = password)
            except EOFError:
                print "Try use RunMode=D"
        sftp = paramiko.SFTPClient.from_transport(t)
        New_d_file=re.sub('//','/',remote_dir + '/')+ os.path.split(local_file)[1]
        Bak_File=New_d_file+'.bak.'+"%d" % (int(time.strftime("%Y%m%d%H%M%S",time.localtime(Global_start_time))))
        if backup:
            try:
                sftp.rename(New_d_file,Bak_File)
                SftpInfo="Warning: %s %s  already exists,backed up to %s \n" % (ip,New_d_file,Bak_File)
            except Exception,e:
                SftpInfo='\n'
        else:
            SftpInfo='\n'
        sftp.put(local_file,New_d_file)
        All_Servers_num += 1
        All_Servers_num_Succ+=1
        print SftpInfo + "\033[1m\033[1;32m+OK [%s@%s] (%0.2f Sec %d/%d)\033[1m\033[0m" % (username,ip,time.time() - start_time,All_Servers_num,All_Servers_num_all)
    except Exception,e:
        All_Servers_num += 1
        print "\033[1m\033[1;31m-ERR [%s@%s] %s(%0.2f Sec,All %d Done %d)\033[1m\033[0m" % (username,ip,e,float(time.time() -start_time),All_Servers_num,All_Servers_num_all)   
    else:
        t.close()

    if All_Servers_num_all == All_Servers_num:
        FailNum=All_Servers_num_all-All_Servers_num_Succ
        if FailNum>0:
            FailNumShow="\033[1m\033[1;31mFail:%d\033[1m\033[0m" % (FailNum)
        else:
            FailNumShow="Fail:%d" % (FailNum)
        print "+Done (Succ:%d,%s, %0.2fSec X_batch(V:%s) )" % (All_Servers_num_Succ,FailNumShow,time.time()-Global_start_time,VERSION)
        All_Servers_num =0
        All_Servers_num_Succ=0
def Upload_file_silent(host_info,local_file,remote_dir,ssh_key="",backup=True):
    '''
    local_file --> remote_dir
    上传文件
    '''
    global output_all
    ip=host_info["ip"]
    username=host_info["username"]
    port=host_info["port"]
    password=host_info["password"]
    start_time=time.time()
    try:
        t = paramiko.Transport((ip,port))
        if ssh_key:
            ssh_mode = "key"
            KeyPath=os.path.expanduser(ssh_key)
            key=paramiko.RSAKey.from_private_key_file(KeyPath)
            t.connect(username = username,pkey=key)
            ##########################################
        else:
            ssh_mode = "password"
            t.connect(username = username,password = password)
        sftp = paramiko.SFTPClient.from_transport(t)
        New_d_file=re.sub('//','/',remote_dir + '/')+ os.path.split(local_file)[1]
        Bak_File=New_d_file+'.bak.'+"%d" % (int(time.strftime("%Y%m%d%H%M%S",time.localtime(start_time))))
        if backup:
            try:
                sftp.rename(New_d_file,Bak_File)
                SftpInfo="Warning: %s %s  already exists,backed up to %s \n" % (ip,New_d_file,Bak_File)
            except Exception,e:
                SftpInfo='\n'
        else:
            SftpInfo='\n'
        sftp.put(local_file,New_d_file)
        exe_stat = "OK"
        output_all["return_msg"][ip]="upload file ok"
        err_info = ""
    except Exception,e:
        output_all["failip_list"].append(ip)
        output_all["return_msg"][ip]=""
        err_info = traceback.format_exc()
        exe_stat = "ERR"
    else:
        t.close()
    finally:
        operation="upload:%s --> %s"%(local_file,remote_dir)
        exe_time = "%0.2f Sec"%float(time.time()-start_time)
        logger.debug("op:[%s] ip:[%s] user:[%s] port:[%s] sshkey:[%s] stat:[%s] exe_time:[%s] ssh_mode:[%s] return_msg:[%s] err_info:[%s]" %(operation,ip,username,port,ssh_key,exe_stat,exe_time,ssh_mode,output_all["return_msg"][ip],err_info))

def Download_file(host_info,remote_file,local_dir):
    ip=host_info["ip"]
    username=host_info["username"]
    port=host_info["port"]
    password=host_info["password"]
    global All_Servers_num_all
    global All_Servers_num
    global All_Servers_num_Succ
    start_time=time.time()
    try:
        t = paramiko.Transport((ip,port))
        if UseKey=='Y':
            KeyPath=os.path.expanduser('~/.ssh/id_rsa')
            key=paramiko.RSAKey.from_private_key_file(KeyPath)
            t.connect(username = username,pkey=key)
        else:
            t.connect(username = username,password = password)
        sftp = paramiko.SFTPClient.from_transport(t)
        New_d_file=re.sub('//','/',local_dir + '/')
        sftp.get(remote_file,"%s%s_%s" % (New_d_file,os.path.basename(remote_file),ip))
        All_Servers_num +=1
        All_Servers_num_Succ+=1
        print "\033[1m\033[1;32m+OK [%s@%s] (%0.2f Sec %d/%d)\033[1m\033[0m" % (username,ip,float(time.time()) - start_time,All_Servers_num,All_Servers_num_all)
    except Exception,e:
        All_Servers_num +=1
        print "\033[1m\033[1;31m-ERR [%s@%s] %s (%0.2f Sec %d/%d)\033[1m\033[0m" % (username,ip,e,float(time.time() - start_time),All_Servers_num,All_Servers_num_all)
    else:
        t.close()
    if All_Servers_num_all == All_Servers_num:
        All_Servers_num = 0
        FailNum=All_Servers_num_all-All_Servers_num_Succ
        if FailNum>0:
            FailNumShow="\033[1m\033[1;31mFail:%d\033[1m\033[0m" % (FailNum)
        else:
            FailNumShow="Fail:%d" % (FailNum)   
        print "+Done (Succ:%d,%s, %0.2fSec X_batch(V:%s))" % (All_Servers_num_Succ,FailNumShow,time.time()-Global_start_time,VERSION)
def Excute_cmd_root(host_info,cmd,UseLocalScript,OPTime):
    # 获取配置信息
    host_ip=host_info["ip"]
    username=host_info["username"]
    Port=host_info["port"]
    Password=host_info["password"]
    Passwordroot=host_info["rootpassword"]
    # 全局变量
    global All_Servers_num_all,All_Servers_num,All_Servers_num_Succ,Done_Status,bufflog,FailIP,PWD
    PWD=re.sub("/{2,}","/",PWD)
    Done_Status='start'
    bufflog=''
    start_time=time.time()
    ResultSum=''
    Result_status=False
    try:
        t=paramiko.SSHClient()
        if UseKey=='Y':
            KeyPath=os.path.expanduser('~/.ssh/id_rsa')
            key=paramiko.RSAKey.from_private_key_file(KeyPath)
            t.load_system_host_keys()
            t.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            t.connect(host_ip,Port,username,pkey=key) 
        else:
            t.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            t.connect(host_ip,Port,username,Password)
        ssh=t.invoke_shell()
        ssh.send("LANG=zh_CN.UTF-8\n")
        ssh.send("export LANG\n")
        if username=='root':
            print "IP[%s]本身是root身份，不能用root切换su-root，故直接执行"%host_ip
            All_Servers_num_Succ+=1
            Result_status=True
        else:
            ssh.send("su - root\n")
            buff=''
            while not re.search("Password:",buff) and not re.search("：", buff):
                resp=ssh.recv(9999)
                buff += resp
            ssh.send("%s\n" % (Passwordroot))
            buff1=''
            while True:
                resp=ssh.recv(500)
                buff1 += resp
                if  re.search('su:',buff1):
                    break
                else:
                    if re.search('# *$',buff1):
                        Result_status=True
                        All_Servers_num_Succ+=1
                        break
        if Result_status:
            ssh.send("%s\n" % (PWD+cmd))
            buff=""
            bufflog=''
            while not buff.endswith("# "):
                resp=ssh.recv(9999)
                buff  += resp
                bufflog  += resp.strip('\r\n') + '\\n'
            t.close()
            All_Servers_num += 1
            buff='\n'.join(buff.split('\r\n')[1:][:-1])
            ResultSum=buff + "\n\033[1m\033[1;32m+OK [%s@%s] (%0.2f Sec %d/%d)\033[1m\033[0m\n" % (username,host_ip,float(time.time() - start_time),All_Servers_num,All_Servers_num_all)
            
            bufflog_new=''
            for t in bufflog.split():
                if t==cmd:
                    continue
                bufflog_new+=t
            bufflog=bufflog_new
        else:
            All_Servers_num += 1
            FailIP.append(host_ip)
            #buff=''.join(buff.split('\r\n')[:-1])+'\n'
            buff=''
            
            ResultSum=buff + "\n\033[1m\033[1;31m-ERR Su Failed (Password Error) [%s@%s] (%0.2f Sec %d/%d)\033[1m\033[0m\n" % (username,host_ip,float(time.time() - start_time),All_Servers_num,All_Servers_num_all)
            
    except Exception,e:
        All_Servers_num += 1
        Result_status=False
        FailIP.append(host_ip)
        ResultSum="\n\033[1m\033[1;31m-ERR %s [%s@%s] (%0.2f Sec %d/%d)\033[1m\033[0m\a"   % (e,username,host_ip,float(time.time() - start_time),All_Servers_num,All_Servers_num_all)
        bufflog=str(e)
    if Result_status:
        mylog.log_write(host_ip,'NULL',bufflog.strip('\\n') + '\n',cmd,LogFile,'Y',username,UseLocalScript,OPTime)
        TmpShow=format_show.Show_Char(ResultSum+"Time:"+OPTime,0)
        mylog.log_writesource(TmpShow)
    else:
        mylog.log_write(host_ip,bufflog.strip('\\n'),'NULL\n',cmd,LogFile,'Y',username,UseLocalScript,OPTime)
        TmpShow=format_show.Show_Char(ResultSum+"Time:"+OPTime,0)
        mylog.log_writesource(TmpShow)
    print TmpShow
    if All_Servers_num_all == All_Servers_num:
        FailNum=All_Servers_num_all-All_Servers_num_Succ
        if FailNum>0:
            print All_Servers_num_Succ
            FailNumShow="\033[1m\033[1;31mFail:%d\033[1m\033[0m" % (FailNum)
        else:
            FailNumShow="Fail:%d" % (FailNum)
        print "+Done (Succ:%d,%s, %0.2fSec X_batch(V:%s) )" % (All_Servers_num_Succ,FailNumShow,time.time()-Global_start_time,VERSION)
        All_Servers_num =0
        All_Servers_num_Succ=0
        Done_Status='end'
def Excute_cmd(hostgroup_all,servers_allinfo):
    global All_Servers_num_all,All_Servers_num,All_Servers_num_Succ,Done_Status,Global_start_time,PWD,FailIP,ScriptFilePath,CONFMD5,HOSTSMD5
    global d_file,s_file

    # 读取完配置后显示的欢迎信息
    print "|-----------------------------------------------------------"
    print "|X_batch version :%s" %VERSION
    print "|"
    print "|X_batch is a batch tools for xserver"
    print "|",hostgroup_all
    print "|"
    print "|Type 'use system     ' ----- system config"
    print "|Type 'use ftp        ' ----- ftp"
    print "|Type 'run LocalScript' ----- run the LocalScript"
    print "|Type 'flush logs     ' ----- flush the logs"
    print "|Type 'exit           ' ----- exit"
    print "|-----------------------------------------------------------"
    print ""
    Done_Status='end'
    All_Servers_num    =0
    All_Servers_num_Succ=0
    UseLocalScript='N' 
    PWD='~'
    IS_PWD=False
    UseSystem=False
    UseFtp=False
    FailIP=[];LastCMD=[]
    # 操作时提示字符
    #----------------------------------------------------------------CmdPrompt_Batch:分发命令提示符
    if Useroot=="Y":
        CmdPrompt_Batch="X_batch root"
    else:
        CmdPrompt_Batch="X_batch"
    
    CmdPrompt_Config="\033[44;37mX_batch config\033[0m"
    CmdPrompt_Ftp="\033[42;37mX_batch ftp\033[0m"
    CmdPrompt=CmdPrompt_Batch
    servers_select_ip = []
    servers_select = {}
    #----------------------------------------------------------------CmdPrompt_Config:配置模式提示符

    while True:

        # 提示符prompt_group
        # 显示是哪个组
        #----------------------------------------------------------------prompt_group
        # print "servers_select_ip",servers_select_ip
        if not len(servers_select_ip):
            for server_ip in servers_allinfo:
                servers_select[server_ip] = servers_allinfo[server_ip]
        else:
            servers_select.clear()
            for server_ip in servers_select_ip:
                servers_select[server_ip] = servers_allinfo[server_ip]
        # print "servers_select",servers_select
        All_Servers_num_all=len(servers_select)

        prompt_group='IP'
        if not cmp(servers_select,servers_allinfo):
            prompt_group='All'
        else:
            for Group in hostgroup_all:
                if not cmp(sorted(servers_select.keys()),sorted(hostgroup_all[Group])):
                    prompt_group=Group
        #----------------------------------------------------------------prompt_group_end

        OPTime=time.strftime('%Y%m%d%H%M%S',time.localtime())
        Askreboot="no"
        for t in threading.enumerate():
            if t is threading.currentThread():
                continue
            else:
                t.join()
        #Threading Done
        try:
            if IS_PWD:
                ShowPWD=re.sub(";$","",PWD.split()[1])
                ShowPWD=re.sub("/{2,}","/",ShowPWD)
                ShowPWD=re.sub("cd *","",ShowPWD)
            else:
                ShowPWD=re.sub(";$|cd *","",PWD)
        except Exception,e:
            ShowPWD=PWD
        # 咱们要读取的命令
        # 提示符
        cmd=raw_input("%s [%s] %s>>>> " % (CmdPrompt,prompt_group,ShowPWD  ))
        if re.search("^ *[Yy]([Ee][Ss])? *$",Askreboot):
            sys.exit()
        # 进行命令转换，尤其是交互式命令
        cmd=re.sub('^ *ll *','ls -l ',cmd)
        cmd=re.sub("^ *top","top  -b -d 1 -n 1 ",cmd)
        cmd=re.sub("^ *ping","ping  -c 4 ",cmd)
        if re.search("^ *vim? +",cmd):
            print "X_batch 不能编辑文件"
            continue
        try:
            if not IS_PWD:
                if re.search("^ *cd.*",cmd):
                    try:
                        cmd.split()[1]
                    except IndexError:
                        PWD="cd ~;"
                        continue
                    PWD=re.search("^ *cd.*",cmd).group() +";"
                    IS_PWD=True
                    if not os.path.isfile("%s/flag/.NoAsk"%HOME):
                        AskNotice=raw_input("\033[1;33m注意: 请您确保切换的路径[%s]在远程服务器上是存在的，否则切换路径没有任何意义,您清楚了吗？\033[0m(yes/no) " % (re.sub("^ *cd *|;","",PWD)))
                        if re.search("[Yy]([Ee][Ss])?",AskNotice):
                            AskCancel=raw_input("是否取消以上提示？(yes/no) ")
                            if re.search("[Yy]([Ee][Ss])?",AskCancel):
                                try:
                                    os.mknod("%s/flag/.NoAsk"%HOME)
                                    os.system("chmod 777 %s/flag/.NoAsk"%HOME)
                                    print "已取消提醒"
                                except Exception,e:
                                    print "抱歉，不能取消提示(%s)" %e
                        else:
                            print "如果您对以上提示不清楚,那么那您可以在远程服务器上手动%s 那一定会报错的，所以请确保[%s]有效!" % (re.sub(";","",PWD),re.sub("^ *cd *|;","",PWD))
                            sys.exit()
                    continue
                else:
                    if PWD=="~":
                        PWD="cd %s;" % PWD
            else:
                try:
                    if re.search("^ *cd.*",cmd):
                        try:
                            cmd.split()[1]
                        except IndexError:
                            PWD="cd ~;"
                            continue
                        if re.search("^[a-zA-Z].*",cmd.split()[1]):
                            PWD=PWD.strip(";")+"/" +re.search("^[a-zA-Z].*",cmd.split()[1]).group()+";"
                        else:
                            PWD=cmd +";"
                        IS_PWD=True
                        continue
                except Exception,e:
                    pass
        except Exception,e:
            if IS_PWD:
                PWD=PWD
            else:
                PWD="cd %s;" % PWD
        ##############################################################################################333
        # 1 X_batch系统命令
        #   (1)run cmd      //执行在本地的文件 
        #   (2)exit         //退出
        #   (3)clear        //清屏
        #   (4)flush logs   //清屏
        #   (5)use sys      //进入配置命令
        #   (6)use ftp      //进入ftp模式
        # 2 X_batch分发命令
        #
        #################################################################################################
        # run cmd
        # 执行在本地的文件
        if re.search("^ *[Rr][Uu][Nn] +",cmd):
            try:
                #ScriptFilePath=cmd.split()[1:]
                ScriptFileCMD=cmd.split()[1:]
                IsScript=False
                for a in ScriptFileCMD:
                    if os.path.isfile(a):
                        ScriptFilePath=a
                        IsScript=True
                        break
                if not IsScript:
                    print "您指定的脚本在您的本地不存在!"
                    continue
                else:
                    ScriptFlag=str(random.randint(999999999,999999999999))
                    d_file='/tmp/' + os.path.basename(ScriptFilePath) + ScriptFlag
                    for host in servers_select:
                        d_file='/tmp/' + os.path.basename(ScriptFilePath) + ScriptFlag
                        LocalScriptUpload(servers_allinfo[host],ScriptFilePath,d_file)
                    #Newcmd="""chmod a+x %s;%s;rm -f %s""" %(d_file,d_file,d_file)
                    ScriptFileCMD=re.sub(ScriptFilePath,d_file,' '.join(ScriptFileCMD))
                    Newcmd="""chmod a+x %s;%s;rm -f %s""" %(d_file,ScriptFileCMD,d_file)
                    UseLocalScript="Y"
            except IndexError:
                print "您尚未指定本服务器上的脚本路径 用法: run /path/scriptfile"
                continue
        else:
            UseLocalScript="N"
            Newcmd=cmd
        # exit
        # 退出
        if re.search("^ *[Ee][Xx][Ii][Tt] *$",cmd):
            sys.exit(0)
        if re.search("^ *[Qq][Uu][Ii][Tt] *$",cmd):
            sys.exit(0)
        # clear
        # 清屏
        if re.search("^ *[Cc][Ll][Ee][Aa][Rr] *",cmd):
            os.system("clear")
            continue
        # flush logs
        # 日志入库
        if re.search('^ *[Ff][Ll][Uu][Ss][Hh] *[Ll][Oo][Gg][Ss] *$',cmd):
            try:
                mylog.log_flush()
                print "+OK"
                continue
            except Exception,e:
                print "Waring : %s Failed (%s)" % (cmd,e)
                continue
        # 空格无效
        if re.search("^ *$",cmd):
            continue
        # use system
        # 配置模式
        # ------------------------------------------------------------------------选择配置模式
        if re.search("^ *[Uu][Ss][Ee] +[Ss]",cmd):
            if UseFtp:
                print "必须先退出ftp模式"
                continue
            if UseSystem==True:
                print "当前已经是Use sys模式"
            else:
                UseSystem=True
                CmdPrompt="%s" % (CmdPrompt_Config)
            continue
        #######################################################################################
        #
        # 配置模式下操作
        #
        #######################################################################################
        #----------------------------------------------------------------------------------config_start
        if UseSystem:
            if re.search("^ *[Ss][Hh][Oo][Ww] *",cmd):
                print "所有主机地址 : %s" % servers_allinfo.keys()
                print "当前可接受命令的主机 : %s" %servers_select.keys()
                print """主机组:"""
                for hostgroup in hostgroup_all:
                    print "\t%s组主机: %s" % (hostgroup,hostgroup_all[hostgroup])
                if LastCMD:
                    print "执行命令%s失败的的主机   : %s" % (LastCMD,FailIP)
                continue
            # select
            elif re.search("^ *[Ss][Ee][Ll][Ee][Cc][Tt] *",cmd):
                # FailIP
                try:
                    SelectFailIP=cmd.split()[1]
                    T=re.search("[Ff][Aa][Ii][Ll] *",SelectFailIP)
                    if T:
                        if not FailIP:
                            print "当前没有执行命令失败的主机,无法选定"
                        else:
                            servers_select_ip=FailIP
                            print "已选定执行命令[%s]失败的主机%s" %(LastCMD,FailIP)
                        continue
                except IndexError:
                    print  "您尚未选定主机 select 主机地址"
                    continue
                SelectServer=re.sub("^ *[Ss][Ee][Ll][Ee][Cc][Tt] *| *","",cmd).lower()
                # select all server
                if re.search("^ *[Aa][Ll]{2} *",SelectServer):
                    servers_select=servers_allinfo
                    print "已选定所有主机: %s" % (servers_select)
                    continue
                # select group
                IsSelectHostsGroup=False
                Host_I_Flag=True
                Any_In_HostsGroup=False
                for select_item in SelectServer.split(","):
                    if select_item in hostgroup_all.keys():
                        if Host_I_Flag:
                            servers_select_ip = hostgroup_all[select_item]
                            Host_I_Flag=False
                        else:
                            servers_select_ip = hostgroup_all[select_item]+servers_select_ip
                        IsSelectHostsGroup=True
                        Any_In_HostsGroup=True
                    elif Any_In_HostsGroup:
                        print "您选定的当前主机组: [%s] 不在hosts配置文件中，请重新选定" % select_item
                        continue
                if IsSelectHostsGroup:
                    print "您已经选定主机组 : %s" %servers_select
                    IsSelectHostsGroup=False
                    continue
                SelectFail=False
                for a in SelectServer.split(","):
                    if not a in servers_allinfo:
                        print "您选定的服务器%s不在配置文件中，所以选定失败,请重新选定" % a
                        SelectFail=True
                        break
                if SelectFail:
                    SelectFail=False
                    continue
                servers_select_ip=[]
                for a in SelectServer.split(','):
                    servers_select_ip.append(a)
                print "您选定的远程服务器是：",servers_select_ip
                continue
            elif re.search("^ *[Nn][Oo] +[Ss] *",cmd):
                UseSystem=False
                CmdPrompt=CmdPrompt_Batch
                print "已退出配置模式"
                continue
            elif re.search("^ *[Nn][Oo] +[Ss][Ee][Ll][Ee][Cc][Tt] *$",cmd):
                servers_select=servers_allinfo
                print "取消选定主机"
                continue
            elif re.search("^ *[Nn][Oo] +[Aa][Ll]{2} *$",cmd):
                servers_select=servers_allinfo
                #UseSystem=False
                print "已取消所有设置"
                continue
            elif re.search("^ *\? *$",cmd) or re.search("^ *[Hh]([Ee][Ll][Pp])? *$",cmd):
                print """内部命令：
    use\tsystem\t\t//进入X_batch内部系统命令
    no\tsystem\t\t//退出配置模式
    no\tselect\t\t//取消选定的主机,回复配置文件中指定的主机
    no\tall\t\t//取消在配置模式中的所有设置
    select\thostname\t//选定一个或者多个主机，多个主机用逗号 "," 分开前提是这些主机必须在配置文件中已经配置好了
    select\tfail\t\t//选定失败的主机
    select\tall\t\t//选定所有主机
    select\tHostsGroupName\t//选定主机组
    show\t\t\t//显示主机分布情况"""
                continue
            else:
                print
                "抱歉，X_batch暂时不支持您输入的内部命令,如果要执行Linux命令，请使用no system退出"
                continue
        else:
            IsBack=False
            if re.search("^ *[Ss][Hh][Oo][Ww] *",cmd):
                IsBack=True
            elif re.search("^ *[Ss][Ee][Ll][Ee][Cc][Tt] *",cmd):
                IsBack=True
            elif re.search("^ *[Nn][Oo] +[Aa]([Ll]{2})? *$",cmd):
                IsBack=True
            elif re.search("^ *[Nn][Oo] +[Ss][Ee][Ss] *$",cmd):
                IsBack=True
            elif re.search("^ *[Nn][Oo] +[Ss][Ee][Ll][Ee][Cc][Tt] *$",cmd):
                IsBack=True
            if IsBack:
                print "该命令是内部命令，请使用use sys进入配置模式执行"
                IsBack=False
                continue
        #----------------------------------------------------------------------------------config_end

        if len(servers_select)==0:
            print "\033[1;33m当前没有设定服务器地址,或者选定的主机组中的服务器列表为空\033[0m"
            continue
        Global_start_time=time.time()
        FailIP=[]
        LastCMD=cmd
        ScriptFlag=str(random.randint(999999999,999999999999))
        Done_Status='start'
        #-------------------------------------------------------------------------------------------add_
        # ftp模式
        # ------------------------------------------------------------------------选择ftp模式
        if re.search("^ *[Uu][Ss][Ee] +[Ff]",cmd):
            if UseFtp==True:
                print "当前已经是Use ftp模式"
            else:
                UseFtp=True
                CmdPrompt="%s" % (CmdPrompt_Ftp)
            continue
        #######################################################################################
        #
        # ftp模式下操作
        #
        #######################################################################################
        #----------------------------------------------------------------------------------config_start
        if UseFtp:
            if re.search("^ *[Pp][Uu][Tt] +",cmd):
                local_file=cmd.split()[1]
                if os.path.exists(local_file):
                    print 'OK,the %s file exists.'%local_file
                else:
                    print 'Sorry,I cannot find the %s file.'%local_file
                    continue
                # remote_dir is a dir
                remote_dir = ShowPWD
                if remote_dir == "~":
                    remote_dir = "/root"
                Global_start_time=time.time()
                for host in servers_select:
                    if RunMode.upper()=='M':
                        a=threading.Thread(target=Upload_file,args=(servers_allinfo[host],local_file,remote_dir))
                        a.start()
                    else: 
                        Upload_file(servers_allinfo[host],local_file,remote_dir)
                continue
            elif re.search("^ *[Gg][Ee][Tt] +",cmd):
                remote_file=cmd.split()[1]
                local_dir = os.getcwd()
                if not os.path.isdir(local_dir):
                    print 'Recv location must be a directory'
                    sys.exit(1)
                Global_start_time=time.time()
                for host in servers_select:
                    a=threading.Thread(target=Download_file,args=(servers_allinfo[host],remote_file,local_dir))
                    a.start()
                continue
            elif re.search("^ *\? *$",cmd) or re.search("^ *[Hh]([Ee][Ll][Pp])? *$",cmd):
                print """ftp命令：
    put\tfile\t\t//upload a file from  local machine to the remote machine
    get\tfile\t\t//download a file from remote machine to the local machine
    no\tftp\t\t//退出配置模式
    
    pwd\t\t\tprint your remote working directory
    ------------------------------------------------
    wls\t\t\tlist contents of a local directory
    wpwd\t\tprint your local working directory
    wcd\t\tchange and/or print local working directory
    """
                continue
            elif re.search("^ *[Ll][Ss]",cmd):
                print 
            elif re.search("^ *[Pp][Ww][Dd]",cmd):
                print  ShowPWD
                continue
            elif re.search("^ *[Ww][Ll][Ss]",cmd):
                # wls
                cmd = 'ls'
                p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                if p.wait() == 0:
                    val = p.stdout.read()
                    print val
                else:
                    print "lls error"
                continue
            elif re.search("^ *[Ww][Pp][Ww][Dd]",cmd):
                # wls
                cmd = 'pwd'
                p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                if p.wait() == 0:
                    val = p.stdout.read()
                    print
                    print val
                else:
                    print "pwd error"
                continue
            elif re.search("^ *[Ww][Cc][Dd]",cmd):
                # wcd
                new_dir=cmd.split()[1]
                if not os.path.isdir(new_dir):
                    print 'must be a directory'
                    continue
                os.chdir(new_dir)
                continue
            elif re.search("^ *[Nn][Oo] +[Ff] *",cmd):
                UseFtp=False
                CmdPrompt=CmdPrompt_Batch
                print "已退出ftp模式"
                continue
            else:
                print
                "抱歉，X_batch暂时不支持您输入的ftp命令,如果要执行Linux命令，请使用no ftp退出"
                continue
        else:
            IsBack=False
            if re.search("^ *[Pp][Uu][Tt] *",cmd):
                IsBack=True
            elif re.search("^ *[Gg][Ee][Tt] *",cmd):
                IsBack=True
            elif re.search("^ *[Nn][Oo] +[Ff][Tt][Pp] *$",cmd):
                IsBack=True
            if IsBack:
                print "该命令是ftp命令，请使用use ftp进入配置模式执行"
                IsBack=False
                continue
        #----------------------------------------------------------------------------------------------
        # 执行的程序
        for host in servers_select:
            # 是否是多线程
            if RunMode.upper()=='M':
                # 否使用su root切换账户
                if Useroot=='Y':
                    a=threading.Thread(target=Excute_cmd_root,args=(servers_allinfo[host],Newcmd,UseLocalScript,OPTime))
                else:
                    a=threading.Thread(target=SSH_cmd,args=(servers_select[host],Newcmd,UseLocalScript,OPTime))
                a.start()
                    
            else:
                if Useroot=='Y':
                    Excute_cmd_root(servers_allinfo[host],Newcmd,UseLocalScript,OPTime)
                else:
                    SSH_cmd(servers_select[host],Newcmd,UseLocalScript,OPTime)
#(1)cmd
#(2)upload
#(3)download
#

class Xbatch():
    '''
    Xbatch is a tool for managing many machines
    '''
    def __init__(self):
        init_install.init_install(DIR_CONF,DIR_LOG,HOME)
        hostgroup_all,servers_allinfo=Read_config()
        #print hostgroup_all
        #print servers_allinfo
        self.hostgroup_all = hostgroup_all
        self.servers_allinfo = servers_allinfo
        
        #-------------------------------------------------------------------output
        global All_Servers_num,All_Servers_num_Succ,Servers_num_all,Global_start_time
        All_Servers_num_all=len(servers_allinfo)
        All_Servers_num  =0
        All_Servers_num_Succ=0
        Global_start_time=time.time()

    def put(self,local_file,remote_dir):
        '''
        eg:xb put local_file remote_dir
        '''
        servers_allinfo = self.servers_allinfo
        for host in servers_allinfo:
            Upload_file(servers_allinfo[host],local_file,remote_dir)
    def get(self,remote_file,local_dir):
        '''
        eg:xb get remote_file local_dir
        '''
        if not os.path.isdir(local_dir):
            print 'Recv location must be a directory'
            sys.exit(1)
        for host in self.servers_allinfo:
            a=threading.Thread(target=Download_file,args=(self.servers_allinfo[host],remote_file,local_dir))
            a.start()
    def cmd(self):
        '''
        eg:xb cmd
        '''
        if not self.servers_allinfo:
            print "当前没有配置服务器地址,请在%s/hosts文件中配置!" %DIR_CONF
            sys.exit()
        # 添加操作时路径 tab 键自动补全
        import command_tab
        Excute_cmd(self.hostgroup_all,self.servers_allinfo)
    def arch_ssh(self,hosts,commands):
        '''
        eg:xb arch_ssh hosts "date"
        '''
        global output_all
        output_all = {}
        # 根据总结果输出
        output_all["stat"]="OK"
        output_all["msg"]=""
        output_all["fail_num"]=0
        output_all["version"]=VERSION
        # 根据单次执行结果获取
        output_all["failip_list"]=[]
        output_all["return_msg"]={}
        
        servers_info = {}

        # 判断输入的 hostgroup 中是否是 IP
        result = re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", hosts)
        if result:
            # result 是个数组
            for ip in result:
                if ip in self.servers_allinfo.keys():
                    servers_info[ip]=self.servers_allinfo[ip]
        else:
            # hostgroup
            if hosts == "all":
                servers_info = self.servers_allinfo
            else:
                if hosts in self.hostgroup_all.keys():
                    for ip in self.hostgroup_all[hosts]:
                        servers_info[ip]=self.servers_allinfo[ip]

        # 检查要获取的机器列表是否为空
        if not servers_info:
            output_all["stat"]="ERR"
            output_all["msg"]="exe failed [%s]" % str(output_all["failip_list"])
            print output_all
            return

        global PWD
        #UseKey,ssh_key
        PWD='cd ~;'
        #----------------------------------------------------------------------------------------------
        # 执行的程序
        logger.debug("====================================================")
        logger.debug("Request: ip_list:%s commands:%s"%(str(servers_info.keys()),commands))
        for host in servers_info:
            # 执行程序
            if UseKey == "Y":
                SSH_cmd_silent(self.servers_allinfo[host],commands,ssh_key)
            else:
                SSH_cmd_silent(self.servers_allinfo[host],commands)
        output_all["fail_num"]=len(output_all["failip_list"])
        if len(output_all["failip_list"]):
            output_all["stat"]="ERR"
            output_all["msg"]="exe failed [%s]" % str(output_all["failip_list"])
        print json.dumps(output_all,indent=4)
        logger.debug("Result ip_list:%s commands:%s output_all:[%s]"%(str(servers_info.keys()),commands,output_all))
        logger.debug("=====================================================")
    def arch_put(self,hosts,local_file,remote_dir):
        '''
        eg:xb arch_put hosts local_file remote_dir
        '''
        logger.debug("#####################################################")
        logger.debug("Request: arch_put hosts:[%s] [%s]-->[%s]"%(hosts,local_file,remote_dir))
        global output_all
        output_all = {}
        # 根据总结果输出
        output_all["stat"]="OK"
        output_all["msg"]=""
        output_all["fail_num"]=0
        output_all["version"]=VERSION
        # 根据单次执行结果获取
        output_all["failip_list"]=[]
        output_all["return_msg"]={}
        
        servers_info = {}

        # 判断输入的 hostgroup 中是否是 IP
        result = re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", hosts)
        if result:
            # result 是个数组
            for ip in result:
                if ip in self.servers_allinfo.keys():
                    servers_info[ip]=self.servers_allinfo[ip]
        else:
            # hostgroup
            if hosts == "all":
                servers_info = self.servers_allinfo
            else:
                if hosts in self.hostgroup_all.keys():
                    for ip in self.hostgroup_all[hosts]:
                        servers_info[ip]=self.servers_allinfo[ip]

        # 检查要获取的机器列表是否为空
        if not servers_info:
            output_all["stat"]="ERR"
            output_all["msg"]="not found the hostgroup or IP [%s]" % hosts
            print output_all
            return

        for host in servers_info:
            if UseKey == "Y":
                Upload_file_silent(servers_info[host],local_file,remote_dir,ssh_key=ssh_key)
            else:
                Upload_file_silent(servers_info[host],local_file,remote_dir)

        output_all["fail_num"]=len(output_all["failip_list"])
        if len(output_all["failip_list"]):
            output_all["stat"]="ERR"
            output_all["msg"]="exe failed [%s]" % str(output_all["failip_list"])
        print json.dumps(output_all,indent=4)
        logger.debug("Result: ip_list:%s op:%s output_all:[%s]"%(str(servers_info.keys()),"upload",output_all))
        logger.debug("#####################################################")
    def sync(self,local_file):
        '''
        eg:xb sync file
        '''
        servers_allinfo = self.servers_allinfo
        print(servers_allinfo.keys())
        #print(self.hostgroup_all)
        remote_dir=os.path.dirname(local_file)
        for host in servers_allinfo:
            if host == '127.0.0.1':
                continue
            Upload_file(servers_allinfo[host],local_file,remote_dir)
    def hosts(self,operation,group_name="",ip_list="",user="",port=""):
        """
        eg:xb hosts set group_name "127.0.0.1 127.0.0.2" root 22
        eg:xb hosts get
        """
        logger.debug("-----------------------------------------------------")
        logger.debug("Request: op:[%s] group_name:[%s] ip_list:[%s] user:[%s] port:[%s]"%(operation,group_name,ip_list,user,port))
        output_config = {}
        # 根据总结果输出
        output_config["stat"]="OK"
        output_config["msg"]=""
        output_config["return_msg"]={}
        output_config["version"]=VERSION

        # 获取主机配置信息
        if operation == "get":
            hostgroup_all=self.hostgroup_all
            output_config["stat"]="OK"
            output_config["msg"]=""
            output_config["return_msg"]=hostgroup_all
            print output_config

        # 生成主机配置信息
        elif operation == "set":
            hostgroup_all=self.hostgroup_all
            # 判断参数是否有值
            if not group_name or not ip_list or not user  or not port:
                output_config["stat"]="ERR"
                output_config["msg"]="args error"
                print output_config
                return 
            # 判断主机组是否存在已有的列表中，如果存在，则添加至已有的的列表中，如果没有，则新增主机组
            if group_name in hostgroup_all.keys():
                # 判断新增的 IP 是否在主机组里有
                ip_all = re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", ip_list)
                ip_add_list = []
                for ip in ip_all:
                    if ip not in hostgroup_all[group_name]:
                        ip_add_list.append(ip)
                # 判断第一行是否有主机组
                lines = []
                with open(HostsFile) as f:
                    for line in f:
                        if re.search("^#",line) or re.search("^ *$",line):
                            lines.append(line)
                            continue
                        if re.search("^ *\[.*\] *$",line):
                            lines.append(line)
                            CurGroup=re.sub("^ *\[|\] *$","",line).strip().lower()
                            if CurGroup == group_name:
                                for ip in ip_add_list:
                                    lines.append("%s===%s===%s===None===None\n"%(ip,port,user))
                            else:
                                continue
                        else:
                            lines.append(line)
                with open(HostsFile,'w') as f:
                    f.write(''.join(lines))
            else:
                # 判断新增的 IP 是否在主机组里有
                ip_all = re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", ip_list)
                # 判断第一行是否有主机组
                lines = []
                with open(HostsFile) as f:
                    for line in f:
                        lines.append(line)
                    lines.append("[%s]\n"%group_name)
                    for ip in ip_all:
                        lines.append("%s===%s===%s===None===None\n"%(ip,port,user))
                with open(HostsFile,'w') as f:
                    f.write(''.join(lines))
            output_config["stat"]="OK"
            output_config["msg"]=""
            print output_config
        elif operation == "init":
            with open(HostsFile,'w') as f:
                f.write('')
            output_config["stat"]="OK"
            output_config["msg"]=""
            print output_config
        else:
            output_config["stat"]="ERR"
            output_config["msg"]="args error"
            print output_config
        logger.debug("Result:"+json.dumps(output_config))
        logger.debug("-----------------------------------------------------")

if  __name__=='__main__':
    xbatch = Xbatch()
    parser=argparse.ArgumentParser(usage='\033[43;37mpython %(prog)s function param [options]\033[0m')
    options, unknown_args = parser.parse_known_args()
    options = vars(options)
    # print(options)
    # print(unknown_args)
    if not unknown_args:
        #print parser.print_usage()
        print(parser.print_help())
        print(render_doc(Xbatch))
        exit()
    func = unknown_args.pop(0)
    
    try:
        cmd = getattr(xbatch, func)
    except:
        print('No such function: %s' % func)
        print(render_doc(Xbatch))
        exit()

    try:
        kwargs = {}
        func_args = []
        for arg in unknown_args:
            if '=' in arg:
                key, value = arg.split('=', 1)
                kwargs[key] = value
            else:
                func_args.append(arg)
        func_args = tuple(func_args)
        function_result = cmd(*func_args, **kwargs)
    except Exception,e:
        print traceback.format_exc()
        exit()
