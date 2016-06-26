#!/usr/bin/python
#coding:utf8
#Author=Bill
# 变量说明(4类变量)
# (1)主机群组hostgroup_all
# (2)主机 servers_allinfo
# (3)运行模式xbatch
# (3)全局变量output_info
VERSION=145
import os
import sys
import mylog
import format_show
import log_collect
import command_tab
import init_install
#{{{config
HOME='/opt/X_operations/X_batch'
DIR_LOG='/var/log/xbatch'
DIR_CONF='/etc/xbatch'
try:
    import paramiko,hashlib,threading,socket,ConfigParser,time,re,getpass,random,getpass,readline
except Exception,e:
    print "\033[1m\033[1;31m-ERR %s\033[0m\a"   % (e)
    sys.exit(1)
reload(sys)
sys.setdefaultencoding('utf8')
#------------------------------------log
LogFile='%s/xbatch.log' %DIR_LOG
SLogFile='%s/xbatch.source.log' %DIR_LOG
DeploymentFlag="/tmp/DeploymentFlag%s" % (str(random.randint(999999999,999999999999)))
#------------------------------------config
HostsFile="%s/hosts" %DIR_CONF
ConfFile="%s/xbatch.conf" %DIR_CONF
try:
    paramiko.util.log_to_file('%s/paramiko.log' %DIR_LOG)
except Exception,e:
    pass
