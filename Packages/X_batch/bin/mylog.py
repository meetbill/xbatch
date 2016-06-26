#!/usr/bin/python
#coding:utf8
#Author=Bill
import os
import time
import shutil
DIR_LOG='/var/log/xbatch'
LogFile='%s/xbatch.log' %DIR_LOG
SLogFile='%s/xbatch.source.log' %DIR_LOG
#{{{log_write
def log_write(ip,stderr,stdout,Logcmd,LogFile,useroot,username,UseLocalScript,Deployment,DeploymentStatus,OPTime):
    os.system("chmod 777 %s/* 2>/dev/null" %DIR_LOG)
    if DeploymentStatus:
        DeploymentStatus_T='Y'
    else:
        DeploymentStatus_T='N'
    Deployment=Deployment.upper()
    
    try:
        T=open(LogFile,"a")
        T.write(ip+ '===' + "user:" +username  + '===' + "time:"+OPTime   + 
                '===' + "su-root:"+useroot + '===' + "userscript:" + 
                UseLocalScript + '===' + "Deployment:"+Deployment + '===' 
                +"DeploymentStatus_T"+ DeploymentStatus_T + '===' + 
                "Logcmd:"+Logcmd + '===' +"stderr:"+ stderr + '===' +"stdout:"+ stdout)
        T.close()
    except Exception,e:
        print "Warning: Can't write log. (%s)" % e
#}}}
#{{{log_writesource
def log_writesource(MSG):
    os.system("chmod 777 %s/* 2>/dev/null" %DIR_LOG)
    try:
        F=open(SLogFile,"a")
        F.write(MSG)
        F.close()
    except Exception,e:
        print "Can not write to source log (%s)" % (e)
#}}}
#{{{log_flush
def log_flush():
    #log_flush
    Log_Flag=time.strftime('%Y%m%d%H%M%S',time.localtime())
    if os.path.exists(LogFile):
        shutil.move('%s'%LogFile,'%s/xbatch%s.log'% (DIR_LOG,Log_Flag))
    #log_logrorate
#}}}