#}}}
#{{{Read_config
def Read_config(file="%s"%ConfFile):
    global CONFMD5,Useroot,RunMode,Timeout,UseKey,sudo,Deployment,ListenFile,ListenTime,ListenChar
    global HOSTSMD5
    HostsGroup={}
    
    # (1)查看是否有配置文件
    try:
        HOSTSMD5=hashlib.md5(open(HostsFile).read()).hexdigest()
        CONFMD5=hashlib.md5(open(ConfFile).read()).hexdigest()
    except Exception,e:
        print "读取配置文件错误(%s)" % e
        sys.exit(1)
    
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
    try:
        Useroot=config_file.get("X_batch","Useroot").upper()
        if Useroot=='Y' and Deployment=='Y':
            print "In Deployment no support su  - root "
            sys.exit(1)
    except Exception,e:
        Useroot="N"

    #---------------------------------------------------------------config RunMode
    try:
        RunMode=config_file.get("X_batch","RunMode").upper()
    except Exception,e:
        RunMode='M'
        print "No Runmode default Mutiple(M)"

    #---------------------------------------------------------------config Timeout
    try:
        Timeout=config_file.get("X_batch","Timeout")
        try:
            Timeout=socket.setdefaulttimeout(int(Timeout))
        except Exception,e:
            Timeout=socket.setdefaulttimeout(3)
    except Exception,e:
        Timeout=socket.setdefaulttimeout(3)
    
    #---------------------------------------------------------------config sudo
    try:
        sudo=config_file.get("X_batch","sudo")
    except:
        sudo=False
    if Useroot=='Y'  and sudo:
        print "您已经su-root了，不能再配置sudo，可以sudo=N后，使用su-root"
        sys.exit(1)

    #---------------------------------------------------------------config UseKey
    try:
        UseKey=config_file.get("X_batch","UseKey").upper()
    except:
        UseKey="N"

    #---------------------------------------------------------------config Deployment
    try:
        Deployment=config_file.get("X_batch","Deployment").upper()
        if Deployment=='Y':
            try:
                ListenFile=config_file.get("X_batch","ListenFile")
            except Exception,e:
                print "In deployment mode ,must be specify ListenFile"
                sys.exit(1)
            try:
                ListenTime=int(config_file.get("X_batch","ListenTime"))
            except Exception,e:
                print  "Warning : ListenTime default is 60"
                ListenTime=60
            try:
                ListenChar=config_file.get("X_batch","ListenChar")
            except Exception,e:
                print "In deployment mode ,must be specify ListenChar"
                sys.exit(1)
    except Exception,e:
        Deployment='N'
    if RunMode=='M' and Deployment=='Y':
        print "In Mutiple-threading mode,do not support deployment mode!"
        sys.exit(1)
            
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
主机地址===端口号===登陆账户===登陆密码===su-root密码，如果没有配置使用su-root，此列可为None""" % b.strip()
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
    os.system("""echo %s >%s/version/version 2>/dev/null"""%(VERSION,HOME))
    if NoPassword and UseKey=="N":
        SetPassword=getpass.getpass("请在此处为在密码列填写了[None]的主机指定密码,如果没有填写None的主机，密码依然读取配置文件中的信息(请确保您输入的密码适用于所有密码列填写了None的主机，否则请在配置文件%s/hosts文件中逐个指定)\n\033[1;33mHosts Password:\033[0m  "%DIR_CONF)
        if SetPassword:
            print "已为所有主机指定密码"
        else:
            print "您尚未指定密码，程序退出"
            sys.exit()
        for host in servers_allinfo:
            if servers_allinfo[host]["password"] is None:
                servers_allinfo[host]["password"]=SetPassword
        NoPassword=False
    if Useroot=="Y":
        if NoRootPassword:
            SetRootPassword=getpass.getpass("请指定su-root的密码 (仅适用于您填写了None列的主机,没有填写None列的主机依然读取配置中的密码): ")
            if SetRootPassword:
                print  "已指定su - root密码"
                for host in servers_allinfo:
                    if  servers_allinfo[host]["password"] is None:
                        servers_allinfo[host]["password"]=SetRootPassword
            else:
                print "您尚未指定su - root的密码,程序退出"
                sys.exit()
    return HostsGroup,servers_info
    
#}}}
#{{{LocalScriptUpload
def LocalScriptUpload(ip,port,username,password,s_file,d_file):
    try:        
        t = paramiko.Transport((ip,port))
        if UseKey=='Y':
            KeyPath=os.path.expanduser('~/.ssh/id_rsa')
            key=paramiko.RSAKey.from_private_key_file(KeyPath)
            t.connect(username = username,pkey=key)
        else:
            t.connect(username = username,password = password)
        sftp = paramiko.SFTPClient.from_transport(t)
        ret=sftp.put(s_file,d_file)
    except Exception,e:     
        print "LocalScript inited Failed",e
        return False    
    else:
        t.close()
#}}}
#{{{_SSH_cmd_执行程序部分
def SSH_cmd(host_info,cmd,UseLocalScript,OPTime,show_output=True):
    ip=host_info["ip"]
    username=host_info["username"]
    port=host_info["port"]
    password=host_info["password"]
    global ListenLog
    PROFILE=". /etc/profile 2>/dev/null;. ~/.bash_profile 2>/dev/null;. /etc/bashrc 2>/dev/null;. ~/.bashrc 2>/dev/null;"
    PATH="export PATH=$PATH:/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin;"
    global All_Servers_num,All_Servers_num_all,All_Servers_num_Succ,Done_Status,Global_start_time,PWD,FailIP
    start_time=time.time()
    ResultSum=''
    ResultSumLog=''
    DeploymentStatus=False
    DeploymentInfo=None
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
        if Deployment=='Y':
            stdin,stdout,stderr=ssh.exec_command(PWD+ListenLog+cmd)
        else:
            stdin,stdout,stderr=ssh.exec_command(PWD+cmd)
        out=stdout.readlines()
        All_Servers_num += 1
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
            if Deployment=='Y':
                DeploymentStatus=False
            mylog.log_write(ip,ResultSumLog.strip('\\n'),out,cmd,LogFile,'N',username,UseLocalScript,Deployment,DeploymentStatus,OPTime)
        else:
            error_out='NULL'
            ResultSum_count="\033[1m\033[1;32m+OK [%s@%s] (%0.2f Sec, %d/%d  Cmd:Sucess)\033[1m\033[0m" % (username,ip,float(time.time()-start_time),All_Servers_num,All_Servers_num_all)
            All_Servers_num_Succ+=1
            if Deployment=='Y':
                print  "Wating %s deployment (for %d Sec)..." % (ip,ListenTime)
                T=log_collect.log_collect(ip,port,username,password,"""grep  -E "%s"  %s -q && echo  -n 'DoneSucc'""" % (ListenChar,DeploymentFlag),ListenTime,UseKey)
                if T:
                    DeploymentStatus=True
                else:
                    DeploymentInfo="Main commands excuted success, But deployment havn't check suncess info (%s) " %(ListenChar)
                    DeploymentStatus=False
                    

            mylog.log_write(ip,error_out,ResultSumLog.strip('\\n') + '\n',cmd,LogFile,'N',username,UseLocalScript,Deployment,DeploymentStatus,OPTime)

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
        mylog.log_write(ip,str(e),'NULL\n',cmd,LogFile,'N',username,UseLocalScript,Deployment,DeploymentStatus,OPTime)
    else:
        ssh.close()
    if Deployment=='Y' and not  DeploymentStatus:
        while True:
            TT=raw_input("%s Deployment not Success (%s) want contiue deployment next server (yes/no) ? " %(ip,DeploymentInfo))
            if TT=='yes':
                break
            elif TT=='no':
                sys.exit(1)
    if All_Servers_num == All_Servers_num_all: #这里防止计数器永远相加下去
        FailNum=All_Servers_num_all-All_Servers_num_Succ
        if FailNum>0:
            FailNumShow="\033[1m\033[1;31mFail:%d\033[1m\033[0m" % (FailNum)
        else:
            FailNumShow="Fail:%d" % (FailNum)
        print "+Done (Succ:%d,%s, %0.2fSec X_batch(V:%d) )" % (All_Servers_num_Succ,FailNumShow,time.time()-Global_start_time,VERSION)
        All_Servers_num =0
        All_Servers_num_Succ=0
        Done_Status='end'
#}}}
#{{{Upload_file
def Upload_file(host_info):
    ip=host_info["ip"]
    username=host_info["username"]
    port=host_info["port"]
    password=host_info["password"]
    start_time=time.time()
    global All_Servers_num
    global All_Servers_num_all
    global All_Servers_num_Succ
    global Global_start_time
    global s_file
    global d_file
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
        New_d_file=re.sub('//','/',d_file + '/')+ os.path.split(s_file)[1]
        Bak_File=New_d_file+'.bak.'+"%d" % (int(time.strftime("%Y%m%d%H%M%S",time.localtime(Global_start_time))))
        try:
            sftp.rename(New_d_file,Bak_File)
            SftpInfo="Warning: %s %s  already exists,backed up to %s \n" % (ip,New_d_file,Bak_File)
        except Exception,e:
            SftpInfo='\n'
        ret=sftp.put(s_file,New_d_file)
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
        
        print "+Done (Succ:%d,%s, %0.2fSec X_batch(V:%d) )" % (All_Servers_num_Succ,FailNumShow,time.time()-Global_start_time,VERSION)
        All_Servers_num =0
        All_Servers_num_Succ=0
#}}}
#{{{Download_file_regex
def Download_file_regex(host_info):
    ip=host_info["ip"]
    username=host_info["username"]
    port=host_info["port"]
    password=host_info["password"]
    global All_Servers_num_all
    global All_Servers_num
    global All_Servers_num_Succ
    global s_file
    global d_file
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
        t_get=sftp.listdir(os.path.dirname(s_file))
        for getfilename in t_get:
            if re.search(os.path.basename(s_file),getfilename):
                download_fullpath=os.path.join(os.path.dirname(s_file),getfilename)
                try:
                    ret=sftp.get(download_fullpath,"%s_%s" % (os.path.join(d_file,getfilename),ip))
                    print  '\t\033[1m\033[1;32m+OK [%s@%s] : %s' % (username,ip,download_fullpath)
                except Exception,e:
                    print  '\t\033[1m\033[1;33m-Failed %s : %s %s' % (ip,download_fullpath,e)
        All_Servers_num +=1
        All_Servers_num_Succ+=1
        print "\033[1m\033[1;32m+OK [%s@%s] (%0.2f Sec %d/%d)\033[1m\033[0m" % (username,ip,float(time.time()) - start_time,All_Servers_num,All_Servers_num_all)
    except Exception,e:
        All_Servers_num +=1
        print "\033[1m\033[1;31m-ERR [%s@%s] %s (%0.2f Sec  %d/%d)\033[1m\033[0m" % (username,ip,e,float(time.time() - start_time),All_Servers_num,All_Servers_num_all)
    else:
        t.close()
    if All_Servers_num_all == All_Servers_num:
        All_Servers_num = 0
        FailNum=All_Servers_num_all-All_Servers_num_Succ
        if FailNum>0:
            FailNumShow="\033[1m\033[1;31mFail:%d\033[1m\033[0m" % (FailNum)
        else:
            FailNumShow="Fail:%d" % (FailNum)
        print "+Done (Succ:%d,%s, %0.2fSec X_batch(V:%d))" % (All_Servers_num_Succ,FailNumShow,time.time()-Global_start_time,VERSION)
#}}}
#{{{Download_file
def Download_file(host_info):
    ip=host_info["ip"]
    username=host_info["username"]
    port=host_info["port"]
    password=host_info["password"]
    global All_Servers_num_all
    global All_Servers_num
    global All_Servers_num_Succ
    global s_file
    global d_file
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
        New_d_file=re.sub('//','/',d_file + '/')
        ret=sftp.get(s_file,"%s%s_%s" % (New_d_file,os.path.basename(s_file),ip))
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
        print "+Done (Succ:%d,%s, %0.2fSec X_batch(V:%d))" % (All_Servers_num_Succ,FailNumShow,time.time()-Global_start_time,VERSION)
#}}}
#{{{Excute_sudo
def Excute_sudo(host_info,cmd,UseLocalScript,OPTime):
    s=host_info["ip"]
    username=host_info["username"]
    Port=host_info["port"]
    Password=host_info["password"]
    global All_Servers_num_all,All_Servers_num,All_Servers_num_Succ,Done_Status,bufflog,FailIP,PWD,sudo
    PWD=re.sub("/{2,}","/",PWD)
    Done_Status='start'
    bufflog=''
    start_time=time.time()
    ResultSum=''
    Result_status=False
    sudoinfo=re.sub("^ *| *$","",sudo).split()
    if username=='root':
        print "不能用root登陆后再sudo登陆"
        sys.exit()
    elif sudoinfo[-1]=='-' or sudoinfo[-1]=='root' or  sudoinfo[-1]=='su':
        prompt='# '
    else:
        prompt='$ '
    try:
        t=paramiko.SSHClient()
        if UseKey=='Y':
            KeyPath=os.path.expanduser('~/.ssh/id_rsa')
            key=paramiko.RSAKey.from_private_key_file(KeyPath)
            t.load_system_host_keys()
            t.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            t.connect(s,Port,username,pkey=key) 
        else:
            t.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            t.connect(s,Port,username,Password)
        ssh=t.invoke_shell()
        ssh.send("LANG=zh_CN.UTF-8\n")
        ssh.send("export LANG\n")
        ssh.send("%s\n"%sudo)
        buff=''
        resp=''
        info=''
        EnterPassword=False
        while True:
            if re.search("\[sudo\] +password for.*:",resp):
                ssh.send("%s\n"%Password)
                while True:
                    resp=ssh.recv(100)
                    if re.search("Sorry, try again",resp):
                        info='密码错误'
                        break
                    elif re.search('%s +.*sudoers'%username,resp):
                        info="没有sudo权限"
                        break
                    elif resp.endswith(prompt):
                        EnterPassword=True
                        Result_status=True
                        break
            if EnterPassword:break
            if buff.endswith(prompt):
                Result_status=True
                break
            if re.search('%s +.*sudoers'%username,resp):
                info="没有sudo权限"
                break
            resp=ssh.recv(9999)
            buff += resp
        if Result_status:
            ssh.send("%s\n" % (PWD+cmd))
            buff=""
            bufflog=''
            while not buff.endswith(prompt):
                resp=ssh.recv(9999)
                buff  += resp
                bufflog  += resp.strip('\r\n') + '\\n'
            t.close()
            All_Servers_num += 1
            buff='\n'.join(buff.split('\r\n')[1:][:-1])
            ResultSum=buff + "\n\033[1m\033[1;32m+OK [%s@%s] (%0.2f Sec %d/%d)\033[1m\033[0m\n" % (username,s,float(time.time() - start_time),All_Servers_num,All_Servers_num_all)
            
            bufflog_new=''
            for t in bufflog.split():
                if t==cmd:
                    continue
                bufflog_new+=t
            bufflog=bufflog_new
            All_Servers_num_Succ+=1
        else:
            All_Servers_num += 1
            FailIP.append(s)
            #buff=''.join(buff.split('\r\n')[:-1])+'\n'
            buff=''
            
            ResultSum=buff + "\n\033[1m\033[1;31m-ERR sudo Failed (%s) [%s@%s] (%0.2f Sec %d/%d)\033[1m\033[0m\n" % (info,username,s,float(time.time() - start_time),All_Servers_num,All_Servers_num_all)
            
    except Exception,e:
        All_Servers_num += 1
        Result_status=False
        FailIP.append(s)
        ResultSum="\n\033[1m\033[1;31m-ERR %s [%s@%s] (%0.2f Sec %d/%d)\033[1m\033[0m\a"   % (e,username,s,float(time.time() - start_time),All_Servers_num,All_Servers_num_all)
        bufflog=str(e)
    if Result_status:
        mylog.log_write(s,'NULL',bufflog.strip('\\n') + '\n',cmd,LogFile,'Y',username,UseLocalScript,'N','N',OPTime)
        TmpShow=format_show.Show_Char(ResultSum+"Time:"+OPTime,0)
        mylog.log_writesource(TmpShow)
    else:
        mylog.log_write(s,bufflog.strip('\\n'),'NULL\n',cmd,LogFile,'Y',username,UseLocalScript,'N','N',OPTime)
        TmpShow=format_show.Show_Char(ResultSum+"Time:"+OPTime,0)
        mylog.log_writesource(TmpShow)
    print TmpShow
    if All_Servers_num_all == All_Servers_num:
        FailNum=All_Servers_num_all-All_Servers_num_Succ
        if FailNum>0:
            FailNumShow="\033[1m\033[1;31mFail:%d\033[1m\033[0m" % (FailNum)
        else:
            FailNumShow="Fail:%d" % (FailNum)
        print "+Done (Succ:%d,%s, %0.2fSec X_batch(V:%d))" % (All_Servers_num_Succ,FailNumShow,time.time()-Global_start_time,VERSION)
        All_Servers_num =0
        All_Servers_num_Succ=0
        Done_Status='end'
#}}}
#{{{_Excute_cmd_root
def Excute_cmd_root(host_info,cmd,UseLocalScript,OPTime):
    s=host_info["ip"]
    username=host_info["username"]
    Port=host_info["port"]
    Password=host_info["password"]
    Passwordroot=host_info["rootpassword"]
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
            t.connect(s,Port,username,pkey=key) 
        else:
            t.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            t.connect(s,Port,username,Password)
        ssh=t.invoke_shell()
        ssh.send("LANG=zh_CN.UTF-8\n")
        ssh.send("export LANG\n")
        if username=='root':
            print "不能用root切换su-root"
            sys.exit()
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
            ResultSum=buff + "\n\033[1m\033[1;32m+OK [%s@%s] (%0.2f Sec %d/%d)\033[1m\033[0m\n" % (username,s,float(time.time() - start_time),All_Servers_num,All_Servers_num_all)
            
            bufflog_new=''
            for t in bufflog.split():
                if t==cmd:
                    continue
                bufflog_new+=t
            bufflog=bufflog_new
        else:
            All_Servers_num += 1
            FailIP.append(s)
            #buff=''.join(buff.split('\r\n')[:-1])+'\n'
            buff=''
            
            ResultSum=buff + "\n\033[1m\033[1;31m-ERR Su Failed (Password Error) [%s@%s] (%0.2f Sec %d/%d)\033[1m\033[0m\n" % (username,s,float(time.time() - start_time),All_Servers_num,All_Servers_num_all)
            
    except Exception,e:
        All_Servers_num += 1
        Result_status=False
        FailIP.append(s)
        ResultSum="\n\033[1m\033[1;31m-ERR %s [%s@%s] (%0.2f Sec %d/%d)\033[1m\033[0m\a"   % (e,username,s,float(time.time() - start_time),All_Servers_num,All_Servers_num_all)
        bufflog=str(e)
    if Result_status:
        mylog.log_write(s,'NULL',bufflog.strip('\\n') + '\n',cmd,LogFile,'Y',username,UseLocalScript,'N','N',OPTime)
        TmpShow=format_show.Show_Char(ResultSum+"Time:"+OPTime,0)
        mylog.log_writesource(TmpShow)
    else:
        mylog.log_write(s,bufflog.strip('\\n'),'NULL\n',cmd,LogFile,'Y',username,UseLocalScript,'N','N',OPTime)
        TmpShow=format_show.Show_Char(ResultSum+"Time:"+OPTime,0)
        mylog.log_writesource(TmpShow)
    print TmpShow
    if All_Servers_num_all == All_Servers_num:
        FailNum=All_Servers_num_all-All_Servers_num_Succ
        if FailNum>0:
            FailNumShow="\033[1m\033[1;31mFail:%d\033[1m\033[0m" % (FailNum)
        else:
            FailNumShow="Fail:%d" % (FailNum)
        print "+Done (Succ:%d,%s, %0.2fSec X_batch(V:%d) )" % (All_Servers_num_Succ,FailNumShow,time.time()-Global_start_time,VERSION)
        All_Servers_num =0
        All_Servers_num_Succ=0
        Done_Status='end'
#}}}
#{{{Excute_cmd
def Excute_cmd(hostgroup_all,servers_allinfo):
    global All_Servers_num_all,All_Servers_num,All_Servers_num_Succ,Done_Status,ListenLog,Global_start_time,PWD,FailIP,ScriptFilePath,CONFMD5,HOSTSMD5
    global d_file,s_file
    global ListenFile

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
    #print "Servers" , Servers
    print ""
    Done_Status='end'
    All_Servers_num    =0
    All_Servers_num_Succ=0
    UseLocalScript='N' 
    PWD='~'
    IS_PWD=False
    UseSystem=False
    UseFtp=False
    #Servers_T=Servers
    servers_select=servers_allinfo
    FailIP=[];LastCMD=[]
    # 操作时提示字符
    #----------------------------------------------------------------CmdPrompt_Batch:分发命令提示符
    if Useroot=="Y":
        CmdPrompt_Batch="X_batch root"
    elif sudo:
        CmdPrompt_Batch="X_batch sudo"
    else:
        CmdPrompt_Batch="X_batch"
    
    CmdPrompt_Config="\033[44;37mX_batch config\033[0m"
    CmdPrompt_Ftp="\033[42;37mX_batch ftp\033[0m"
    CmdPrompt=CmdPrompt_Batch
    #----------------------------------------------------------------CmdPrompt_Config:配置模式提示符

    while True:
        All_Servers_num_all=len(servers_select)

        # 提示符prompt_group
        # 显示是哪个组
        #----------------------------------------------------------------prompt_group
        prompt_group='IP'
        if not cmp(servers_select,servers_allinfo):
            prompt_group='All'
        else:
            for Group in hostgroup_all:
                if not cmp(servers_select.keys(),hostgroup_all[Group]):
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
        if HOSTSMD5!=hashlib.md5(open(HostsFile).read()).hexdigest():
            Askreboot=raw_input("Hosts配置文件发生变化,重启程序[%s]才能生效 (yes/no)? " %sys.argv[0])
            HOSTSMD5=hashlib.md5(open(HostsFile).read()).hexdigest()
        elif CONFMD5!=hashlib.md5(open(ConfFile).read()).hexdigest():
            Askreboot=raw_input("conf配置文件发生变化,重启程序[%s]才能生效 (yes/no)? " %sys.argv[0])
            CONFMD5=hashlib.md5(open(ConfFile).read()).hexdigest()
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
                        if UseKey=="Y":
                            LocalScriptUpload(host,servers_select[host]["port"],servers_select[host]["username"],None,ScriptFilePath,d_file)
                        else:
                            LocalScriptUpload(s,servers_select[host]["port"],servers_select[host]["username"],ScriptFilePath,d_file)
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
                    print "\t%s组主机: %s" % (hostgroup,hostgroup_all[B])
                if LastCMD:
                    print "执行命令%s失败的的主机   : %s" % (LastCMD,FailIP)
                continue
            elif re.search("^ *[Ss][Ee][Ll][Ee][Cc][Tt] *",cmd):
                try:
                    SelectFailIP=cmd.split()[1]
                    T=re.search("[Ff][Aa][Ii][Ll] *",SelectFailIP)
                    if T:
                        if not FailIP:
                            print "当前没有执行命令失败的主机,无法选定"
                        else:
                            servers_select=FailIP
                            print "已选定执行命令[%s]失败的主机%s" %(LastCMD,FailIP)
                        continue
                except IndexError:
                    print  "您尚未选定主机 select 主机地址"
                    continue
                SelectServer=re.sub("^ *[Ss][Ee][Ll][Ee][Cc][Tt] *| *","",cmd).lower()
                if re.search("^ *[Aa][Ll]{2} *",SelectServer):
                    servers_select=servers_allinfo
                    print "已选定所有主机: %s" % (servers_select)
                    continue
                IsSelectHostsGroup=False
                Host_I_Flag=True
                Any_In_HostsGroup=False
                for c in SelectServer.split(","):
                    if c in hostgroup_all.keys():
                        if Host_I_Flag:
                            servers_select=hostgroup_all[c]
                            Host_I_Flag=False
                        else:
                            servers_select=hostgroup_all[c]+servers_select
                        IsSelectHostsGroup=True
                        Any_In_HostsGroup=True
                    elif Any_In_HostsGroup:
                        print "您选定的当前主机组: [%s] 不在hosts配置文件中，请重新选定" % c
                        continue
                if IsSelectHostsGroup:
                    print "您已经选定主机组 : %s" %servers_select
                    IsSelectHostsGroup=False
                    continue
                SelectFail=False
                for a in SelectServer.split(","):
                    if not a in Servers:
                        print "您选定的服务器%s不在配置文件中，所以选定失败,请重新选定" % a
                        SelectFail=True
                        break
                        
                if SelectFail:
                    SelectFail=False
                    continue
                servers_select=[]
                for a in SelectServer.split(','):
                    servers_select.append(a)
                print "您选定的远程服务器是：",servers_select
                continue
            elif re.search("^ *[Nn][Oo] +[Ss] *",cmd):
                UseSystem=False
                CmdPrompt=CmdPrompt_Batch
                print "已退出配置模式"
                continue
            elif re.search("^ *[Nn][Oo] +[Ss][Ee][Ll][Ee][Cc][Tt] *$",cmd):
                servers_select=Servers
                print "取消选定主机"
                continue
            elif re.search("^ *[Nn][Oo] +[Aa][Ll]{2} *$",cmd):
                servers_select=Servers
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
            if re.search("^ *[Uu][Pp][Ll][Oo][Aa][Dd] +",cmd):
                s_file=cmd.split()[1]
                if os.path.exists(s_file):
                    print 'OK,the %s file exists.'%s_file
                else:
                    print 'Sorry,I cannot find the %s file.'%s_file
                    continue
                d_file = ShowPWD
                if d_file == "~":
                    d_file = "/root"
                Global_start_time=time.time()
                for host in servers_select:
                    if RunMode.upper()=='M':
                        a=threading.Thread(target=Upload_file,args=(servers_allinfo[host],))
                        a.start()
                    else: 
                        Upload_file(servers_allinfo[host])
                continue
            elif re.search("^ *[Dd][Oo][Ww][Nn][Ll][Oo][Aa][Dd] +",cmd):
                s_file=cmd.split()[1]
                d_file = ShowPWD
                if d_file == "~":
                    d_file = "/root"
                if not os.path.isdir(d_file):
                    print 'Recv location must be a directory'
                    sys.exit(1)
                Global_start_time=time.time()
                for host in servers_select:
                    a=threading.Thread(target=Download_file_regex,args=(servers_allinfo[host]))
                    a.start()
                continue
            elif re.search("^ *\? *$",cmd) or re.search("^ *[Hh]([Ee][Ll][Pp])? *$",cmd):
                print """ftp命令：
    upload\tfile\t\t//upload a file from  local machine to the remote machine
    download\tfile\t\t//download a file from remote machine to the local machine
    no\t\tftp\t\t//退出配置模式
    """
                continue
            elif re.search("^ *[Ll][Ss]",cmd):
                print 
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
            if re.search("^ *[Uu][Pp][Ll][Oo][Aa][Dd] *",cmd):
                IsBack=True
            elif re.search("^ *[Dd][Oo][Ww][Nn][Ll][Oo][Aa][Dd] *",cmd):
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
                if Useroot=='Y':
                    a=threading.Thread(target=Excute_cmd_root,args=(servers_allinfo[host],Newcmd,UseLocalScript,OPTime))
                    a.start()
                else:
                    if sudo:
                        a=threading.Thread(target=Excute_sudo,args=(servers_allinfo[host],Newcmd,UseLocalScript,OPTime))
                    else:
                        a=threading.Thread(target=SSH_cmd,args=(servers_select[host],Newcmd,UseLocalScript,OPTime))
                    a.start()
                    
            else:
                if Useroot=='Y':
                    Excute_cmd_root(servers_allinfo[host],Newcmd,UseLocalScript,OPTime)
                else:
                    if Deployment=='Y':
                        ListenLog="""if [ ! -r %s ] ; then echo -e '\033[1m\033[1;31m-ERR ListenFile %s  not exists,so do not excute commands !\033[1m\033[0m\a ' 1>&2 ;exit;else nohup tail -n 0 -f  %s  2&>%s &   fi;""" % (ListenFile,ListenFile,ListenFile,DeploymentFlag)
                    if sudo:
                        Excute_sudo(servers_allinfo[host],Newcmd,UseLocalScript,OPTime)
                    else:
                        SSH_cmd(servers_select[host],Newcmd,UseLocalScript,OPTime)
                            
            ############################################################################################
#}}}
#{{{Excute_inspection()
def Excute_inspection(servers_allinfo,Newcmd):
    global All_Servers_num_all,All_Servers_num,All_Servers_num_Succ,Done_Status,ListenLog,Global_start_time,PWD,FailIP,ScriptFilePath,CONFMD5,HOSTSMD5
    global ListenFile
    All_Servers_num_Succ=0
    UseLocalScript='N' #
    OPTime=time.strftime('%Y%m%d%H%M%S',time.localtime())
    PWD='cd ~;'
    FailIP=[]
    All_Servers_num_all=len(servers_allinfo)
    Global_start_time=time.time()
    #----------------------------------------------------------------------------------------------
    # 执行的程序
    for host in servers_allinfo:
        # 是否是多线程
        if RunMode.upper()=='M':
            if Useroot=='Y':
                a=threading.Thread(target=Excute_cmd_root,args=(servers_allinfo[host],Newcmd,UseLocalScript,OPTime))
                a.start()
            else:
                if sudo:
                    a=threading.Thread(target=Excute_sudo,args=(servers_allinfo[host],Newcmd,UseLocalScript,OPTime))
                else:
                    #默认模式
                    a=threading.Thread(target=SSH_cmd,args=(servers_allinfo[host],Newcmd,UseLocalScript,OPTime,False))
                a.start()
                
        else:
            if Useroot=='Y':
                Excute_cmd_root(servers_allinfo[host],Newcmd,UseLocalScript,OPTime)
            else:
                if Deployment=='Y':
                    ListenLog="""if [ ! -r %s ] ; then echo -e '\033[1m\033[1;31m-ERR ListenFile %s  not exists,so do not excute commands !\033[1m\033[0m\a ' 1>&2 ;exit;else nohup tail -n 0 -f  %s  2&>%s &   fi;""" % (ListenFile,ListenFile,ListenFile,DeploymentFlag)
                if sudo:
                    Excute_sudo(servers_allinfo[host],Newcmd,UseLocalScript,OPTime)
                else:
                    SSH_cmd(servers_allinfo[host],Newcmd,UseLocalScript,OPTime,False)
                        
        ############################################################################################
#}}}
#(1)cmd
#(2)upload
#(3)download
#
#{{{main
def main():
    init_install.init_install(DIR_CONF,DIR_LOG,HOME)
    hostgroup_all,servers_allinfo=Read_config()
    global s_file,d_file,LocalScript,Global_start_time
    global All_Servers_num_Succ,All_Servers_num_all,All_Servers_num
    All_Servers_num  =0
    All_Servers_num_Succ=0
    if not servers_allinfo:
        print "当前没有配置服务器地址,请在%s/hosts文件中配置!" %DIR_CONF
        sys.exit()
    # (2)主程序
    try:
        from optparse import OptionParser
        p=OptionParser()
        p.add_option("-t","--excute-type",help="""Description: select excute type
            Parameter: [cmd|download|upload]
            cmd     : Excute Shell Command
            download: Download file
            upload  : Upload file
            
            Example: %s -t cmd""" % sys.argv[0])
        p.add_option("-c","--cmd",help="cmd")
        p.add_option("-s","--source-file",help="""Description:  Specific Source file  path
            Example:
                %s  -t upload   -s /local/file  -d /remote/dir
                %s  -t download -s /remote/file -d /local/dir""" %(sys.argv[0],sys.argv[0]))
        p.add_option("-d","--destination-file",help="""
            Description: Specific a destination directory Path""")
        p.add_option("-r","--regex",action='store_false',default=True,help="""
            Description: Use regex match filename
            Example: 
            %s  -t download -s '^/remote/tomcat/logs/localhost_2015-0[1-3].*log$' -d  /local/dir/

            Notice: This parameter applies only to download""" % sys.argv[0])
        (option,args)=p.parse_args()
        Global_start_time=time.time()
        if option.excute_type == "cmd": 
            mylog.log_flush()
            Excute_inspection(servers_allinfo,option.cmd)
            exit(1)
        elif option.excute_type == "upload":
            All_Servers_num_all=len(servers_allinfo)
            if option.source_file and option.destination_file:
                s_file=option.source_file
                d_file=option.destination_file
            else:
                print "Upload File"
                s_file=raw_input("Local Source Path>>>")
                d_file=raw_input("Remote Destination Full-Path>>>")
            for host in servers_allinfo:
                if RunMode.upper()=='M':
                    if UseKey=="Y":
                        if  float(sys.version[:3])<2.6:
                            Upload_file(servers_allinfo[host])
                        else:
                            a=threading.Thread(target=Upload_file,args=(servers_allinfo[host],))
                            a.start()
                    else:
                        if  float(sys.version[:3])<2.6:
                            Upload_file(servers_allinfo[host])
                        else:
                            a=threading.Thread(target=Upload_file,args=(servers_allinfo[host],))
                            a.start()
                else:
                    Upload_file(servers_allinfo[host])
        elif option.excute_type == "download":
            All_Servers_num_all=len(servers_allinfo)
            if option.source_file and option.destination_file:
                s_file=option.source_file
                d_file=option.destination_file
                print d_file
            else:
                print "Download File"
                s_file=raw_input("Remote Source Full-Path>>>")
                d_file=raw_input("Local Destination Path>>>")
            if not os.path.isdir(d_file):
                print 'Recv location must be a directory'
                sys.exit(1)
            for host in servers_allinfo:
                if option.regex:
                    a=threading.Thread(target=Download_file,args=(servers_allinfo[host],))
                else:
                    a=threading.Thread(target=Download_file_regex,args=(servers_allinfo[host],))
                a.start()

        # 不输入参数的话，会执行以下程序
        elif not option.excute_type:
            if not os.path.isfile("%s/flag/.NoTabAsk"%HOME):
                TabAsk=raw_input("在新版本中，已经支持TAB补全功能，但是补全的依据是根据您当前所在的这个服务器上的路径为标准的，而并不是远程服务器上的路径，所以您需要确保使用TAB补全后，路径是正确的\n是否取消提示 (yes/no) ")
                if re.search("^ *[Yy]([Ee][Ss])? *$",TabAsk):
                    try:
                        os.mknod("%s/flag/.NoTabAsk"%HOME)
                        print "已取消提醒"
                    except Exception,e:
                        print "取消提醒失败(%s)" % e
            # 执行的命令    
            Excute_cmd(hostgroup_all,servers_allinfo)
            sys.exit(0)
        else:
            print "Parameter does not currently support\t(%s)\a" % (option.excute_type)
            Excute_cmd()
    except KeyboardInterrupt:
        print "exit"
    except EOFError:
        print "exit"
#}}}
if  __name__=='__main__':
    main()
